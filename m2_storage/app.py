"""Sazabi M2 - FastAPI log ingestion service"""
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Literal
from contextlib import asynccontextmanager
import db
from config import settings


class LogEvent(BaseModel):
    session_id: str
    timestamp: str
    stream: Optional[Literal["stdout", "stderr"]] = None
    content: str
    source: str


class EventOut(BaseModel):
    id: int
    session_id: str
    timestamp: str
    stream: Optional[str]
    content: str
    source: str


class SessionOut(BaseModel):
    session_id: str
    started_at: str
    last_event_at: str
    event_count: int


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    yield


app = FastAPI(title="Sazabi Storage Service", version="2.0.0", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok", "db": settings.DB_PATH}


@app.post("/events", status_code=201)
def post_event(event: LogEvent):
    event_id = db.insert_event(
        session_id=event.session_id,
        timestamp=event.timestamp,
        stream=event.stream,
        content=event.content,
        source=event.source,
    )
    return {"id": event_id}


@app.get("/events", response_model=List[EventOut])
def get_events(
    session_id: str = Query(..., description="Session UUID"),
    limit: int = Query(100, ge=1, le=10000),
    offset: int = Query(0, ge=0),
):
    return db.query_events(session_id, limit, offset)


@app.get("/sessions", response_model=List[SessionOut])
def get_sessions(limit: int = Query(50, ge=1, le=200)):
    return db.query_sessions(limit)
