import pathlib
p=pathlib.Path(r"C:\Users\t.komurcu\sazabi\m4_memory\memory.py")
s=p.read_text("utf-8")
bad=("lines = [f"+chr(34)+"Step {s[chr(39)]step_number[chr(39)]}: {s[chr(39)]action_type[chr(39)]} - {s[chr(39)]result_summary[chr(39)]}"+chr(34)+" for s in timeline["+chr(34)+"steps"+chr(34)+"]]")
good=("lines = [f"+chr(34)+"Step {step[chr(39)step_number chr(39)]}: {step[chr(39)action_type chr(39)]} - {step[chr(39)result_summary chr(39)]}"+chr(34)+" for step in timeline["+chr(34)+"steps"+chr(34)+"]]")
# Simple approach - just rewrite the summarise function cleanly
# Find the bad line and replace with safe version
bad2 = " lines = [f"+chr(34)+"Step {s[chr(39)]step_number[chr(39)]}: {s[chr(39)]action_type[chr(39)]} - {s[chr(39)]result_summary[chr(39)]}"+chr(34)+" for s in timeline["+chr(34)+"steps"+chr(34)+"]]"
good2 = chr(32)*8+"lines = []"+chr(10)+chr(32)*8+"for step in timeline["+chr(34)+"steps"+chr(34)+"]:"+chr(10)+chr(32)*12+"num=step["+chr(34)+"step_number"+chr(34)+"]"+chr(10)+chr(32)*12+"atype=step["+chr(34)+"action_type"+chr(34)+"] or "+chr(34)+"unknown"+chr(34)+chr(10)+chr(32)*12+"rsumm=step["+chr(34)+"result_summary"+chr(34)+"] or "+chr(34)+""+chr(34)+chr(10)+chr(32)*12+"lines.append(f"+chr(34)+"Step {num}: {atype} - {rsumm}"+chr(34)+")"
print("bad found:", bad2 in s)
s2=s.replace(bad2,good2,1)
p.write_text(s2,"utf-8")
print("fixed")