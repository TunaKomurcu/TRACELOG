import pathlib
files=[r"C:\Users\t.komurcu\sazabi\m1_logger\forwarder.py",r"C:\Users\t.komurcu\sazabi\m2_storage\db.py",r"C:\Users\t.komurcu\sazabi\m2_storage\app.py",r"C:\Users\t.komurcu\sazabi\m2_storage\config.py"]
for f in files:
    raw=pathlib.Path(f).read_bytes()
    if raw[:3]==b"\xef\xbb\xbf":
        pathlib.Path(f).write_bytes(raw[3:])
        print("BOM removed:",f)
    else:
        print("OK:",f)