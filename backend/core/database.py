import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from backend.core.config import settings

db_url = settings.DATABASE_URL
connect_args = {}

if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    # If SQLite path is relative (e.g. sqlite:///./reserve_ai.db), resolve against project root
    if db_url.startswith("sqlite:///./") or (
        db_url.startswith("sqlite:///")
        and not db_url.startswith("sqlite:////")
        and not (len(db_url) > 11 and db_url[10] == ":")
    ):
        from pathlib import Path
        root_dir = Path(__file__).resolve().parent.parent.parent
        rel_path = db_url.replace("sqlite:///./", "").replace("sqlite:///", "")
        resolved = (root_dir / rel_path).resolve()
        db_url = f"sqlite:///{resolved.as_posix()}"
else:
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    if ("supabase" in db_url or "pooler.supabase.com" in db_url) and "sslmode" not in db_url:
        separator = "&" if "?" in db_url else "?"
        db_url = f"{db_url}{separator}sslmode=require"

engine_kwargs = {
    "pool_pre_ping": True,
}

if not db_url.startswith("sqlite"):
    engine_kwargs.update({
        "pool_size": 5,
        "max_overflow": 10,
        "pool_timeout": 10,
        "pool_recycle": 300,
    })

engine = create_engine(
    db_url,
    connect_args=connect_args,
    **engine_kwargs
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
