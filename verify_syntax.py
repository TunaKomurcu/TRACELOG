import ast,pathlib
files=[r"C:\Users\t.komurcu\sazabi\m1_logger\forwarder.py",r"C:\Users\t.komurcu\sazabi\m2_storage\db.py",r"C:\Users\t.komurcu\sazabi\m2_storage\app.py",r"C:\Users\t.komurcu\sazabi\m2_storage\config.py"]
for f in files:
    try:
        ast.parse(pathlib.Path(f).read_text("utf-8"))
        print("OK:",f.split(chr(92))[-1])
    except SyntaxError as e:
        print("ERR:",f.split(chr(92))[-1],e)