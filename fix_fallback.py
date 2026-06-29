import pathlib
p=pathlib.Path(r"C:\Users\t.komurcu\sazabi\m3_compression\fallback.py")
s=p.read_text("utf-8")
key="msg"
old = chr(32)*8+"summary_parts.append(f"+chr(34)+"En ciddi hata: {errors[-1][chr(39)]msg[chr(39)][:150]}."+chr(34)+")"
new = chr(32)*8+"last_msg = errors[-1]["+chr(34)+key+chr(34)+"][:150]"+chr(10)+chr(32)*8+"summary_parts.append(f"+chr(34)+"En ciddi hata: {last_msg}."+chr(34)+")"
print("found:", old in s)
s2 = s.replace(old, new, 1)
p.write_text(s2,"utf-8")
print("done")