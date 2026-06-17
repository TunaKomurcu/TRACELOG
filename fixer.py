import pathlib
p = pathlib.Path(r"C:\Users\t.komurcu\sazabi\m1_logger\tests\test_m1.py")
src = p.read_text("utf-8")
bad_line = chr(32)*8 + chr(34)+"hello"+chr(34)+" in combined or __import__("+chr(92)+chr(34)+"sys"+chr(92)+chr(34)+").exit("+chr(92)+chr(34)+"hello not found"+chr(92)+chr(34)+") # noqa"
good_line = chr(32)*8 + "assert "+chr(34)+"hello"+chr(34)+" in combined"
print("bad found:", bad_line in src)
src2 = src.replace(bad_line, good_line)
p.write_text(src2, "utf-8")
print("fixed")