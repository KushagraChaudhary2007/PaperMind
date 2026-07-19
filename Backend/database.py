import os

from collections.abc import Generator

from sqlalchemy import (
    create_engine,
)

from sqlalchemy.orm import (
    DeclarativeBase,
    Session,
    sessionmaker,
)


# =========================================================
# Database configuration
# =========================================================

# Local development:
#
# sqlite:///./papermind.db
#
# Production:
#
# Railway will provide:
#
# sqlite:////data/papermind.db
#
# through the DATABASE_URL environment variable.

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./papermind.db",
)


# =========================================================
# SQLAlchemy engine configuration
# =========================================================

engine_options = {}


# SQLite requires this setting because FastAPI may use
# database connections across different request threads.

if DATABASE_URL.startswith(
    "sqlite"
):
    engine_options[
        "connect_args"
    ] = {
        "check_same_thread": False,
    }


engine = create_engine(
    DATABASE_URL,
    **engine_options,
)


# =========================================================
# Database session
# =========================================================

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


# =========================================================
# Base SQLAlchemy model
# =========================================================

class Base(
    DeclarativeBase
):
    pass


# =========================================================
# Database dependency
# =========================================================

def get_db() -> Generator[
    Session,
    None,
    None,
]:
    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()