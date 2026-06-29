import pathlib
nl=chr(10)
i4=b"\x20\x20\x20\x20".decode()
i8=b"\x20\x20\x20\x20\x20\x20\x20\x20".decode()
i12=b"\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20\x20".decode()
dq=chr(34)
sq=chr(39)
p=pathlib.Path(r"C:\Users\t.komurcu\sazabi\m5_sandbox\tests\test_m5.py")
s=p.read_text("utf-8")
lines=[
"",
"",
"class TestWhitelist:",
i4+"def test_allowed_python(self):",
i8+"security.validate_command(["+dq+"python"+dq+", "+dq+"-c"+dq+", "+dq+"pass"+dq+"]) # must not raise",
i4+"def test_allowed_pytest(self):",
i8+"security.validate_command(["+dq+"pytest"+dq+", "+dq+"--version"+dq+"]) # must not raise",
i4+"def test_reject_rm(self):",
i8+"with pytest.raises(security.SecurityError, match="+dq+"not allowed"+dq+"):",
i12+"security.validate_command(["+dq+"rm"+dq+", "+dq+"-rf"+dq+", "+dq+"/"+dq+"])",
i4+"def test_reject_curl(self):",
i8+"with pytest.raises(security.SecurityError):",
i12+"security.validate_command(["+dq+"curl"+dq+", "+dq+"http://evil.com"+dq+"])",
i4+"def test_reject_bash(self):",
i8+"with pytest.raises(security.SecurityError):",
i12+"security.validate_command(["+dq+"bash"+dq+", "+dq+"-c"+dq+", "+dq+"echo hi"+dq+"])",
i4+"def test_reject_empty(self):",
i8+"with pytest.raises(security.SecurityError):",
i12+"security.validate_command([])",
i4+"def test_reject_os_system(self):",
i8+"with pytest.raises(security.SecurityError, match="+dq+"Dangerous"+dq+"):",
i12+"security.validate_command(["+dq+"python"+dq+", "+dq+"-c"+dq+", "+dq+"import os; os.system("+sq+"ls"+sq+")"+dq+"])",
]
p.write_text(s+nl.join(lines)+nl,"utf-8")
print("p2 ok")