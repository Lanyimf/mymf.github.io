import sqlite3
from pathlib import Path

db = sqlite3.connect(r'C:\Users\XH610G2\Documents\landevaluationBot\src\layer3_output\evaluation.db')
db.executescript("""
CREATE TABLE IF NOT EXISTS revision_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp   TEXT DEFAULT (datetime('now','+8 hours')),
    sheet       TEXT NOT NULL,
    table_name  TEXT NOT NULL,
    action      TEXT NOT NULL,
    row_key     TEXT,
    field       TEXT,
    old_value   TEXT,
    new_value   TEXT,
    source      TEXT DEFAULT 'excel',
    note        TEXT
);
CREATE INDEX IF NOT EXISTS idx_rev_ts    ON revision_log(timestamp);
CREATE INDEX IF NOT EXISTS idx_rev_sheet ON revision_log(sheet);
""")
db.commit()
n = db.execute("SELECT COUNT(*) FROM revision_log").fetchone()[0]
print(f"revision_log 建立完成，目前 {n} 筆")

# 確認所有 tables
for (t,) in db.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall():
    n = db.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    print(f"  {t}: {n} 筆")
db.close()
