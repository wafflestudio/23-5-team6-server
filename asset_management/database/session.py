from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from asset_management.database.settings import DB_SETTINGS

# Engine configured from environment (defaults to local SQLite for dev/tests).
ENGINE = create_engine(DB_SETTINGS.url, future=True)
SessionLocal = sessionmaker(bind=ENGINE, autocommit=False, autoflush=False, future=True)

# Import all models to ensure they are registered with SQLAlchemy
from asset_management.database import import_models
import_models()


@contextmanager
def session_scope():
    """Provide a transactional scope around a series of operations."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_session():
    """FastAPI dependency to inject a SQLAlchemy session per request."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
