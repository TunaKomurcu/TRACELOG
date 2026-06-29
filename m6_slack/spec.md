# M6 - Slack Bot Control Panel

## Amac
Tum sistemin (M1-M5) kontrol merkezi. Slack slash komutlari ile
servis saglik kontrolu, log ozeti, sandbox calistirma, agent timeline.

## Slash Komutlar
/sazabi status - M1-M5 health check ozeti
/sazabi logs [session_id] - M3 compressed log ozeti
/sazabi run [komut] - M5 sandbox calistirma
/sazabi memory [agent_id] - M4 agent timeline
/sazabi alerts - Son 1 saatin M3 anomalileri

## Guvenlik
SLACK_BOT_TOKEN ve SLACK_SIGNING_SECRET .env dosyasinda.

## Kritik Uyarı
M3 severity=critical tespit edince Slack kanalina otomatik ping.

## Kabul Kriterleri
1. /sazabi status - M1-M5 health gorunuyor
2. /sazabi run python -c print(1+1) -> Slack 2 gorunuyor
3. M3 critical -> otomatik Slack mesaji
4. Tum komutlar 3sn alti response
5. pytest tests/test_m6.py geciyor
