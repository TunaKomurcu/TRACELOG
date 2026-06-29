import pathlib
p=pathlib.Path(r"C:\Users\t.komurcu\sazabi\m4_memory\memory.py")
s=p.read_text("utf-8")
bad=" import pipeline as m3_pipeline"+chr(10)+" lines = []"
good=" import pipeline as m3_pipeline"+chr(10)+" lines = []"
print("bad found:", bad in s)
p.write_text(s.replace(bad,good,1),"utf-8")
print("done")