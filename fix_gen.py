import pathlib
p=pathlib.Path(r"C:\Users\t.komurcu\sazabi\gen_t6.py")
s=p.read_text("utf-8")
s=s.replace("i8.decode()", "i8")
s=s.replace("i12.decode()", "i12")
# also fix the init lines
s=s.replace("i8=b"+chr(39)+chr(92)+"x20"+chr(39)+"*8", "i8="+chr(39)+" "*8+chr(39))
s=s.replace("i12=b"+chr(39)+chr(92)+"x20"+chr(39)+"*12", "i12="+chr(39)+" "*12+chr(39))
p.write_text(s,"utf-8")
print("fixed, bytes:", s.count("i8.decode()"), "remaining")