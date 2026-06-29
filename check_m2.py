import pathlib
base=pathlib.Path(r"C:\Users\t.komurcu\sazabi\m2_storage")
for f in sorted(base.rglob("*")):
    if f.is_file():
        raw=f.read_bytes()
        bom=raw[:3]==b"\\xef\\xbb\\xbf"
        print(f"BOM={int(bom)} {f.relative_to(base)}")