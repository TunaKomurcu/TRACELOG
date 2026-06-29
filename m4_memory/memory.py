"""Sazabi M4 - High-level memory API: record_step, record_snapshot."""
import os, logging
from typing import Optional, List, Dict, Any
import db
import git_tracker

logger = logging.getLogger("sazabi.m4.memory")


def record_step(
    agent_id: str,
    step_number: int,
    action_type: Optional[str] = None,
    action_detail: Optional[str] = None,
    result_summary: Optional[str] = None,
    file_paths: Optional[List[str]] = None,
    repo_root: str = ".",
) -> Dict[str, Any]:
    """
    Record one agent step and optionally snapshot changed files.
    Returns dict with step_id and snapshot_ids.
    """
    step_id = db.insert_step(agent_id, step_number, action_type, action_detail, result_summary)
    snapshot_ids = []

    for fp in (file_paths or []):
        git_hash, diff_summary = git_tracker.snapshot_file(fp, repo_root)
        sid = db.insert_snapshot(step_id, fp, git_hash, diff_summary)
        snapshot_ids.append(sid)
        logger.debug(f"Snapshot {sid} for {fp} at step {step_id}")

    # Run full diff --stat for the step
    if git_tracker.is_git_repo(repo_root):
        full_diff = git_tracker.diff_stat(repo_root)
        if full_diff:
            logger.info(f"Step {step_id} diff --stat: {full_diff[:200]}")

    return {"step_id": step_id, "snapshot_ids": snapshot_ids}


def build_timeline(agent_id: str) -> Dict[str, Any]:
    """Assemble full timeline dict for an agent (Slack-ready JSON)."""
    steps = db.get_agent_steps(agent_id)
    enriched = []
    for step in steps:
        snapshots = db.get_snapshots_for_step(step["id"])
        enriched.append({
            "step_number": step["step_number"],
            "action_type": step["action_type"],
            "action_detail": step["action_detail"],
            "result_summary": step["result_summary"],
            "timestamp": step["timestamp"],
            "snapshots": [
                {"file_path": s["file_path"], "git_hash": s["git_hash"], "diff_summary": s["diff_summary"], "timestamp": s["timestamp"]}
                for s in snapshots
            ],
        })

    return {
        "agent_id": agent_id,
        "total_steps": len(steps),
        "steps": enriched,
        "summary": f"Agent {agent_id}: {len(steps)} steps recorded.",
    }



def summarise_with_llm(agent_id: str) -> dict:
    """Optional: summarise steps via M3 pipeline."""
    timeline = build_timeline(agent_id)
    try:
        import sys, pathlib as _pl
        m3 = _pl.Path(__file__).parent.parent / "m3_compression"
        if str(m3) not in sys.path:
            sys.path.insert(0, str(m3))
        import pipeline as _m3
        lines = []
        for st in timeline["steps"]:
            num = st["step_number"]
            atype = st["action_type"] or "unknown"
            rsumm = st["result_summary"] or ""
            lines.append(f"Step {num}: {atype} - {rsumm}")
        res = _m3.run(lines, session_id=agent_id)
        timeline["llm_summary"] = res.summary
    except Exception as e:
        logger.warning(f"M3 summarise failed: {e}")
        timeline["llm_summary"] = None
    return timeline
