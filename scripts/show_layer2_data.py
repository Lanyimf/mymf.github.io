import sqlite3
import lancedb
import pandas as pd
from pathlib import Path

DB   = r'C:\Users\XH610G2\Documents\landevaluationBot\src\layer1_data\parcels.db'
LANCE = r'C:\Users\XH610G2\Documents\landevaluationBot\src\layer1_data\lancedb'

conn = sqlite3.connect(DB)

# 1. 使用地類別分布
print("=== 使用地類別分布（parcels）===")
rows = conn.execute("""
    SELECT 使用地類別, 非都使用分區, COUNT(*) as n
    FROM parcels
    GROUP BY 使用地類別, 非都使用分區
    ORDER BY n DESC
    LIMIT 20
""").fetchall()
for r in rows:
    print(f"  {str(r[0]):12s} | {str(r[1]):15s} | {r[2]} 筆")

# 2. 場址類別分布
print("\n=== 場址類別分布 ===")
rows = conn.execute("""
    SELECT 場址類別, COUNT(*) as n FROM parcels
    GROUP BY 場址類別 ORDER BY n DESC
""").fetchall()
for r in rows:
    print(f"  {str(r[0]):20s} {r[1]} 筆")

# 3. c_items 用地類別
print("\n=== C項目用地類別（c_items）===")
rows = conn.execute("""
    SELECT 用地類別, COUNT(*) as n,
           SUM(CASE WHEN 許可狀態='✓' THEN 1 ELSE 0 END) as 許可,
           SUM(CASE WHEN 許可狀態='△' THEN 1 ELSE 0 END) as 附條件
    FROM c_items GROUP BY 用地類別
""").fetchall()
for r in rows:
    print(f"  {str(r[0]):20s} 共{r[1]}項  ✓{r[2]}  △{r[3]}")

# 4. LanceDB law_chunks
print("\n=== LanceDB law_chunks 來源 ===")
db = lancedb.connect(LANCE)
tbl = db.open_table("law_chunks")
df = tbl.to_pandas()
print(f"  總計 {len(df)} 筆")
for src, grp in df.groupby("source"):
    print(f"  [{src}] {len(grp)} 筆")
    for _, row in grp.head(2).iterrows():
        print(f"    • {row['text'][:80]}")

conn.close()
