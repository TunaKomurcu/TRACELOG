# M2 - Storage Service

FastAPI + SQLite log ingestion servisi.

## Endpoints
- POST /events - log satiri yaz
- GET /events?session_id=X&limit=100&offset=0
- GET /sessions - son 50 session

## Schema
log_events(id, session_id, timestamp, stream, content, source)

## Ortam Degiskenleri
DB_PATH, SERVICE_HOST, SERVICE_PORT, LOG_LEVEL

## Kabul Kriterleri
1. Servis ayaga kalkiyor
2. M1 log uretince SQLite a yaziliyor
3. 10k write + p95 okuma 50ms alti
4. Restart ta veri kaybolmuyor
5. pytest tests/test_m2.py yesil
