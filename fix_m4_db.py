import pathlib
p=pathlib.Path(r"C:\Users\t.komurcu\sazabi\m4_memory\db.py")
s=p.read_text("utf-8")
bad_def=("def utc_now() -> str:"+chr(10)+chr(34)+" now = datetime.now(timezone.utc)"+chr(34)+chr(10)+
 " return now.strftime("+chr(34)+chr(34)+"%Y-%m-%dT%H:%M:%S."+chr(34)+chr(34)+") + f"+chr(34)+chr(34)+"{now.microsecond // 1000:03d}Z"+chr(34)+chr(34))
good_def=("def utc_now() -> str:"+chr(10)+
 " now = datetime.now(timezone.utc)"+chr(10)+
 " return now.strftime("+chr(34)+"%Y-%m-%dT%H:%M:%S."+chr(34)+") + f"+chr(34)+"{now.microsecond // 1000:03d}Z"+chr(34))
print("bad found:", bad_def in s)
s2=s.replace(bad_def,good_def,1)
p.write_text(s2,"utf-8")
print("done")