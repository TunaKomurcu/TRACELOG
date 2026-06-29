import pathlib
nl=chr(10); sq=chr(39); dq=chr(34)
vals=sq+"file_write"+sq+","+sq+"bash"+sq+","+sq+"api_call"+sq+","+sq+"decision"+sq
ddl_steps=("CREATE TABLE IF NOT EXISTS agent_steps ("
 "id INTEGER PRIMARY KEY AUTOINCREMENT, "
 "agent_id TEXT NOT NULL, "
 "step_number INTEGER NOT NULL, "
 "action_type TEXT CHECK(action_type IN ("+vals+")), "
 "action_detail TEXT, result_summary TEXT, timestamp TEXT NOT NULL)")
ddl_snaps=("CREATE TABLE IF NOT EXISTS file_snapshots ("
 "id INTEGER PRIMARY KEY AUTOINCREMENT, "
 "step_id INTEGER REFERENCES agent_steps(id), "
 "file_path TEXT NOT NULL, "
 "git_hash TEXT, diff_summary TEXT, timestamp TEXT NOT NULL)")
idx1="CREATE INDEX IF NOT EXISTS idx_m4_agent ON agent_steps(agent_id)"
idx2="CREATE INDEX IF NOT EXISTS idx_m4_snap_step ON file_snapshots(step_id)"
idx3="CREATE INDEX IF NOT EXISTS idx_m4_snap_file ON file_snapshots(file_path)"
lines=[
dq*3+"Sazabi M4 - memory.db layer (SEPARATE from M2 sazabi.db)."+dq*3,
"import sqlite3, os, pathlib",
"from contextlib import contextmanager",
"from typing import Optional, List, Dict, Any",
"from datetime import datetime, timezone",
"","",
"_DDL_STEPS = "+dq+ddl_steps+dq,
"_DDL_SNAPS = "+dq+ddl_snaps+dq,
"_INDEXES = ["+dq+idx1+dq+", "+dq+idx2+dq+", "+dq+idx3+dq+"]",
"","",
"def utc_now() -> str:",
dq+" "*4+"now = datetime.now(timezone.utc)"+dq,
" return now.strftime("+dq+"%Y-%m-%dT%H:%M:%S."+dq+") + f"+dq+"{now.microsecond // 1000:03d}Z"+dq,
"","",
"def get_memory_db_path() -> str:",
" if os.name != "+dq+"nt"+dq+":",
" return os.getenv("+dq+"MEMORY_DB_PATH"+dq+", "+dq+"/data/memory.db"+dq+")",
" d = str(pathlib.Path(os.environ.get("+dq+"TEMP"+dq+","+dq+"C:/Temp"+dq+")) / "+dq+"sazabi"+dq+" / "+dq+"memory.db"+dq+")",
" return os.getenv("+dq+"MEMORY_DB_PATH"+dq+", d)",
]
pathlib.Path(r"C:\Users\t.komurcu\sazabi\m4_memory\db.py").write_text(nl.join(lines)+nl,"utf-8")
print("header ok")