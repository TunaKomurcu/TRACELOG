import pathlib
base=pathlib.Path(r"C:\Users\t.komurcu\sazabi\m3_compression\tests\fixtures\sample_logs")
lines=[]
for i in range(1000):
    mm=str(i//60).zfill(2); ss=str(i%60).zfill(2)
    ts=f"[2025-01-15T14:{mm}:{ss}.000Z]"
    if i%100==0:
        lines.append(f"{ts} [stderr] DEBUG: progress {i}/1000")
    elif i%50==0:
        lines.append(f"{ts} [stderr] WARNING: high latency {i*3}ms")
    elif i%75==0:
        lines.append(f"{ts} [stderr] ERROR: timeout on attempt {i}")
    elif i%30==0:
        lines.append(f"{ts} [stdout] GET /health 200 OK 2ms")
    else:
        lines.append(f"{ts} [stdout] processed request {i} status=200")
(base/"large_1000_lines.log").write_text(chr(10).join(lines)+chr(10),"utf-8")
print("large_1000_lines.log ok,",len(lines),"lines")