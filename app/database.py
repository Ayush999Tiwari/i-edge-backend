# ==========================================================
# Single SQLAlchemy database for the whole application.
#
# This replaces TWO previous, duplicate DB layers:
#   1. db_manager.py  - SQLAlchemy engine for vehicle_logs / video_jobs
#   2. database.py    - a second, raw sqlite3 DatabaseManager for
#                        live-surveillance "events"
#
# Both now share this one engine/session and write through the
# models in models.py. No detection logic lives here.
# ==========================================================
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Render / Neon PostgreSQL
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace(
            "postgres://",
            "postgresql://",
            1
        )

    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
    )

else:
    # Local development - existing SQLite
    from app.core.config import DATABASE_PATH

    engine = create_engine(
        f"sqlite:///{DATABASE_PATH}",
        connect_args={"check_same_thread": False},
    )


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    Base.metadata.create_all(bind=engine)