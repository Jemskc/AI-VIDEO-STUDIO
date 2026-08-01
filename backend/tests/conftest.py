"""
Shared pytest setup: run against a throwaway SQLite DB and execute Celery
tasks eagerly (in-process), so the test suite doesn't require a real
Postgres/Redis stack to run.
"""
import os
import sys
from pathlib import Path

TEST_DB_PATH = Path(__file__).resolve().parent / "test_db.sqlite3"
os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB_PATH}"

if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.workers.celery_app import celery_app  # noqa: E402

celery_app.conf.update(task_always_eager=True)
