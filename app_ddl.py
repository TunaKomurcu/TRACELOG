import pathlib
sq=chr(39); nl=chr(10)
vals=sq+"file_write"+sq+","+sq+"bash"+sq+","+sq+"api_call"+sq+","+sq+"decision"+sq
ddl_s=("CREATE TABLE IF NOT EXISTS agent_steps (id INTEGER PRIMARY KEY AUTOINCREMENT, "+
"agent_id TEXT NOT NULL, step_number INTEGER NOT NULL, "+
"action_type TEXT CHECK(action_type IN ("+vals+")), "+
"action_detail TEXT, result_summary TEXT, timestamp TEXT NOT NULL)")
ddl_f=("CREATE TABLE IF NOT EXISTS file_snapshots (id INTEGER PRIMARY KEY AUTOINCREMENT, "+
"step_id INTEGER REFERENCES agent_steps(id), file_path TEXT NOT NULL, "+
"git_hash TEXT, diff_summary TEXT, timestamp TEXT NOT NULL)")
idx1="CREATE INDEX IF NOT EXISTS idx_m4a ON agent_steps(agent_id)"
idx2="CREATE INDEX IF NOT EXISTS idx_m4b ON file_snapshots(step_id)"
idx3="CREATE INDEX IF NOT EXISTS idx_m4c ON file_snapshots(file_path)"
block=(nl+nl+nl+
"_DDL_STEPS = "+chr(34)+ddl_s+chr(34)+nl+
"_DDL_SNAPS = "+chr(34)+ddl_f+chr(34)+nl+
"_INDEXES = ["+chr(34)+idx1+chr(34)+", "+chr(34)+idx2+chr(34)+", "+chr(34)+idx3+chr(34)+"]"+nl
)
p=pathlib.Path(r"C:\Users\t.komurcu\sazabi\m4_memory\db.py")
p.write_text(p.read_text("utf-8")+block,"utf-8")
print("ddl ok")