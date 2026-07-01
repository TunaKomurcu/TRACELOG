"""Tracelog M4 - FastAPI memory service."""
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from contextlib import asynccontextmanager
import db
import memory


class StepIn(BaseModel):
    agent_id: str
    step_number: int
    action_type: Optional[str] = None
    action_detail: Optional[str] = None
    result_summary: Optional[str] = None
    file_paths: Optional[List[str]] = None
    repo_root: str = "."


class SnapshotOut(BaseModel):
    file_path: str
    git_hash: Optional[str]
    diff_summary: Optional[str]
    timestamp: str


class StepOut(BaseModel):
    step_number: int
    action_type: Optional[str]
    action_detail: Optional[str]
    result_summary: Optional[str]
    timestamp: str
    snapshots: List[SnapshotOut] = []


class TimelineOut(BaseModel):
    agent_id: str
    total_steps: int
    steps: List[StepOut]
    summary: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    yield


app = FastAPI(title="Tracelog Memory Service", version="4.0.0", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok", "db": db.get_memory_db_path()}


@app.post("/memory/steps", status_code=201)
def record_step(step: StepIn):
    """Record one agent step with optional file snapshots."""
    result = memory.record_step(
        agent_id=step.agent_id,
        step_number=step.step_number,
        action_type=step.action_type,
        action_detail=step.action_detail,
        result_summary=step.result_summary,
        file_paths=step.file_paths or [],
        repo_root=step.repo_root,
    )
    return result


@app.get("/memory/agent/{agent_id}/timeline", response_model=TimelineOut)
def get_timeline(agent_id: str):
    """
    Full step timeline for an agent.
    Returns Slack-ready JSON with steps and file snapshots.
    """
    steps = db.get_agent_steps(agent_id)
    if not steps:
        raise HTTPException(status_code=404, detail=f"No steps found for agent {agent_id}")
    timeline = memory.build_timeline(agent_id)
    return timeline


@app.get("/memory/agent/{agent_id}/timeline/llm")
def get_timeline_llm(agent_id: str):
    """Timeline with optional LLM summary via M3."""
    steps = db.get_agent_steps(agent_id)
    if not steps:
        raise HTTPException(status_code=404, detail=f"No steps found for agent {agent_id}")
    return memory.summarise_with_llm(agent_id)


@app.get("/memory/agent/{agent_id}/snapshots")
def get_file_snapshots(agent_id: str, file_path: str = Query(...)):
    """All snapshots of a specific file for an agent."""
    return db.get_snapshots_for_file(file_path)


if __name__ == "__main__":
    import uvicorn, os
    uvicorn.run("api:app", host="0.0.0.0", port=int(os.getenv("MEMORY_PORT","8766")), reload=False)
