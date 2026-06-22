from typing import Any

from fastapi import APIRouter, Depends, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.auth.session import (
    delete_admin_session,
    get_admin_from_session,
    is_admin_authenticated,
)
from app.core.deps import get_db
from app.models import Election, ElectionStatus
from app.repositories import election_repository
from app.services import candidate_service, tally_service, voting_service
from app.zkp.paths import PROJECT_ROOT, ensure_files_exist, get_zkp_artifact_paths


templates = Jinja2Templates(directory="app/web/templates")
SNARKJS_BROWSER_BUNDLE_PATH = (
    PROJECT_ROOT / "node_modules" / "snarkjs" / "build" / "snarkjs.min.js"
)

router = APIRouter(
    tags=["web"],
    include_in_schema=False,
)


def build_context(
    request: Request,
    active_nav: str,
    **extra_context: Any,
) -> dict[str, Any]:
    context = {
        "request": request,
        "active_nav": active_nav,
        "admin_username": get_admin_from_session(request),
        "is_admin": is_admin_authenticated(request),
    }
    context.update(extra_context)

    return context


def render_voter_entry(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "home.html",
        build_context(request, active_nav="voter"),
    )


@router.get("/vendor/snarkjs.min.js")
def serve_snarkjs_browser_bundle() -> FileResponse:
    ensure_files_exist([SNARKJS_BROWSER_BUNDLE_PATH])
    return FileResponse(
        SNARKJS_BROWSER_BUNDLE_PATH,
        media_type="application/javascript",
    )


@router.get("/zkp-artifacts/vote_eligibility.wasm")
def serve_vote_circuit_wasm() -> FileResponse:
    paths = get_zkp_artifact_paths()
    ensure_files_exist([paths.wasm_path])
    return FileResponse(
        paths.wasm_path,
        media_type="application/wasm",
    )


@router.get("/zkp-artifacts/vote_eligibility_final.zkey")
def serve_vote_circuit_zkey() -> FileResponse:
    paths = get_zkp_artifact_paths()
    ensure_files_exist([paths.zkey_path])
    return FileResponse(
        paths.zkey_path,
        media_type="application/octet-stream",
    )


@router.get("/", response_class=HTMLResponse)
def show_home(request: Request) -> HTMLResponse:
    return render_voter_entry(request)


@router.get("/voter", response_class=HTMLResponse)
def show_voter_entry(request: Request) -> HTMLResponse:
    return render_voter_entry(request)


@router.get("/elections", response_class=HTMLResponse)
def show_active_elections(
    request: Request,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "elections.html",
        build_context(
            request,
            active_nav="elections",
            elections=voting_service.list_active_elections(db),
        ),
    )


@router.get("/elections/{election_id}", response_class=HTMLResponse)
def show_election_details(
    election_id: int,
    request: Request,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    election = voting_service.get_active_election_details(db, election_id)
    candidates = voting_service.list_candidates_for_active_election(db, election_id)

    return templates.TemplateResponse(
        request,
        "election_detail.html",
        build_context(
            request,
            active_nav="elections",
            election=election,
            candidates=candidates,
        ),
    )


@router.get("/results", response_class=HTMLResponse)
def show_results_index(
    request: Request,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    closed_elections = election_repository.list_elections_by_status(
        db,
        ElectionStatus.CLOSED,
    )

    return templates.TemplateResponse(
        request,
        "results.html",
        build_context(
            request,
            active_nav="results",
            closed_elections=closed_elections,
            selected_results=None,
        ),
    )


@router.get("/results/{election_id}", response_class=HTMLResponse)
def show_election_results(
    election_id: int,
    request: Request,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    closed_elections = election_repository.list_elections_by_status(
        db,
        ElectionStatus.CLOSED,
    )
    results = tally_service.get_public_election_results(db, election_id)

    return templates.TemplateResponse(
        request,
        "results.html",
        build_context(
            request,
            active_nav="results",
            closed_elections=closed_elections,
            selected_results=results,
        ),
    )


@router.get("/admin/login", response_class=HTMLResponse)
def show_admin_login(request: Request) -> HTMLResponse:
    if is_admin_authenticated(request):
        return RedirectResponse(url="/admin", status_code=303)

    return templates.TemplateResponse(
        request,
        "login.html",
        build_context(request, active_nav="admin"),
    )


@router.post("/admin/logout")
def logout_admin_from_web(request: Request) -> RedirectResponse:
    delete_admin_session(request)
    return RedirectResponse(url="/admin/login", status_code=303)


@router.get("/admin", response_class=HTMLResponse)
def show_admin_dashboard(
    request: Request,
    db: Session = Depends(get_db),
):
    if not is_admin_authenticated(request):
        return RedirectResponse(url="/admin/login", status_code=303)

    elections: list[Election] = election_repository.list_elections(db)

    return templates.TemplateResponse(
        request,
        "admin.html",
        build_context(
            request,
            active_nav="admin",
            elections=elections,
        ),
    )
