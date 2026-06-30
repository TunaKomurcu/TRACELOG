"""Sazabi M2 - Test Suite
Run: pytest tests/test_m2.py -v
"""
import os, sys, json, time, uuid, pathlib, tempfile, pytest

from fastapi.testclient import TestClient


@pytest.fixture(scope="function")
def tmp_db(tmp_path, monkeypatch):
    """Each test gets its own temp SQLite file."""
    db_file = str(tmp_path / "test.db")
    monkeypatch.setenv("DB_PATH", db_file)
    # Save original sys.path and clean competing paths
    original_path = sys.path.copy()
    m2_dir = str(pathlib.Path(__file__).parent.parent)
    # Remove competing module paths
    sys.path = [p for p in sys.path if not any(x in p for x in ["m1_logger","m3_compression","m4_memory","m5_sandbox","m6_slack"])]
    if m2_dir not in sys.path:
        sys.path.insert(0, m2_dir)
    # Clean stale module references before reimporting
    import importlib
    for mod_key in list(sys.modules.keys()):
        if mod_key in ('app', 'db', 'config') or mod_key.startswith(('m2_storage.',)):
            del sys.modules[mod_key]
    # Import fresh modules
    import config, db
    importlib.reload(config)
    importlib.reload(db)
    # Import app after config/db are ready
    import app as app_module
    importlib.reload(app_module)
    db.init_db()
    result = (db_file, app_module.app)
    yield result
    # Restore sys.path after test
    sys.path = original_path


@pytest.fixture(scope="function")
def client(tmp_db):
    _, fastapi_app = tmp_db
    with TestClient(fastapi_app) as c:
        yield c


class TestHealth:
    def test_health_ok(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


class TestPostEvent:
    def _payload(self, **kwargs):
        base = {"session_id": str(uuid.uuid4()), "timestamp": "2025-01-15T14:23:01.234Z","stream": "stdout", "content": "hello", "source": "agent"}
        base.update(kwargs)
        return base

    def test_post_returns_id(self, client):
        r = client.post("/events", json=self._payload())
        assert r.status_code == 201
        assert "id" in r.json()
        assert isinstance(r.json()["id"], int)

    def test_post_stdout(self, client):
        r = client.post("/events", json=self._payload(stream="stdout"))
        assert r.status_code == 201

    def test_post_stderr(self, client):
        r = client.post("/events", json=self._payload(stream="stderr"))
        assert r.status_code == 201

    def test_post_invalid_stream(self, client):
        r = client.post("/events", json=self._payload(stream="bad"))
        # SQLite CHECK constraint - should fail at db or return error
        assert r.status_code in (400, 422, 500)

    def test_post_no_stream(self, client):
        p = self._payload()
        del p["stream"]
        r = client.post("/events", json=p)
        assert r.status_code == 201


class TestGetEvents:
    def test_get_events_returns_list(self, client):
        sid = str(uuid.uuid4())
        for x in range(5):
            client.post("/events", json={"session_id":sid,"timestamp":f"2025-01-15T14:23:0{x}.000Z","stream":"stdout","content":f"line {x}","source":"agent"})
        r = client.get("/events", params={"session_id": sid})
        assert r.status_code == 200
        assert len(r.json()) == 5

    def test_get_events_content_correct(self, client):
        sid = str(uuid.uuid4())
        client.post("/events", json={"session_id":sid,"timestamp":"2025-01-15T14:23:01.000Z","stream":"stdout","content":"unique_xyz","source":"agent"})
        r = client.get("/events", params={"session_id": sid})
        assert r.json()[0]["content"] == "unique_xyz"

    def test_get_events_limit(self, client):
        sid = str(uuid.uuid4())
        for x in range(10):
            client.post("/events", json={"session_id":sid,"timestamp":f"2025-01-15T14:23:{x:02d}.000Z","stream":"stdout","content":f"l{x}","source":"agent"})
        r = client.get("/events", params={"session_id": sid, "limit": 3})
        assert len(r.json()) == 3

    def test_get_events_offset(self, client):
        sid = str(uuid.uuid4())
        for x in range(5):
            client.post("/events", json={"session_id":sid,"timestamp":f"2025-01-15T14:23:0{x}.000Z","stream":"stdout","content":f"l{x}","source":"agent"})
        r = client.get("/events", params={"session_id": sid, "offset": 3})
        assert len(r.json()) == 2

    def test_get_events_session_isolation(self, client):
        s1, s2 = str(uuid.uuid4()), str(uuid.uuid4())
        client.post("/events", json={"session_id":s1,"timestamp":"2025-01-15T14:23:01.000Z","stream":"stdout","content":"A","source":"agent"})
        client.post("/events", json={"session_id":s2,"timestamp":"2025-01-15T14:23:02.000Z","stream":"stdout","content":"B","source":"agent"})
        assert len(client.get("/events", params={"session_id": s1}).json()) == 1
        assert len(client.get("/events", params={"session_id": s2}).json()) == 1


class TestGetSessions:
    def test_sessions_returns_list(self, client):
        sid = str(uuid.uuid4())
        client.post("/events", json={"session_id":sid,"timestamp":"2025-01-15T14:23:01.000Z","stream":"stdout","content":"x","source":"agent"})
        r = client.get("/sessions")
        assert r.status_code == 200
        sessions = r.json()
        assert any(s["session_id"] == sid for s in sessions)

    def test_session_has_required_fields(self, client):
        sid = str(uuid.uuid4())
        client.post("/events", json={"session_id":sid,"timestamp":"2025-01-15T14:23:01.000Z","stream":"stdout","content":"x","source":"agent"})
        sessions = client.get("/sessions").json()
        s = next(s for s in sessions if s["session_id"] == sid)
        assert "started_at" in s
        assert "last_event_at" in s
        assert "event_count" in s
        assert s["event_count"] == 1


class TestPerformance:
    """Kabul kriteri 3: 10k write + p95 read < 50ms."""

    def test_10k_write_and_p95_read(self, tmp_db):
        db_file, fastapi_app = tmp_db
        import db as db_mod, importlib, config
        importlib.reload(config)
        importlib.reload(db_mod)
        db_mod.init_db()
        sid = str(uuid.uuid4())
        # Bulk insert 10k rows
        rows = [(sid, f"2025-01-15T14:{i//60:02d}:{i%60:02d}.000Z", "stdout", f"line {i}", "agent") for i in range(10000)]
        db_mod.insert_events_bulk(rows)
        # Measure p95 of 100 reads
        timings = []
        for _ in range(100):
            t0 = time.perf_counter()
            db_mod.query_events(sid, limit=100, offset=0)
            timings.append((time.perf_counter() - t0) * 1000)
        timings.sort()
        p95 = timings[94]
        print(f"p95 read latency: {p95:.2f}ms")
        assert p95 < 50, f"p95 {p95:.2f}ms exceeded 50ms"


class TestPersistence:
    """Kabul kriteri 4: restart ta veri kaybolmuyor (volume simulation)."""

    def test_data_survives_db_reconnect(self, tmp_db, monkeypatch):
        db_file, _ = tmp_db
        import importlib, config, db as db_mod
        sid = str(uuid.uuid4())
        db_mod.insert_event(sid, "2025-01-15T14:23:01.000Z", "stdout", "persist_test", "agent")
        # Simulate restart: reload module (new connections, same file)
        importlib.reload(config)
        importlib.reload(db_mod)
        rows = db_mod.query_events(sid)
        assert len(rows) == 1
        assert rows[0]["content"] == "persist_test"


class TestSchema:
    def test_event_fields(self, client):
        sid = str(uuid.uuid4())
        client.post("/events", json={"session_id":sid,"timestamp":"2025-01-15T14:23:01.000Z","stream":"stderr","content":"schema test","source":"cicd"})
        events = client.get("/events", params={"session_id":sid}).json()
        e = events[0]
        for field in ["id","session_id","timestamp","stream","content","source"]:
            assert field in e, f"Missing field: {field}"
        assert e["stream"] == "stderr"
        assert e["source"] == "cicd"

    def test_source_agent_cicd_api(self, client):
        sid = str(uuid.uuid4())
        for src in ["agent","cicd","api"]:
            r = client.post("/events", json={"session_id":sid,"timestamp":"2025-01-15T14:23:01.000Z","stream":"stdout","content":"x","source":src})
            assert r.status_code == 201
