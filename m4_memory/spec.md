# M4 - Agentic Memory

## Amac
Ajan adim gecmisini ve dosya degisikliklerini ayri bir SQLite DB
(memory.db) icinde izler. M2 log_db ile hicbir sekilde karistirilmaz.

## DB: /data/memory.db (M2 den AYRI)

## Schema
agent_steps(id, agent_id, step_number, action_type, action_detail, result_summary, timestamp)
file_snapshots(id, step_id -> agent_steps.id, file_path, git_hash, diff_summary, timestamp)

## action_type degerleri
file_write | bash | api_call | decision

## REST API
GET /memory/agent/{agent_id}/timeline
 -> JSON: {agent_id, steps:[{step, action, result, snapshots:[...]}], summary}

## M3 Entegrasyonu
Timeline ozetleme isteginde M3 pipeline.run() cagrilir (opsiyonel).

## Dosyalar
m4_memory/
 spec.md
 db.py - memory.db CRUD
 git_tracker.py - git diff --stat, hash
 memory.py - record_step, record_snapshot
 api.py - FastAPI endpoints
 .env.example
 tests/
 __init__.py
 test_m4.py

## Kabul Kriterleri
1. 20 adimlik agent run kaydedilip timeline geri cekilebiliyor
2. Ayni dosya 3 kez degisince 3 ayri snapshot var
3. M2 DB etkilenmiyor (ayri dosya testi)
4. Timeline endpoint Slack JSON formatinda donuyor
5. pytest tests/test_m4.py geciyor
