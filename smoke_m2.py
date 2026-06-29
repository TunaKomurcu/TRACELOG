import sys, os, pathlib
sys.path.insert(0, r"C:\Users\t.komurcu\sazabi\m2_storage")
os.environ["DB_PATH"] = str(pathlib.Path(os.environ["TEMP"]) / "sazabi_smoke.db")
import importlib, config, db, app as app_module
importlib.reload(config); importlib.reload(db); importlib.reload(app_module)
db.init_db()
from fastapi.testclient import TestClient
with TestClient(app_module.app) as c:
 r = c.get("/health")
 assert r.status_code == 200
 assert r.json()["status"] == "ok"
 r2 = c.get("/sessions")
 assert r2.status_code == 200
 r3 = c.post("/events", json={"session_id":"abc","timestamp":"2025-01-15T14:00:00.000Z","stream":"stdout","content":"smoke","source":"agent"})
 assert r3.status_code == 201
 print("Smoke test PASSED - app boots and all endpoints respond correctly")