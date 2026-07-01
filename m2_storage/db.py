"""Tracelog M2 - Database layer"""
import sqlite3, pathlib
from contextlib import contextmanager
from typing import Optional
from config import settings

_STREAM_VALS = chr(39)+"stdout"+chr(39)+","+chr(39)+"stderr"+chr(39)

_CREATE_TABLE = (
    "CREATE TABLE IF NOT EXISTS log_events ("
    "id INTEGER PRIMARY KEY AUTOINCREMENT, "
    "session_id TEXT NOT NULL, "
    "timestamp TEXT NOT NULL, "
    "stream TEXT CHECK(stream IN (" + _STREAM_VALS + ")), "
    "content TEXT NOT NULL, "
    "source TEXT NOT NULL)"
)

_CREATE_IDX1 = "CREATE INDEX IF NOT EXISTS idx_session ON log_events(session_id)"
_CREATE_IDX2 = "CREATE INDEX IF NOT EXISTS idx_timestamp ON log_events(timestamp)"


def _db_path()->str: return settings.DB_PATH


def init_db()->None:
    db_file=pathlib.Path(_db_path())
    db_file.parent.mkdir(parents=True,exist_ok=True)
    with sqlite3.connect(_db_path()) as c:
        c.execute(_CREATE_TABLE)
        c.execute(_CREATE_IDX1)
        c.execute(_CREATE_IDX2)
        c.commit()


@contextmanager
def _conn():
    c=sqlite3.connect(_db_path(),check_same_thread=False)
    c.row_factory=sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA synchronous=NORMAL")
    try:
        yield c
    finally:
        c.close()


def insert_event(session_id:str,timestamp:str,stream:Optional[str],content:str,source:str)->int:
    with _conn() as c:
        cur=c.execute(
            "INSERT INTO log_events(session_id,timestamp,stream,content,source) VALUES(?,?,?,?,?)",
            (session_id,timestamp,stream,content,source))
        c.commit()
        return cur.lastrowid


def insert_events_bulk(rows:list)->int:
    """rows = list of (session_id,timestamp,stream,content,source)"""
    with _conn() as c:
        c.executemany(
            "INSERT INTO log_events(session_id,timestamp,stream,content,source) VALUES(?,?,?,?,?)",
            rows)
        c.commit()
        return len(rows)


def query_events(session_id:str,limit:int=100,offset:int=0)->list:
    with _conn() as c:
        rows=c.execute(
            "SELECT id,session_id,timestamp,stream,content,source "
            "FROM log_events WHERE session_id=? "
            "ORDER BY timestamp ASC LIMIT ? OFFSET ?"
            ,(session_id,limit,offset)).fetchall()
        return [dict(r) for r in rows]


def query_sessions(limit:int=50)->list:
    with _conn() as c:
        rows=c.execute(
            "SELECT session_id, MIN(timestamp) AS started_at, "
            "MAX(timestamp) AS last_event_at, COUNT(*) AS event_count "
            "FROM log_events GROUP BY session_id "
            "ORDER BY started_at DESC LIMIT ?",(limit,)).fetchall()
        return [dict(r) for r in rows]


def count_events(session_id:str)->int:
    with _conn() as c:
        return c.execute("SELECT COUNT(*) FROM log_events WHERE session_id=?",(session_id,)).fetchone()[0]
