# SAZABI - End-to-End Test Guide

## Overview
SAZABI is a distributed system for AI agent trace log analysis with Slack integration. This guide walks through complete setup and testing from scratch.

## System Architecture
- **M1 Logger**: Structured logging library
- **M2 Storage**: Log storage service (HTTP API, SQLite)
- **M3 Compression**: Log compression & anomaly detection (library)
- **M4 Memory**: Agent timeline storage (HTTP API, SQLite)
- **M5 Sandbox**: Code execution sandbox (HTTP API)
- **M6 Slack Bot**: Slack control panel (Slash commands)

## Prerequisites
- Python 3.14+
- pip
- Git
- Slack Workspace (with admin access for bot creation)
- 5GB free disk space

---

## Step 1: Clone Repository

```bash
git clone <repository-url>
cd SAZABI
```

---

## Step 2: Environment Setup

### 2.1 Install Python Dependencies

Each module has its own `requirements.txt`. Install all:

```bash
# M1 (Logger - library only, no install needed)
cd m1_logger
# No requirements.txt - uses stdlib

# M2 (Storage)
cd ../m2_storage
pip install -r requirements.txt

# M3 (Compression)
cd ../m3_compression
pip install -r requirements.txt

# M4 (Memory)
cd ../m4_memory
pip install -r requirements.txt

# M5 (Sandbox)
cd ../m5_sandbox
pip install -r requirements.txt

# M6 (Slack Bot)
cd ../m6_slack
pip install -r requirements.txt
```

### 2.2 Configure Environment Variables

Each module has a `.env.example` file. Copy and configure:

#### M2 Storage (.env)
```bash
cd m2_storage
cp .env.example .env
```

Edit `.env`:
```bash
DB_PATH=/data/sazabi.db
SERVICE_HOST=0.0.0.0
SERVICE_PORT=8765
LOG_LEVEL=info
API_SECRET=your-random-secret-here
```

Generate random secret:
```powershell
# PowerShell
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | ForEach-Object {[char]$_})
```

#### M3 Compression (.env)
```bash
cd ../m3_compression
cp .env.example .env
```

Edit `.env`:
```bash
# Optional: Google AI API key for LLM fallback
GOOGLE_API_KEY=
# Leave empty to use rule-based only (recommended)
```

#### M4 Memory (.env)
```bash
cd ../m4_memory
cp .env.example .env
```

Edit `.env`:
```bash
DB_PATH=/data/memory.db
SERVICE_HOST=0.0.0.0
SERVICE_PORT=8766
LOG_LEVEL=info
```

#### M5 Sandbox (.env)
```bash
cd ../m5_sandbox
cp .env.example .env
```

Edit `.env`:
```bash
SERVICE_HOST=0.0.0.0
SERVICE_PORT=8767
LOG_LEVEL=info
MAX_EXECUTION_SECONDS=30
```

#### M6 Slack Bot (.env)
```bash
cd ../m6_slack
cp .env.example .env
```

Edit `.env`:
```bash
SLACK_BOT_TOKEN=xoxb-your-bot-token-here
SLACK_SIGNING_SECRET=your-signing-secret-here
SLACK_ALERT_CHANNEL=#sazabi-alerts
M2_URL=http://localhost:8765
M4_URL=http://localhost:8766
M5_URL=http://localhost:8767
HTTP_TIMEOUT=5
```

### 2.3 Create Slack App

1. Go to https://api.slack.com/apps
2. Click "Create New App" → "From scratch"
3. App Name: `Sazabi Bot`
4. Workspace: Select your workspace
5. **OAuth & Permissions**:
   - Scroll to "Scopes" → "Bot Token Scopes"
   - Add: `chat:write`, `commands`
6. **Install to Workspace**:
   - Click "Install to Workspace"
   - Copy **Bot User OAuth Token** → `SLACK_BOT_TOKEN`
7. **Slash Commands**:
   - Go to "Slash Commands" → "Create New Command"
   - Command: `/sazabi`
   - Request URL: `https://your-domain.com/slack/events` (for Socket Mode, leave blank)
   - Description: `Sazabi system control`
8. **Basic Information**:
   - Scroll to "App Credentials"
   - Copy **Signing Secret** → `SLACK_SIGNING_SECRET`

**Note**: For local testing, use Socket Mode (no public URL needed).

---

## Step 3: Initialize Databases

### 3.1 M2 Storage Database

```bash
cd m2_storage
python -c "from db import init_db; init_db()"
```

This creates `/data/sazabi.db` with required tables.

### 3.2 M4 Memory Database

```bash
cd ../m4_memory
python -c "from db import init_db; init_db()"
```

This creates `/data/memory.db` with required tables.

---

## Step 4: Start Services

Start services in order (M2 → M4 → M5 → M6). Use separate terminals.

### 4.1 Start M2 Storage (Port 8765)

```bash
cd m2_storage
python app.py
```

Expected output:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8765
```

### 4.2 Start M4 Memory (Port 8766)

```bash
cd m4_memory
python api.py
```

Expected output:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8766
```

### 4.3 Start M5 Sandbox (Port 8767)

```bash
cd m5_sandbox
python api.py
```

Expected output:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8767
```

### 4.4 Start M6 Slack Bot

```bash
cd m6_slack
python app.py
```

Expected output:
```
⚡️ Bolt app is running!
```

---

## Step 5: Verify Health Checks

### 5.1 Test M2 Health

```bash
curl http://localhost:8765/health
```

Expected response:
```json
{"status": "ok"}
```

### 5.2 Test M4 Health

```bash
curl http://localhost:8766/health
```

Expected response:
```json
{"status": "ok"}
```

### 5.3 Test M5 Health

```bash
curl http://localhost:8767/health
```

Expected response:
```json
{"status": "ok"}
```

---

## Step 6: Slack Bot Testing

### 6.1 Test `/sazabi status`

In Slack workspace, type:
```
/sazabi status
```

Expected response:
```
🔍 Sazabi System Status
✅ M2 Storage: ok
✅ M4 Memory: ok
✅ M5 Sandbox: ok
✅ M3 Compressor: ok (library)
✅ M1 Logger: ok (library)
```

**Acceptance Criteria**: All services show "ok" status.

### 6.2 Test `/sazabi run`

In Slack, type:
```
/sazabi run python -c "print(1+1)"
```

Expected response:
```
✅ Sandbox Result
Command: `python -c "print(1+1)"`
Status: completed | Exit: `0` | Time: 50ms

stdout:
```
2
```
```

**Acceptance Criteria**: Output shows "2".

### 6.3 Test `/sazabi run` with Error

In Slack, type:
```
/sazabi run python -c "1/0"
```

Expected response:
```
❌ Sandbox Result
Command: `python -c "1/0"`
Status: completed | Exit: `1` | Time: 30ms

stderr:
```
ZeroDivisionError: division by zero
```
```

### 6.4 Test `/sazabi run` without Argument

In Slack, type:
```
/sazabi run
```

Expected response:
```
❌ Error: Usage: /sazabi run <command>
```

### 6.5 Test `/sazabi memory`

First, create some agent activity (simulate agent run):
```bash
# In terminal, send some logs to M2
curl -X POST http://localhost:8765/events \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-session-001",
    "agent_id": "test-agent-001",
    "timestamp": "2024-01-01T00:00:00Z",
    "level": "info",
    "content": "Agent started",
    "metadata": {"action_type": "bash", "result_summary": "ok"}
  }'
```

In Slack, type:
```
/sazabi memory test-agent-001
```

Expected response:
```
🧠 Agent Memory
Agent: `test-agent-001` | Steps: 1

Step 1 `bash`: ok
```

### 6.6 Test `/sazabi memory` without Argument

In Slack, type:
```
/sazabi memory
```

Expected response:
```
❌ Error: Usage: /sazabi memory <agent_id>
```

### 6.7 Test `/sazabi logs`

First, create some logs:
```bash
curl -X POST http://localhost:8765/events \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test-session-002",
    "agent_id": "test-agent-002",
    "timestamp": "2024-01-01T00:00:00Z",
    "level": "info",
    "content": "Processing request",
    "metadata": {}
  }'
```

In Slack, type:
```
/sazabi logs test-session-002
```

Expected response:
```
📜 Log Summary
Session: `test-session-002`
No summary.
```

### 6.8 Test `/sazabi logs` without Argument

In Slack, type:
```
/sazabi logs
```

Expected response:
```
❌ Error: Usage: /sazabi logs <session_id>
```

### 6.9 Test `/sazabi alerts`

In Slack, type:
```
/sazabi alerts
```

Expected response:
```
🚨 Recent Alerts (60 min)
✅ No critical alerts.
```

---

## Step 7: Test Alert Mechanism

### 7.1 Simulate Critical Error

Create logs with error patterns:
```bash
curl -X POST http://localhost:8765/events \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "critical-test-001",
    "agent_id": "test-agent",
    "timestamp": "2024-01-01T00:00:00Z",
    "level": "error",
    "content": "Connection refused: database down",
    "metadata": {}
  }'
```

### 7.2 Trigger Alert Check

The system automatically detects critical errors. To verify:
- Check Slack channel `#sazabi-alerts` (or your configured channel)
- Should see a message like:
```
🚨 CRITICAL ALERT
Session: `critical-test-001`
🔴 Connection refused: database down
```

**Note**: This requires M3 compression to detect the error as critical.

---

## Step 8: Performance Testing

### 8.1 Test Response Time (< 3 seconds)

All Slack commands should respond within 3 seconds (Slack's timeout).

Test with:
```
/sazabi status
```

Measure time from command send to response receipt.

**Acceptance Criteria**: < 3 seconds

### 8.2 Test Concurrent Requests

```bash
# Send 10 concurrent health checks
for i in {1..10}; do
  curl http://localhost:8765/health &
done
wait
```

All should return `{"status": "ok"}`.

---

## Step 9: Unit Tests

Run unit tests for each module:

```bash
# M1
cd m1_logger
python -m pytest tests/test_m1.py -v

# M2
cd ../m2_storage
python -m pytest tests/test_m2.py -v

# M3
cd ../m3_compression
python -m pytest tests/test_m3.py -v

# M4
cd ../m4_memory
python -m pytest tests/test_m4.py -v

# M5
cd ../m5_sandbox
python -m pytest tests/test_m5.py -v

# M6
cd ../m6_slack
python -m pytest tests/test_m6.py -v
```

**Acceptance Criteria**: All tests pass.

---

## Step 10: Integration Test (Full Flow)

### 10.1 Complete Agent Run Simulation

1. Start a session:
```bash
curl -X POST http://localhost:8765/events \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "integration-test-001",
    "agent_id": "integration-agent",
    "timestamp": "2024-01-01T00:00:00Z",
    "level": "info",
    "content": "Agent started",
    "metadata": {"action_type": "init", "result_summary": "ok"}
  }'
```

2. Execute code via Slack:
```
/sazabi run python -c "print('Hello from SAZABI')"
```

3. Check logs via Slack:
```
/sazabi logs integration-test-001
```

4. Check memory via Slack:
```
/sazabi memory integration-agent
```

5. Check system status:
```
/sazabi status
```

**Acceptance Criteria**: All commands work, data flows correctly through M2 → M3 → M4 → M5 → M6.

---

## Troubleshooting

### Issue: "No logs: session_id"
**Cause**: Session doesn't exist in M2 database.
**Solution**: First create logs via POST to `/events` endpoint.

### Issue: "Memory error"
**Cause**: Agent doesn't exist in M4 database.
**Solution**: Agent timeline is created automatically when logs are sent with `agent_id`.

### Issue: Slack bot "invalid_auth"
**Cause**: Invalid SLACK_BOT_TOKEN or SLACK_SIGNING_SECRET.
**Solution**: Re-check Slack app credentials.

### Issue: Services won't start
**Cause**: Port already in use.
**Solution**: Change port in `.env` or kill conflicting process.

### Issue: M3 compression fails
**Cause**: Missing dependencies or import error.
**Solution**: Check `m3_compression` is in Python path, reinstall requirements.

---

## Cleanup

Stop all services (Ctrl+C in each terminal).

To remove databases:
```bash
rm /data/sazabi.db
rm /data/memory.db
```

---

## Success Criteria

✅ All services start without errors
✅ All health checks return `{"status": "ok"}`
✅ `/sazabi status` shows all services as "ok"
✅ `/sazabi run python -c "print(1+1)"` returns "2"
✅ `/sazabi memory <agent_id>` shows timeline
✅ `/sazabi logs <session_id>` shows compressed summary
✅ `/sazabi alerts` shows recent anomalies
✅ Critical errors trigger Slack alerts
✅ All commands respond within 3 seconds
✅ All unit tests pass
