import pathlib
p=pathlib.Path(r"C:\Users\t.komurcu\sazabi\m4_memory\memory.py")
s=p.read_text("utf-8-sig")
# Find the start of summarise_with_llm and cut everything from there
marker="def summarise_with_llm"
idx=s.find(marker)
base=s[:idx]
new_fn=(
 "def summarise_with_llm(agent_id: str) -> dict:"+chr(10)+
 chr(32)*4+chr(34)*3+"Optional: pass step text through M3 pipeline for LLM summary."+chr(34)*3+chr(10)+
 chr(32)*4+"timeline = build_timeline(agent_id)"+chr(10)+
 chr(32)*4+"try:"+chr(10)+
 chr(32)*8+"import sys, pathlib as _pl"+chr(10)+
 chr(32)*8+"m3 = _pl.Path(__file__).parent.parent / "+chr(34)+"m3_compression"+chr(34)+chr(10)+
 chr(32)*8+"if str(m3) not in sys.path:"+chr(10)+
 chr(32)*12+"sys.path.insert(0, str(m3))"+chr(10)+
 chr(32)*8+"import pipeline as _m3"+chr(10)+
 chr(32)*8+"lines = ["+chr(10)+
 chr(32)*12+"f"+chr(34)+"Step {st["+chr(34)*2+"step_number"+chr(34)*2+"]}: {st["+chr(34)*2+"action_type"+chr(34)*2+"] or "+chr(34)*2+"?"+chr(34)*2+"} - {st["+chr(34)*2+"result_summary"+chr(34)*2+"] or "+chr(34)*2+""+chr(34)*2+"}"+chr(34)+chr(10)+
 chr(32)*12+"for st in timeline["+chr(34)+"steps"+chr(34)+"]"+chr(10)+
 chr(32)*8+"]"+chr(10)+
 chr(32)*8+"res = _m3.run(lines, session_id=agent_id)"+chr(10)+
 chr(32)*8+"timeline["+chr(34)+"llm_summary"+chr(34)+"] = res.summary"+chr(10)+
 chr(32)*4+"except Exception as e:"+chr(10)+
 chr(32)*8+"logger.warning(f"+chr(34)+"M3 summarise failed: {e}"+chr(34)+")"+chr(10)+
 chr(32)*8+"timeline["+chr(34)+"llm_summary"+chr(34)+"] = None"+chr(10)+
 chr(32)*4+"return timeline"+chr(10)+
)
p.write_text(base+new_fn,"utf-8")
print("memory.py rewritten, lines=",len((base+new_fn).splitlines()))