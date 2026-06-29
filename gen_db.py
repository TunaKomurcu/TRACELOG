import pathlib
sq=chr(39)
nl=chr(10)
i4=" "*4
i8=" "*8
check="action_type TEXT CHECK(action_type IN ("+sq+"file_write"+sq+","+sq+"bash"+sq+","+sq+"api_call"+sq+","+sq+"decision"+sq+"))"
idx=("CREATE INDEX IF NOT EXISTS idx_agent_steps ON agent_steps(agent_id, step_number);"+nl+
 "CREATE INDEX IF NOT EXISTS idx_snapshots_step ON file_snapshots(step_id);"+nl+
 "CREATE INDEX IF NOT EXISTS idx_snapshots_file ON file_snapshots(file_path);"
)
lines=[
 chr(34)*3+"Sazabi M4 - memory.db database layer (SEPARATE from M2 log_db)."+chr(34)*3,
 "import sqlite3, os, pathlib",
 "from contextlib import contextmanager",
 "from typing import Optional, List, Dict, Any",
 "from datetime import datetime, timezone",
 "",
 "",
 "def utc_now() -> str:",
 i4+"now = datetime.now(timezone.utc)",
 i4+"return now.strftime("+chr(34)+"%Y-%m-%dT%H:%M:%S."+chr(34)+") + f"+chr(34)+"{now.microsecond // 1000:03d}Z"+chr(34),
 "",
 "",
 "def get_memory_db_path() -> str:",
 i4+chr(34)*3+"Always returns memory.db path - NEVER the M2 log DB."+chr(34)*3,
 i4+"default = "+chr(34)+"/data/memory.db"+chr(34)+" if os.name != "+chr(34)+"nt"+chr(34)+" else str(",
 i8+"pathlib.Path(os.environ.get("+chr(34)+"TEMP"+chr(34)+","+chr(34)+"C:/Temp"+chr(34)+")) / "+chr(34)+"sazabi"+chr(34)+" / "+chr(34)+"memory.db"+chr(34),
 i4+")",
 i4+"return os.getenv("+chr(34)+"MEMORY_DB_PATH"+chr(34)+", default)",
 "",
 "",
 "_DDL_STEPS = (",
 i4+chr(34)+"CREATE TABLE IF NOT EXISTS agent_steps ("+chr(34),
 i4+chr(34)+"id INTEGER PRIMARY KEY AUTOINCREMENT, "+chr(34),
 i4+chr(34)+"agent_id TEXT NOT NULL, "+chr(34),
 i4+chr(34)+"step_number INTEGER NOT NULL, "+chr(34),
 i4+check+",",
 i4+chr(34)+"action_detail TEXT, "+chr(34),
 i4+chr(34)+"result_summary TEXT, "+chr(34),
 i4+chr(34)+"timestamp TEXT NOT NULL)"+chr(34),
 ")",
 "",
 "_DDL_SNAPS = (",
 i4+chr(34)+"CREATE TABLE IF NOT EXISTS file_snapshots ("+chr(34),
 i4+chr(34)+"id INTEGER PRIMARY KEY AUTOINCREMENT, "+chr(34),
 i4+chr(34)+"step_id INTEGER REFERENCES agent_steps(id), "+chr(34),
 i4+chr(34)+"file_path TEXT NOT NULL, "+chr(34),
 i4+chr(34)+"git_hash TEXT, "+chr(34),
 i4+chr(34)+"diff_summary TEXT, "+chr(34),
 i4+chr(34)+"timestamp TEXT NOT NULL)"+chr(34),
 ")",
]
pathlib.Path(r"C:\Users\t.komurcu\sazabi\m4_memory\db.py").write_text(nl.join(lines)+nl,"utf-8")
print("db p1 ok")