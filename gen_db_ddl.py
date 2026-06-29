import pathlib
p=pathlib.Path(r"C:\Users\t.komurcu\sazabi\m4_memory\db.py")
s=p.read_text("utf-8")
sq=chr(39)
dq=chr(34)
# Replace the _CHECK placeholder with actual DDL strings
ddl=["_DDL_STEPS = (",
 dq+"CREATE TABLE IF NOT EXISTS agent_steps ("+dq+",",
 dq+"id INTEGER PRIMARY KEY AUTOINCREMENT, "+dq+",",
 dq+"agent_id TEXT NOT NULL, "+dq+",",
 dq+"step_number INTEGER NOT NULL, "+dq+",",
 "_CHECK,",
 dq+"action_detail TEXT, "+dq+",",
 dq+"result_summary TEXT, "+dq+",",
 dq+"timestamp TEXT NOT NULL)"+dq,
 ")",
 "",
 "_DDL_SNAPS = (",
 dq+"CREATE TABLE IF NOT EXISTS file_snapshots ("+dq+",",
 dq+"id INTEGER PRIMARY KEY AUTOINCREMENT, "+dq+",",
 dq+"step_id INTEGER REFERENCES agent_steps(id), "+dq+",",
 dq+"file_path TEXT NOT NULL, "+dq+",",
 dq+"git_hash TEXT, "+dq+",",
 dq+"diff_summary TEXT, "+dq+",",
 dq+"timestamp TEXT NOT NULL)"+dq,
 ")",
 "",
 "_DDL_IDX = [",
 dq+"CREATE INDEX IF NOT EXISTS idx_agent_steps ON agent_steps(agent_id, step_number)"+dq+",",
 dq+"CREATE INDEX IF NOT EXISTS idx_snapshots_step ON file_snapshots(step_id)"+dq+",",
 dq+"CREATE INDEX IF NOT EXISTS idx_snapshots_file ON file_snapshots(file_path)"+dq,
 "]",
]
s2=s+chr(10).join(ddl)+chr(10)
p.write_text(s2,"utf-8")
print("ddl appended, len=",len(s2))