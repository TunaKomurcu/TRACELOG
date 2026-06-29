import pathlib
p=pathlib.Path(r"C:\Users\t.komurcu\sazabi\m5_sandbox\tests\test_m5.py")
s=p.read_text("utf-8")
dq=chr(34); sq=chr(39)
# Fix exit_code test: add quotes around the -c argument
old1=("result = runner.run_sandboxed("+dq+"python -c import sys; sys.exit(42)"+dq+")")
new1=("result = runner.run_sandboxed("+dq+"python -c "+chr(39)+"import sys; sys.exit(42)"+chr(39)+dq+")")
print("exit_code fix found:", old1 in s)
s=s.replace(old1,new1,1)
# Fix stderr test: add quotes around the -c argument
old2=("result = runner.run_sandboxed("+dq+"python -c import sys; sys.stderr.write("+sq+"err"+sq+")"+dq+")")
new2=("result = runner.run_sandboxed("+dq+"python -c "+sq+"import sys; sys.stderr.write(chr(101)+chr(114)+chr(114))"+sq+dq+")")
print("stderr fix found:", old2 in s)
s=s.replace(old2,new2,1)
# Fix timeout test: add quotes around while True: pass
old3=("result = runner.run_sandboxed("+dq+"python -c while True: pass"+dq+")")
new3=("result = runner.run_sandboxed("+dq+"python -c "+sq+"while True: pass"+sq+dq+")")
print("timeout fix found:", old3 in s)
s=s.replace(old3,new3,1)
# Fix os_system test in security enforcement
old4=("result = runner.run_sandboxed("+dq+"python -c import os; os.system("+sq+"ls"+sq+")"+dq+")")
new4=("result = runner.run_sandboxed("+dq+"python -c "+sq+"import os; os.system(chr(108)s)"+sq+dq+")")
p.write_text(s,"utf-8")
print("tests patched")