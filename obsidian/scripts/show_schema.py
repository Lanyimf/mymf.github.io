import sqlite3
conn = sqlite3.connect(r'C:\Users\XH610G2\Documents\landevaluationBot\src\layer1_data\parcels.db')

tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
for (t,) in tables:
    cols = conn.execute(f"PRAGMA table_info({t})").fetchall()
    count = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    print(f"=== {t} ({count} 筆) ===")
    for c in cols:
        print(f"  [{c[0]:02d}] {c[1]:35s} {c[2]}")
    # 顯示第一筆範例
    row = conn.execute(f"SELECT * FROM {t} LIMIT 1").fetchone()
    if row:
        print("  -- 範例資料 --")
        for col, val in zip([c[1] for c in cols], row):
            if val is not None and str(val).strip():
                print(f"       {col}: {str(val)[:60]}")
    print()
conn.close()
