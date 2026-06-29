import pathlib
sq=chr(39); nl=chr(10); dq=chr(34)
check_vals=sq+"file_write"+sq+","+sq+"bash"+sq+","+sq+"api_call"+sq+","+sq+"decision"+sq
check_col=dq+"action_type TEXT CHECK(action_type IN ("+check_vals+"))"+dq
idx_sql=("CREATE INDEX IF NOT EXISTS idx_agent_steps ON agent_steps(agent_id, step_number)"+nl+
"CREATE INDEX IF NOT EXISTS idx_snapshots_step ON file_snapshots(step_id)"+nl+
"CREATE INDEX IF NOT EXISTS idx_snapshots_file ON file_snapshots(file_path)"
)
content=(
 dq*3+"Sazabi M4 - memory.db layer (SEPARATE from M2)."+dq*3+nl+
 "import sqlite3, os, pathlib"+nl+
 "from contextlib import contextmanager"+nl+
 "from typing import Optional, List, Dict, Any"+nl+
 "from datetime import datetime, timezone"+nl+nl+nl+
 "def utc_now() -> str:"+nl+
 " now = datetime.now(timezone.utc)"+nl+
 " return now.strftime("+dq+"%Y-%m-%dT%H:%M:%S."+dq+") + f"+dq+"{now.microsecond // 1000:03d}Z"+dq+nl+nl+nl+
 "def get_memory_db_path() -> str:"+nl+
 " if os.name != "+dq+"nt"+dq+":"+nl+
 " return os.getenv("+dq+"MEMORY_DB_PATH"+dq+", "+dq+"/data/memory.db"+dq+")"+nl+
 " default = str(pathlib.Path(os.environ.get("+dq+"TEMP"+dq+","+dq+"C:/Temp"+dq+")) / "+dq+"sazabi"+dq+" / "+dq+"memory.db"+dq+")"+nl+
 " return os.getenv("+dq+"MEMORY_DB_PATH"+dq+", default)"+nl+nl+nl+
 "_DDL_STEPS = ("+nl+
 " "+dq+"CREATE TABLE IF NOT EXISTS agent_steps ("+dq+nl+
 " "+dq+"id INTEGER PRIMARY KEY AUTOINCREMENT, "+dq+nl+
 " "+dq+"agent_id TEXT NOT NULL, "+dq+nl+
 " "+dq+"step_number INTEGER NOT NULL, "+dq+nl+
 " "+check_col+", "+nl+
 " "+dq+"action_detail TEXT, "+dq+nl+
 " "+dq+"result_summary TEXT, "+dq+nl+
 " "+dq+"timestamp TEXT NOT NULL)"+dq+nl+
 ")"+nl+nl+
 "_DDL_SNAPS = ("+nl+
 " "+dq+"CREATE TABLE IF NOT EXISTS file_snapshots ("+dq+nl+
 " "+dq+"id INTEGER PRIMARY KEY AUTOINCREMENT, "+dq+nl+
 " "+dq+"step_id INTEGER REFERENCES agent_steps(id), "+dq+nl+
 " "+dq+"file_path TEXT NOT NULL, "+dq+nl+
 " "+dq+"git_hash TEXT, "+dq+nl+
 " "+dq+"diff_summary TEXT, "+dq+nl+
 " "+dq+"timestamp TEXT NOT NULL)"+dq+nl+
 ")"+nl+nl+
 "_DDL_IDX = "+dq*3+idx_sql+dq*3+nl+
)
pathlib.Path(r"C:\Users\t.komurcu\sazabi\m4_memory\db.py").write_text(content,"utf-8")
print("header ok, len=",len(content))