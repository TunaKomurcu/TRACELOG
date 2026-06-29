# M5 - Secure Sandbox

## Amac
Shell komutlarini izole bir ortamda calistiran guvenlik katmanli subprocess sarmalayici.
Docker-in-Docker YOK. Python subprocess + whitelist + timeout + resource limits.

## Guvenlik Katmanlari
1. Whitelist: python pip pytest git cat ls grep (baskasi reject)
2. Resource limits: 30s timeout, 256MB RAM, 100 proses (Linux: rlimit, Windows: timeout)
3. Filesystem: sadece /tmp/sandbox_{uuid}/ dizinine yazilabilir
4. Network: NO_PROXY=* env degiskeni ile disari cikis engellenir

## Cikti Formati
sandbox_id, command, exit_code, stdout, stderr, duration_ms, resource_usage

## REST API (port 8767)
POST /sandbox/run - komutu calistir
GET /sandbox/{id} - sonucu getir
POST /webhook/sandbox-result - M6 webhook (forward)

## Kabul Kriterleri
1. os.system(rm -rf /) calismiyor
2. Sonsuz dongu 30s timeout ile kill ediliyor
3. /tmp disina dosya yazilamiyor
4. Basarili run M6 webhook una gidiyor
5. pytest tests/test_m5.py -v geciyor
