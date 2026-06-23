from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Candidate, Election, ElectionStatus


def create_web_election(
    db_session: Session,
    status: ElectionStatus = ElectionStatus.ACTIVE,
    name: str = "Web election",
) -> Election:
    now = datetime.now(timezone.utc)
    election = Election(
        name=name,
        description="Rendered by a web route test.",
        status=status,
        merkle_root="root",
        starts_at=now - timedelta(hours=1),
        ends_at=now + timedelta(days=1),
    )
    db_session.add(election)
    db_session.commit()
    db_session.refresh(election)

    return election


def test_home_page_renders_voter_entry(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "ZKP Voting" in response.text
    assert "Voter entry" in response.text
    assert 'id="voter-package-form"' in response.text
    assert 'href="/admin"' not in response.text
    assert 'type="module" src="/static/js/app.js' in response.text


def test_voter_entry_page_renders(client: TestClient) -> None:
    response = client.get("/voter")

    assert response.status_code == 200
    assert "Load voter package" in response.text
    assert 'id="voter-package-status"' in response.text


def test_active_elections_page_renders_active_election(
    client: TestClient,
    db_session: Session,
) -> None:
    election = create_web_election(db_session, name="Visible web election")

    response = client.get("/elections")

    assert response.status_code == 200
    assert election.name in response.text


def test_election_detail_page_renders_candidates(
    client: TestClient,
    db_session: Session,
) -> None:
    election = create_web_election(db_session)
    candidate = Candidate(
        election_id=election.id,
        name="Web candidate",
        description="Candidate shown in web detail.",
    )
    db_session.add(candidate)
    db_session.commit()

    response = client.get(f"/elections/{election.id}")

    assert response.status_code == 200
    assert "Web candidate" in response.text
    assert "Cast vote" in response.text
    assert "locally in this browser" in response.text
    assert 'id="vote-package-required"' in response.text
    assert 'name="candidate_id"' in response.text
    assert 'id="vote-payload"' not in response.text
    assert 'src="/vendor/snarkjs.min.js"' in response.text


def test_results_page_renders(client: TestClient) -> None:
    response = client.get("/results")

    assert response.status_code == 200
    assert "Results" in response.text


def test_admin_dashboard_redirects_to_login_without_session(
    client: TestClient,
) -> None:
    response = client.get("/admin", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/admin/login"


def test_admin_login_page_renders(client: TestClient) -> None:
    response = client.get("/admin/login")

    assert response.status_code == 200
    assert "Admin login" in response.text


def test_admin_dashboard_contains_logout_form(
    admin_client: TestClient,
) -> None:
    response = admin_client.get("/admin")

    assert response.status_code == 200
    assert 'href="/admin"' in response.text
    assert 'href="/voter"' not in response.text
    assert 'href="/elections"' not in response.text
    assert 'href="/results"' not in response.text
    assert 'action="/admin/logout"' in response.text
    assert 'data-admin-action="cancel-election"' in response.text
    assert "Log out" in response.text


def test_admin_web_logout_clears_session(
    admin_client: TestClient,
) -> None:
    logout_response = admin_client.post("/admin/logout", follow_redirects=False)

    assert logout_response.status_code == 303
    assert logout_response.headers["location"] == "/admin/login"

    dashboard_response = admin_client.get("/admin", follow_redirects=False)

    assert dashboard_response.status_code == 303
    assert dashboard_response.headers["location"] == "/admin/login"
