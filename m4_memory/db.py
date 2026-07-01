"""Tracelog M4 - memory.db layer (SEPARATE from M2 tracelog.db)."""
import sqlite3, os, pathlib
from contextlib import contextmanager
from typing import Optional, List, Dict
from datetime import datetime, timezone


def utc_now() -> str:
    now = datetime.now(timezone.utc)
    return now.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now.microsecond // 1000:03d}Z"


def get_memory_db_path() -> str:
    if os.name != "nt":
        return os.getenv("MEMORY_DB_PATH", "/data/memory.db")
    d = str(pathlib.Path(os.environ.get("TEMP","C:/Temp")) / "tracelog" / "memory.db")
    return os.getenv("MEMORY_DB_PATH", d)



_DDL_STEPS = "CREATE TABLE IF NOT EXISTS agent_steps (id INTEGER PRIMARY KEY AUTOINCREMENT, agent_id TEXT NOT NULL, step_number INTEGER NOT NULL, action_type TEXT CHECK(action_type IN ('file_write','bash','api_call','decision')), action_detail TEXT, result_summary TEXT, timestamp TEXT NOT NULL)"
_DDL_SNAPS = "CREATE TABLE IF NOT EXISTS file_snapshots (id INTEGER PRIMARY KEY AUTOINCREMENT, step_id INTEGER REFERENCES agent_steps(id), file_path TEXT NOT NULL, git_hash TEXT, diff_summary TEXT, timestamp TEXT NOT NULL)"
_INDEXES = ["CREATE INDEX IF NOT EXISTS idx_m4a ON agent_steps(agent_id)", "CREATE INDEX IF NOT EXISTS idx_m4b ON file_snapshots(step_id)", "CREATE INDEX IF NOT EXISTS idx_m4c ON file_snapshots(file_path)"]


def init_db() -> None:
    db_path = pathlib.Path(get_memory_db_path())
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(db_path)) as c:
        c.execute(_DDL_STEPS)
        c.execute(_DDL_SNAPS)
        for s in _INDEXES:
            c.execute(s)
        c.commit()


@contextmanager
def _conn():
    c = sqlite3.connect(get_memory_db_path(), check_same_thread=False)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA foreign_keys=ON")
    try:
        yield c
    finally:
        c.close()


def insert_step(agent_id: str, step_number: int, action_type: Optional[str],
            action_detail: Optional[str], result_summary: Optional[str]) -> int:
    ts = utc_now()
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO agent_steps(agent_id,step_number,action_type,action_detail,result_summary,timestamp)"
            "VALUES(?,?,?,?,?,?)",(agent_id,step_number,action_type,action_detail,result_summary,ts))
        c.commit(); return cur.lastrowid


def insert_snapshot(step_id: int, file_path: str, git_hash: Optional[str], diff_summary: Optional[str]) -> int:
    ts = utc_now()
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO file_snapshots(step_id,file_path,git_hash,diff_summary,timestamp)"
            "VALUES(?,?,?,?,?)",(step_id,file_path,git_hash,diff_summary,ts))
        c.commit(); return cur.lastrowid


def get_agent_steps(agent_id: str) -> List[Dict]:
    with _conn() as c:
        return [dict(r) for r in c.execute(
            "SELECT * FROM agent_steps WHERE agent_id=? ORDER BY step_number ASC",(agent_id,)).fetchall()]


def get_snapshots_for_step(step_id: int) -> List[Dict]:
    with _conn() as c:
        return [dict(r) for r in c.execute(
            "SELECT * FROM file_snapshots WHERE step_id=? ORDER BY timestamp ASC",(step_id,)).fetchall()]


def get_snapshots_for_file(file_path: str) -> List[Dict]:
    with _conn() as c:
        return [dict(r) for r in c.execute(
            "SELECT * FROM file_snapshots WHERE file_path=? ORDER BY timestamp ASC",(file_path,)).fetchall()]


def count_steps(agent_id: str) -> int:
    with _conn() as c:
        return c.execute("SELECT COUNT(*) FROM agent_steps WHERE agent_id=?",(agent_id,)).fetchone()[0]
