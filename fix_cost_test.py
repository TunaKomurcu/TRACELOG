import pathlib
p=pathlib.Path(r"C:\Users\t.komurcu\sazabi\m3_compression\tests\test_m3.py")
s=p.read_text("utf-8")
old=(chr(32)*8+"# 1M input @ $0.80 + 1M output @ $4.00 = $4.80"+chr(10)+chr(32)*8+"assert abs(ur.cost_usd - 4.80) < 0.001")
new=(chr(32)*8+"# 1M input @ $0.075 + 1M output @ $0.30 = $0.375 (Gemini 2.0 Flash Lite)"+chr(10)+chr(32)*8+"assert abs(ur.cost_usd - 0.375) < 0.001")
print("found:", old in s)
s2=s.replace(old,new,1)
p.write_text(s2,"utf-8")
print("done")