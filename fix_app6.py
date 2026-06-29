import pathlib
p=pathlib.Path(r'C:\Users\t.komurcu\sazabi\m6_slack\app.py')
s=p.read_text('utf-8').replace('))); return','); return')
lines=s.splitlines()
fixed=[chr(32)*8+ln.strip() if len(ln)-len(ln.lstrip())==12 and '); return' in ln else ln for ln in lines]
p.write_text(chr(10).join(fixed)+chr(10),'utf-8')
print('done,lines=',len(fixed))