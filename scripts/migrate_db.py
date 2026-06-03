"""
資料庫遷移：新增 Layer 2 運算層所需欄位
"""
import sqlite3
from pathlib import Path

DB = Path(r'C:\Users\XH610G2\Documents\landevaluationBot\src\layer1_data\parcels.db')
conn = sqlite3.connect(DB)

# 新增欄位（已存在則跳過）
new_columns = [
    # GIS 套疊結果
    ("國土功能分區",       "TEXT"),
    ("國土分區細類",       "TEXT"),
    ("林地重疊率",         "REAL"),
    ("距道路距離_m",       "REAL"),
    ("距台電饋線距離_km",  "REAL"),
    # 使用者輸入
    ("開發項目類型",       "TEXT"),
    # Layer 2 運算輸出
    ("評估分數",           "REAL"),
    ("風險等級",           "TEXT"),
    ("可行項目清單",       "TEXT"),   # JSON array
    ("法規命中條文",       "TEXT"),   # JSON array
    ("評估時間",           "TEXT"),
]

added = []
for col, dtype in new_columns:
    try:
        conn.execute(f"ALTER TABLE parcels ADD COLUMN {col} {dtype}")
        added.append(col)
    except sqlite3.OperationalError:
        pass   # 欄位已存在

conn.commit()

# 確認結果
cols = conn.execute("PRAGMA table_info(parcels)").fetchall()
print(f"parcels 現有 {len(cols)} 個欄位")
print(f"新增欄位：{added if added else '（全部已存在）'}")
print()

# 用地代碼對照表（補充 c_items 缺少的類型）
ZONE_CODE_MAP = [
    ("EA", "EA 甲種建築用地"),
    ("EB", "EB 乙種建築用地"),
    ("EC", "EC 丙種建築用地"),
    ("ED", "ED 丁種建築用地"),
    ("EE", "EE 農牧用地"),
    ("EF", "EF 林業用地"),
    ("EG", "EG 交通用地"),
    ("EH", "EH 水利用地"),
    ("EI", "EI 遊憩用地"),
    ("EJ", "EJ 國土保安用地"),
    ("EK", "EK 墳墓用地"),
    ("EL", "EL 礦業用地"),
    ("EM", "EM 鹽業用地"),
    ("EN", "EN 殯葬用地"),
    ("EP", "EP 特定目的事業用地"),
    ("ZZ", "ZZ 暫未編定"),
]

# 建立用地代碼對照表
conn.execute("""
    CREATE TABLE IF NOT EXISTS zone_code_map (
        代碼   TEXT PRIMARY KEY,
        名稱   TEXT,
        說明   TEXT
    )
""")
for code, name in ZONE_CODE_MAP:
    conn.execute(
        "INSERT OR IGNORE INTO zone_code_map (代碼, 名稱) VALUES (?,?)",
        (code, name)
    )
conn.commit()
print("zone_code_map 對照表已建立")

# 列出完整欄位
print("\n=== 完整欄位清單 ===")
for c in conn.execute("PRAGMA table_info(parcels)").fetchall():
    print(f"  [{c[0]:02d}] {c[1]:30s} {c[2]}")

conn.close()
print("\n✅ 遷移完成")
