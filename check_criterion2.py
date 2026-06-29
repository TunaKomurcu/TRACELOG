import sys, os, pathlib, threading, json, time
sys.path.insert(0, r"C:\Users\t.komurcu\sazabi\m2_storage")
db_path = str(pathlib.Path(os.environ["TEMP"]) / "sazabi_integration.db")
os.environ["DB_PATH"] = db_path
import importlib, config, db as db_mod, app as app_module
importlib.reload(config); importlib.reload(db_mod); importlib.reload(app_module)
db_mod.init_db()
# Start the FastAPI server in a thread via TestClient context
from fastapi.testclient import TestClient
import subprocess
# Simulate M1 forward_event by posting directly (same as forwarder does over HTTP)
with TestClient(app_module.app) as client:
 r = client.post("/events", json={"session_id":"integ-session-1","timestamp":"2025-01-15T14:23:01.234Z","stream":"stdout","content":"hello from m1","source":"agent"})
 assert r.status_code == 201, r.text
 event_id = r.json()["id"]
 # Verify via GET /events
 r2 = client.get("/events", params={"session_id": "integ-session-1"})
 assert r2.status_code == 200
 events = r2.json()
 assert len(events) == 1
 assert events[0]["content"] == "hello from m1"
 assert events[0]["stream"] == "stdout"
 print(f"Criterion 2 PASSED - event_id={event_id}, content verified via GET /events")