# TRACELOG

AI Agent Trace Log Analysis System with Slack Integration

## Overview

TRACELOG is a distributed system for analyzing AI agent trace logs with real-time anomaly detection, compression, and Slack-based monitoring. It provides a complete observability stack for AI agent operations.

## Architecture

TRACELOG consists of 6 modular components:

- **M1 Logger**: Structured logging library for agent operations
- **M2 Storage**: HTTP API service for log storage (SQLite backend)
- **M3 Compression**: Log compression and anomaly detection library (rule-based + optional LLM fallback)
- **M4 Memory**: HTTP API service for agent timeline storage (SQLite backend)
- **M5 Sandbox**: Secure code execution sandbox with timeout and resource limits
- **M6 Slack Bot**: Slack integration with slash commands for system control

## Features

- **Structured Logging**: JSON-based logging with metadata support
- **Log Compression**: Intelligent compression with anomaly detection
- **Agent Timeline**: Track agent execution history and snapshots
- **Code Execution**: Safe sandbox for running Python code with timeout
- **Slack Integration**: Real-time monitoring via slash commands
- **Critical Alerts**: Automatic Slack notifications for critical errors
- **3-Second Response**: All Slack commands respond within Slack's timeout

## Quick Start

### Prerequisites

- Python 3.14+
- pip
- Slack Workspace (for M6 bot)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd TRACELOG

# Install dependencies for each module
cd m2_storage && pip install -r requirements.txt
cd ../m3_compression && pip install -r requirements.txt
cd ../m4_memory && pip install -r requirements.txt
cd ../m5_sandbox && pip install -r requirements.txt
cd ../m6_slack && pip install -r requirements.txt
```

### Configuration

Each module has a `.env.example` file. Copy and configure:

```bash
# M2 Storage
cd m2_storage
cp .env.example .env
# Edit .env with your settings

# M3 Compression
cd ../m3_compression
cp .env.example .env
# Optional: Add GOOGLE_API_KEY for LLM fallback

# M4 Memory
cd ../m4_memory
cp .env.example .env
# Edit .env with your settings

# M5 Sandbox
cd ../m5_sandbox
cp .env.example .env
# Edit .env with your settings

# M6 Slack Bot
cd ../m6_slack
cp .env.example .env
# Edit .env with Slack credentials
```

### Running Services

Start services in order (separate terminals):

```bash
# Terminal 1: M2 Storage (port 8765)
cd m2_storage
python app.py

# Terminal 2: M4 Memory (port 8766)
cd m4_memory
python api.py

# Terminal 3: M5 Sandbox (port 8767)
cd m5_sandbox
python api.py

# Terminal 4: M6 Slack Bot
cd m6_slack
python app.py
```

### Slack Commands

Once the bot is running, use these commands in Slack:

- `/tracelog status` - Check health of all services
- `/tracelog run <command>` - Execute code in sandbox
- `/tracelog logs <session_id>` - Get compressed log summary
- `/tracelog memory <agent_id>` - View agent timeline
- `/tracelog alerts` - View recent critical alerts

## Testing

### Unit Tests

```bash
# Run tests for each module
cd m1_logger && python -m pytest tests/test_m1.py -v
cd ../m2_storage && python -m pytest tests/test_m2.py -v
cd ../m3_compression && python -m pytest tests/test_m3.py -v
cd ../m4_memory && python -m pytest tests/test_m4.py -v
cd ../m5_sandbox && python -m pytest tests/test_m5.py -v
cd ../m6_slack && python -m pytest tests/test_m6.py -v
```

### End-to-End Testing

See [END_TO_END_TEST.md](END_TO_END_TEST.md) for comprehensive testing guide.

## Module Documentation

Each module has its own specification:

- [M1 Logger](m1_logger/spec.md)
- [M2 Storage](m2_storage/spec.md)
- [M3 Compression](m3_compression/spec.md)
- [M4 Memory](m4_memory/spec.md)
- [M5 Sandbox](m5_sandbox/spec.md)
- [M6 Slack Bot](m6_slack/spec.md)

## API Endpoints

### M2 Storage (Port 8765)

- `GET /health` - Health check
- `POST /events` - Store log event
- `GET /events?session_id=<id>&limit=<n>` - Retrieve events
- `GET /sessions` - List all sessions

### M4 Memory (Port 8766)

- `GET /health` - Health check
- `GET /memory/agent/<agent_id>/timeline` - Get agent timeline
- `POST /memory/agent/<agent_id>/step` - Store execution step

### M5 Sandbox (Port 8767)

- `GET /health` - Health check
- `POST /sandbox/run` - Execute code in sandbox


## Performance

- All Slack commands respond within 3 seconds
- Log compression uses rule-based detection (fast)
- Optional LLM fallback for complex cases
- SQLite for fast local storage

## License

This project is licensed under the MIT License, which is free and permissive for personal, academic, and commercial use. See [LICENSE](LICENSE) for the full text.

## Support

For detailed setup and testing instructions, see [END_TO_END_TEST.md](END_TO_END_TEST.md).
