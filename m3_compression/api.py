"""Tracelog M3 - FastAPI log compression service."""
from datetime import datetime, timezone
import json
import sqlite3
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
from contextlib import asynccontextmanager
import pipeline

DB_PATH = Path(__file__).parent / "compression_history.db"


def _get_db():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _init_db():
    with _get_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS compression_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT,
                timestamp TEXT NOT NULL,
                severity TEXT NOT NULL,
                summary TEXT,
                errors_json TEXT
            )
            """
        )


def _get_severity(errors: list) -> str:
    severity = "info"
    for item in errors:
        if not isinstance(item, dict):
            continue
        level = str(item.get("severity", "")).lower()
        if level == "critical":
            return "critical"
        if level == "warning":
            severity = "warning"
    return severity


def _store_compression(result: dict, session_id: str):
    if not isinstance(result, dict):
        return
    errors = result.get("errors") if isinstance(result.get("errors"), list) else []
    severity = _get_severity(errors)
    summary = str(result.get("summary") or "")
    errors_json = json.dumps(errors, ensure_ascii=False)
    timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    with _get_db() as conn:
        conn.execute(
            "INSERT INTO compression_log (session_id, timestamp, severity, summary, errors_json) VALUES (?, ?, ?, ?, ?)",
            (session_id or "", timestamp, severity, summary, errors_json),
        )


class LogLines(BaseModel):
    lines: List[str]
    session_id: Optional[str] = ""


@asynccontextmanager
async def lifespan(app: FastAPI):
    _init_db()
    yield


app = FastAPI(title="Tracelog Compression Service", version="3.0.0", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/compress", status_code=200)
def compress(request: LogLines):
    """
    Compress log lines to structured summary.
    Returns JSON with summary, errors, anomalies, root_cause_hint.
    """
    result = pipeline.run(request.lines, request.session_id)
    payload = result.to_dict()
    _store_compression(payload, request.session_id)
    return payload


@app.get("/compressions")
def list_compressions(session_id: Optional[str] = None, limit: int = 50):
    """Son compression sonuçlarını listeler, alert sistemi için kullanılır."""
    with _get_db() as conn:
        query = "SELECT session_id, timestamp, severity, summary, errors_json FROM compression_log"
        params = []
        if session_id:
            query += " WHERE session_id = ?"
            params.append(session_id)
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(query, params).fetchall()
    results = []
    for row in rows:
        errors = []
        try:
            errors = json.loads(row["errors_json"] or "[]")
        except Exception:
            errors = []
        results.append(
            {
                "session_id": row["session_id"],
                "timestamp": row["timestamp"],
                "severity": row["severity"],
                "summary": row["summary"],
                "errors": errors,
            }
        )
    return results


if __name__ == "__main__":
    import uvicorn, os
    uvicorn.run("api:app", host="0.0.0.0", port=int(os.getenv("COMPRESSION_PORT","8002")), reload=False)
