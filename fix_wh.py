import pathlib
p=pathlib.Path(r"C:\Users\t.komurcu\sazabi\m5_sandbox\webhook.py")
s=p.read_text("utf-8")
# 1. Remove module-level M6_WEBHOOK_URL constant
s=s.replace("M6_WEBHOOK_URL = os.getenv("+chr(34)+"M6_WEBHOOK_URL"+chr(34)+", "+chr(34)+chr(34)+")","# M6_WEBHOOK_URL read per-call (supports env patching in tests)",1)
# 2. Make send_result read env at call time
s=s.replace(" target = url or M6_WEBHOOK_URL"," target = url or os.getenv("+chr(34)+"M6_WEBHOOK_URL"+chr(34)+", "+chr(34)+chr(34)+")",1)
p.write_text(s,"utf-8")
print("webhook.py patched")