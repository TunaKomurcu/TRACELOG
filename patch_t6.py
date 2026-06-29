import pathlib
p=pathlib.Path(r"C:\Users\t.komurcu\sazabi\m6_slack\tests\test_m6.py")
s=p.read_text("utf-8")
# Commands tests: replace bare "from app import X" with proper setup using get_test_app
# First import app at top of tests
old_import="import blocks, services"
new_import="import blocks, services, app as app_module"
s=s.replace(old_import,new_import,1)
# Patch: each test that does "from app import X" should call function directly
# Replace "from app import _cmd_status" + "_cmd_status(say)" pattern
fixes=[
 ("from app import _cmd_status"+chr(10)+" _cmd_status(say)",
 "from app import _cmd_status"+chr(10)+" _cmd_status(say)"),
]
# Simpler: just replace all "from app import _cmd_X" with direct calls
import re
s=s.replace("from app import _cmd_status"+chr(10),"from app import _cmd_status, get_test_app"+chr(10))
s=re.sub(r"from app import _cmd_(run|logs|memory|alerts)"+chr(10),"+chr(39)+chr(39)+",s)
p.write_text(s,"utf-8")
print("patched tests, chars=",len(s))