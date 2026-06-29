import sys, os, pathlib, time, uuid
sys.path.insert(0, r"C:\Users\t.komurcu\sazabi\m2_storage")
db_path = str(pathlib.Path(os.environ["TEMP"]) / "sazabi_perf.db")
os.environ["DB_PATH"] = db_path
import importlib, config, db as db_mod
importlib.reload(config); importlib.reload(db_mod)
db_mod.init_db()
sid = str(uuid.uuid4())
rows = [(sid, f"2025-01-15T14:{i//3600:02d}:{(i%3600)//60:02d}.{i%1000:03d}Z", "stdout", f"line {i}", "agent") for i in range(10000)]
t0 = time.perf_counter()
db_mod.insert_events_bulk(rows)
write_ms = (time.perf_counter()-t0)*1000
print(f"10k bulk write: {write_ms:.1f}ms")
timings = []
for _ in range(200):
 t0 = time.perf_counter()
 db_mod.query_events(sid, limit=100, offset=0)
 timings.append((time.perf_counter()-t0)*1000)
timings.sort()
p50 = timings[99]; p95 = timings[189]; p99 = timings[197]
print(f"Read p50={p50:.2f}ms p95={p95:.2f}ms p99={p99:.2f}ms")
assert p95 < 50, f"p95 {p95:.2f}ms > 50ms FAILED"
print("Criterion 3 PASSED")