import logging
import os

from sqlalchemy import inspect, text
from sqlmodel import Session, SQLModel, create_engine

from .config import settings

log = logging.getLogger(__name__)

os.makedirs(os.path.dirname(os.path.abspath(settings.database_path)), exist_ok=True)

engine = create_engine(f"sqlite:///{settings.database_path}", echo=False)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def migrate() -> None:
    """Add columns introduced after initial schema creation."""
    inspector = inspect(engine)
    with engine.connect() as conn:
        sub_cols = [c["name"] for c in inspector.get_columns("subscriber")]
        if "subscriber_platforms" not in sub_cols:
            conn.execute(text(
                "ALTER TABLE subscriber ADD COLUMN subscriber_platforms TEXT NOT NULL DEFAULT ''"
            ))
            conn.commit()
            log.info("Migration: added subscriber.subscriber_platforms")

        giveaway_cols = [c["name"] for c in inspector.get_columns("giveaway")]
        if "instructions" not in giveaway_cols:
            conn.execute(text("ALTER TABLE giveaway ADD COLUMN instructions TEXT"))
            conn.commit()
            log.info("Migration: added giveaway.instructions")


def get_session():
    with Session(engine) as session:
        yield session
