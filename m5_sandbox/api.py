"""Tracelog M5 - FastAPI sandbox service."""
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager
import runner, webhook

_results: Dict[str, Dict[str, Any]] = {}


class RunRequest(BaseModel):
    command: str
    sandbox_id: Optional[str] = None
    notify_webhook: bool = True


class RunResult(BaseModel):
    sandbox_id: str
    command: str
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: float
    resource_usage: Dict[str, Any]
    status: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="Tracelog Sandbox Service", version="5.0.0", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok", "service": "m5_sandbox"}


@app.post("/sandbox/run", response_model=RunResult, status_code=200)
def run_command(req: RunRequest):
    """Run a sandboxed command. Returns structured result."""
    result = runner.run_sandboxed(req.command, req.sandbox_id)
    _results[result["sandbox_id"]] = result
    # Forward to M6 webhook (fire-and-forget)
    if req.notify_webhook:
        webhook.send_result(result)
    return result


@app.get("/sandbox/{sandbox_id}", response_model=RunResult)
def get_result(sandbox_id: str):
    if sandbox_id not in _results:
        raise HTTPException(status_code=404, detail=f"Sandbox {sandbox_id} not found")
    return _results[sandbox_id]


@app.post("/webhook/sandbox-result", status_code=200)
def receive_webhook(payload: Dict[str, Any]):
    """M6 integration: receive sandbox result from upstream."""
    sid = payload.get("sandbox_id", "unknown")
    _results[sid] = payload
    return {"received": True, "sandbox_id": sid}
