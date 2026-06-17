import pathlib
p = pathlib.Path(r"C:\Users\t.komurcu\sazabi\m1_logger\tests\test_m1.py")
s = p.read_text("utf-8")
# build the regex pattern using chr() to avoid any escaping issues
bs = chr(92) # backslash
dq = chr(34) # double quote
pat = "ISO8601_PATTERN = re.compile(r" + dq + bs+"["+bs+"d{4}-"+bs+"d{2}-"+bs+"d{2}T"+bs+"d{2}:"+bs+"d{2}:"+bs+"d{2}"+bs+"."+bs+"d{3}Z"+bs+"]" + dq + ")"
print("pattern line:", pat)
lines = s.splitlines()
new_lines = []
for line in lines:
    if line.startswith("ISO8601_PATTERN"):
        new_lines.append(pat)
    else:
        new_lines.append(line)
p.write_text(chr(10).join(new_lines) + chr(10), "utf-8")
print("fixed")