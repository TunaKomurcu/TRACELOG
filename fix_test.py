import pathlib
p = pathlib.Path(r"C:\Users\t.komurcu\sazabi\m1_logger\tests\test_m1.py")
s = p.read_text("utf-8")
old = chr(32)*8 + "log_lines = [l for l in content.splitlines() if l.strip()]"
new = chr(32)*8 + "log_lines = [l for l in content.splitlines() if l.strip() and not l.startswith("+chr(39)+"[META:"+ chr(39)+")]"
print("found:", old in s)
s2 = s.replace(old, new)
p.write_text(s2, "utf-8")
print("done")