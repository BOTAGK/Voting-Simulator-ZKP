from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_app_dockerfile_contains_demo_scripts_and_circuits() -> None:
    dockerfile = (PROJECT_ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert "COPY scripts ./scripts" in dockerfile
    assert "COPY circuits ./circuits" in dockerfile


def test_compose_mounts_demo_output_directory() -> None:
    compose_file = (PROJECT_ROOT / "docker-compose.yml").read_text(
        encoding="utf-8"
    )

    assert "./output:/app/output" in compose_file
