from __future__ import annotations
"""Persistent AURA storage.

SQLite is the zero-config local/default store. Set AURA_DATABASE_URL to a
PostgreSQL URL in production; psycopg is loaded only when that URL is used.
"""
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
SQLITE_PATH = Path(os.getenv("AURA_SQLITE_PATH", str(DATA_DIR / "aura.db")))
DATABASE_URL = os.getenv("AURA_DATABASE_URL", "").strip()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _is_postgres() -> bool:
    return DATABASE_URL.startswith(("postgres://", "postgresql://"))


def _sqlite():
    SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(SQLITE_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    if _is_postgres():
        try:
            import psycopg
            with psycopg.connect(DATABASE_URL) as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS aura_projects (
                            project_id TEXT PRIMARY KEY,
                            snapshot_json TEXT NOT NULL,
                            updated_at TEXT NOT NULL
                        )
                    """)
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS aura_executions (
                            execution_id TEXT PRIMARY KEY,
                            project_id TEXT NOT NULL,
                            snapshot_json TEXT NOT NULL,
                            created_at TEXT NOT NULL
                        )
                    """)
                conn.commit()
            return
        except ImportError as exc:
            raise RuntimeError("AURA_DATABASE_URL points to PostgreSQL but psycopg is not installed.") from exc
    with _sqlite() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS aura_projects (
                project_id TEXT PRIMARY KEY,
                snapshot_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS aura_executions (
                execution_id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                snapshot_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_aura_exec_project ON aura_executions(project_id, created_at DESC);
        """)


def upsert_project(project_id: str, snapshot: dict[str, Any]) -> None:
    payload = json.dumps(snapshot, ensure_ascii=False)
    stamp = _now()
    if _is_postgres():
        import psycopg
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO aura_projects(project_id, snapshot_json, updated_at)
                    VALUES (%s, %s, %s)
                    ON CONFLICT(project_id) DO UPDATE SET snapshot_json=EXCLUDED.snapshot_json, updated_at=EXCLUDED.updated_at
                """, (project_id, payload, stamp))
            conn.commit()
        return
    with _sqlite() as conn:
        conn.execute("""
            INSERT INTO aura_projects(project_id, snapshot_json, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(project_id) DO UPDATE SET snapshot_json=excluded.snapshot_json, updated_at=excluded.updated_at
        """, (project_id, payload, stamp))
        conn.commit()


def load_projects() -> dict[str, dict[str, Any]]:
    init_db()
    if _is_postgres():
        import psycopg
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT project_id, snapshot_json FROM aura_projects")
                rows = cur.fetchall()
    else:
        with _sqlite() as conn:
            rows = conn.execute("SELECT project_id, snapshot_json FROM aura_projects").fetchall()
    out: dict[str, dict[str, Any]] = {}
    for row in rows:
        project_id, raw = row[0], row[1]
        try:
            value = json.loads(raw)
            if isinstance(value, dict): out[str(project_id)] = value
        except Exception:
            continue
    return out


def save_execution(execution_id: str, project_id: str, snapshot: dict[str, Any]) -> None:
    payload = json.dumps(snapshot, ensure_ascii=False)
    stamp = _now()
    if _is_postgres():
        import psycopg
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO aura_executions(execution_id, project_id, snapshot_json, created_at)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT(execution_id) DO UPDATE SET snapshot_json=EXCLUDED.snapshot_json
                """, (execution_id, project_id, payload, stamp))
            conn.commit()
        return
    with _sqlite() as conn:
        conn.execute("""
            INSERT INTO aura_executions(execution_id, project_id, snapshot_json, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(execution_id) DO UPDATE SET snapshot_json=excluded.snapshot_json
        """, (execution_id, project_id, payload, stamp))
        conn.commit()


def load_executions(project_id: str) -> list[dict[str, Any]]:
    init_db()
    if _is_postgres():
        import psycopg
        with psycopg.connect(DATABASE_URL) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT snapshot_json FROM aura_executions WHERE project_id=%s ORDER BY created_at DESC", (project_id,))
                rows = cur.fetchall()
    else:
        with _sqlite() as conn:
            rows = conn.execute("SELECT snapshot_json FROM aura_executions WHERE project_id=? ORDER BY created_at DESC", (project_id,)).fetchall()
    out=[]
    for row in rows:
        try:
            value=json.loads(row[0])
            if isinstance(value, dict): out.append(value)
        except Exception:
            pass
    return out


def storage_info() -> dict[str, Any]:
    return {
        "backend": "postgresql" if _is_postgres() else "sqlite",
        "persistent": True,
        "location": "AURA_DATABASE_URL" if _is_postgres() else str(SQLITE_PATH),
        "production_ready": _is_postgres(),
    }
