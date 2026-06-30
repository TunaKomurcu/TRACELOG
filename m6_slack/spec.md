# M6 - Slack Bot (Sazabi Control Panel)

## Amac
Slack uzerinden M1-M5 sistemlerine erisim saglar.
Proaktif alert gonderir, komut calistirir, durum raporu verir.

## Komutlar

### /sazabi status
- httpx ile M2_URL/health, M4_URL/health, M5_URL/health cagirilir
- Her biri icin ayri try/except kullanilir
- Block Kit formatinda sonuc gosterilir:
  - :white_check_mark: M2 Storage: calisiyor (X events)
  - :warning: M4 Memory: erisilimiyor
  - :white_check_mark: M5 Sandbox: calisiyor

## Ortam Degiskenleri
SLACK_BOT_TOKEN
SLACK_SIGNING_SECRET
SLACK_ALERT_CHANNEL
M2_URL
M4_URL
M5_URL
HTTP_TIMEOUT
SLACK_PORT
