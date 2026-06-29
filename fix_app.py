import pathlib
i4=b"\x20\x20\x20\x20".decode()
p=pathlib.Path(r"C:\Users\t.komurcu\sazabi\m6_slack\app.py")
s=p.read_text("utf-8")
new_lines=[]
for line in s.splitlines():
if "timeline[chr(34)" in line and "error" in line:
ek=chr(34)+"error"+chr(34)
new_lines.append(chr(32)*8+"err_d = str(timeline.get("+ek+", "+chr(34)+"unknown"+chr(34)+"))[:100]")
new_lines.append(chr(32)*8+"say(blocks=blocks.error_block(f"+chr(34)+"Could not fetch memory: {err_d}"+chr(34)+"))")
print("fixed:", repr(line[:70]))
else:
new_lines.append(line)
p.write_text(chr(10).join(new_lines)+chr(10),"utf-8")
print("done")