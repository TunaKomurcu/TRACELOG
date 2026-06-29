import pathlib
p=pathlib.Path(r"C:\Users\t.komurcu\sazabi\m2_storage\requirements.txt")
raw=p.read_bytes()
if raw[:3]==b"\xef\xbb\xbf":
 p.write_bytes(raw[3:])
 print("BOM stripped")
else:
 print("clean")