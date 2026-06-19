from pathlib import Path
from typing import Any

from sqlalchemy import MetaData, create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import Settings, get_settings


NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


settings: Settings = get_settings()


def ensure_sqlite_parent_dir(database_url: str) -> None:
    if not database_url.startswith("sqlite:///"):
        return

    raw_path: str = database_url.removeprefix("sqlite:///")

    if raw_path == ":memory:":
        return

    Path(raw_path).expanduser().parent.mkdir(parents=True, exist_ok=True)


def get_connect_args(database_url: str) -> dict[str, bool]:
    if database_url.startswith("sqlite"):
        return {"check_same_thread": False}

    return {}


def create_app_engine(database_url: str) -> Engine:
    ensure_sqlite_parent_dir(database_url)

    engine = create_engine(
        database_url,
        connect_args=get_connect_args(database_url),
    )

    if database_url.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def enable_foreign_keys(
            dbapi_connection: Any,
            _connection_record: Any,
        ) -> None:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


engine = create_app_engine(settings.database_url)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


def init_db() -> None:
    import app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
