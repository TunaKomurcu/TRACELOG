import pathlib
p=pathlib.Path(r"C:\Users\t.komurcu\sazabi\m4_memory\memory.py")
s=p.read_text("utf-8-sig")
idx=s.find("def summarise_with_llm")
p.write_text(s[:idx],"utf-8")
print("truncated at", idx)