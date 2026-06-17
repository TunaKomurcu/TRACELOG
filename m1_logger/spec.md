# M1 - Naked Logger

## Amac
SDK gerektirmeden herhangi bir komutu wrap eden process wrapper.

## Kullanim
 python logger.py -- <komut> [args...]

## Gereksinimler

### 1. Process Yonetimi
- subprocess.Popen(stdout=PIPE, stderr=PIPE)
- Her iki stream icin ayri okuma thread ac
- Alt prosesin exit code unu propagate et

### 2. Log Satir Formati
 [2025-01-15T14:23:01.234Z] [stdout] mesaj

### 3. Log Dosyasi
- Yol: TEMP/sazabi/session_<uuid4>.log
- Session metadata basa ve sona yazilir

### 4. Signal Handling
- SIGINT/SIGTERM yakalanir, alt prosese iletilir

## Kabul Kriterleri
1. Cikti hem terminalde gorunur hem dosyada olur
2. Her satirda ISO 8601 timestamp bulunur
3. Exit code dogru propagate edilir
4. pytest tests/test_m1.py -v tum testler gecmeli

## Bagimliliklar
Yalnizca Python stdlib
