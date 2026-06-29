# M3 - LLM Compression

## Amac
SQLiteden cekilen ham log satirlarini Google Gemini gemini-2.0-flash-lite ile ozetler.
API key yoksa kural bazli fallback devreye girer.

## Pipeline
```
raw logs -> pre_filter -> Gemini API -> structured JSON output
 -> (fallback) rule-based summary
```

## Cikti Formati
```json
{
 "summary": "Ne oldu (2-3 cumle)",
 "errors": [{"line": 42, "msg": "...", "severity": "critical|warning"}],
 "anomalies": ["..."],
 "root_cause_hint": "..."
}
```

## Kurallar
- Model: gemini-2.0-flash-lite
- Batch max: 50 KB
- Rate limit: 10 API call/dakika
- Retry: exponential backoff, max 3 deneme
- Pre-filter: tekrar eden satirlar ve DEBUG level kaldirilir

## Dosyalar
```
m3_compression/
 spec.md
 filter.py - kural bazli on-filtre
 compressor.py - Gemini API istemcisi, rate limit, retry, maliyet takibi
 fallback.py - API key yoksa ozet
 pipeline.py - ana orkestrasyon
 .env.example
 tests/
 __init__.py
 test_m3.py
 fixtures/sample_logs/
 normal_run.log
 python_traceback.log
 large_1000_lines.log
```

## Kabul Kriterleri
1. 1000 satir log - anlamli ozet
2. Python traceback -> root_cause_hint dogru
3. API key yoksa graceful fallback
4. Token maliyeti loglanmis
5. pytest tests/test_m3.py -v gecmeli
