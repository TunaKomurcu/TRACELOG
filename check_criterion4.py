import sys, os, pathlib, uuid, importlib
sys.path.insert(0, r"C:\Users\t.komurcu\sazabi\m2_storage")
db_path = str(pathlib.Path(os.environ["TEMP"]) / "sazabi_persist_check.db")
os.environ["DB_PATH"] = db_path
import config, db as db_mod
importlib.reload(config); importlib.reload(db_mod)
db_mod.init_db()
sid = str(uuid.uuid4())
db_mod.insert_event(sid, "2025-01-15T14:00:00.000Z", "stdout", "persist_check_content", "agent")
print("Written. Simulating restart (module reload)...")
# Simulate process restart: reload all modules with same DB_PATH
importlib.reload(config); importlib.reload(db_mod)
rows = db_mod.query_events(sid)
assert len(rows) == 1, f"Expected 1 row, got {len(rows)}"
assert rows[0]["content"] == "persist_check_content"
print(f"Criterion 4 PASSED - data survived restart: {rows[0]}")