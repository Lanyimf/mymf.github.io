"""
Phase 3 評估引擎資料庫遷移
新增：
  - parcels 補充欄位（Step 1~4 輸出）
  - evaluation_criteria  硬性/加權條件定義表
  - financial_params     財務試算參數表
  - evaluation_results   每筆完整評估結果（含明細）
"""
import sqlite3, json
from pathlib import Path

DB = Path(r'C:\Users\XH610G2\Documents\landevaluationBot\src\layer1_data\parcels.db')
conn = sqlite3.connect(DB)

# ══════════════════════════════════════════════════════
# 1. parcels 補充欄位
# ══════════════════════════════════════════════════════
parcel_new_cols = [
    # Step 1 硬性篩選輸出
    ("通過硬性篩選",    "INTEGER DEFAULT 1"),   # 1=通過 0=淘汰
    ("淘汰原因",        "TEXT"),                 # 不通過時說明
    # Step 2 加權評分輸出
    ("加權分數明細",    "TEXT"),                 # JSON: {條件: {分數,權重,加權後}}
    # Step 3 C項目比對輸出（已有 可行項目清單）
    ("可行項目數",      "INTEGER"),
    # Step 4 財務試算輸出
    ("財務試算結果",    "TEXT"),                 # JSON array of {用途,ROI,回收年限,NPV}
    ("最佳用途",        "TEXT"),
    ("最佳ROI",         "REAL"),
    ("最佳回收年限",    "REAL"),
]
added = []
for col, dtype in parcel_new_cols:
    try:
        conn.execute(f"ALTER TABLE parcels ADD COLUMN {col} {dtype}")
        added.append(col)
    except sqlite3.OperationalError:
        pass
print(f"parcels 新增欄位：{added}")

# ══════════════════════════════════════════════════════
# 2. evaluation_criteria — 評估條件定義
# ══════════════════════════════════════════════════════
conn.executescript("""
CREATE TABLE IF NOT EXISTS evaluation_criteria (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    條件代碼    TEXT UNIQUE NOT NULL,
    條件名稱    TEXT NOT NULL,
    類型        TEXT NOT NULL,      -- 'hard'硬性 | 'weighted'加權
    說明        TEXT,
    硬性門檻    TEXT,               -- 硬性條件的判斷式（e.g. "列管狀態 NOT IN ('公告為整治場址')"）
    權重        REAL DEFAULT 1.0,   -- 加權條件的權重（0~1，合計=1）
    滿分        REAL DEFAULT 10.0,  -- 該條件滿分
    資料來源欄位 TEXT,              -- 對應 parcels 的欄位名稱
    啟用        INTEGER DEFAULT 1
);
""")

# 預設硬性條件
hard_criteria = [
    ("H01", "非整治場址",       "hard", "整治場址不可申請開發",
     "列管狀態 NOT IN ('公告為整治場址')",   0, 0, "列管狀態"),
    ("H02", "非國土保育第一類", "hard", "國土保育地區第一類原則禁止開發",
     "國土功能分區 != '國土保育地區' OR 國土分區細類 != '第一類'", 0, 0, "國土功能分區"),
    ("H03", "林地重疊率<70%",   "hard", "林地重疊超過70%視為不可開發",
     "林地重疊率 < 70 OR 林地重疊率 IS NULL", 0, 0, "林地重疊率"),
    ("H04", "坐標資料完整",     "hard", "無坐標無法GIS定位",
     "座標x IS NOT NULL AND 座標y IS NOT NULL", 0, 0, "座標x"),
]

# 預設加權條件
weighted_criteria = [
    ("W01", "國土功能分區適宜性", "weighted", "分區越適合開發分數越高",
     None, 0.30, 10.0, "國土功能分區"),
    ("W02", "道路可及性",         "weighted", "距道路越近分數越高",
     None, 0.20, 10.0, "距道路距離_m"),
    ("W03", "台電饋線可及性",     "weighted", "距饋線越近分數越高（太陽能）",
     None, 0.20, 10.0, "距台電饋線距離_km"),
    ("W04", "林地重疊率",         "weighted", "重疊率越低分數越高",
     None, 0.15, 10.0, "林地重疊率"),
    ("W05", "整治進度",           "weighted", "整治進度越高表示可能解除管制",
     None, 0.10, 10.0, "改善整治進度百分比"),
    ("W06", "土地面積",           "weighted", "面積越大開發效益越高",
     None, 0.05, 10.0, "場址面積"),
]

for c in hard_criteria + weighted_criteria:
    conn.execute("""
        INSERT OR IGNORE INTO evaluation_criteria
        (條件代碼,條件名稱,類型,說明,硬性門檻,權重,滿分,資料來源欄位)
        VALUES (?,?,?,?,?,?,?,?)
    """, c)

# ══════════════════════════════════════════════════════
# 3. financial_params — 財務試算參數
# ══════════════════════════════════════════════════════
conn.executescript("""
CREATE TABLE IF NOT EXISTS financial_params (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    用途類型         TEXT UNIQUE NOT NULL,
    單位             TEXT,           -- 每公頃/每坪/每kW
    建設成本_萬元    REAL,           -- 建設成本（萬元/單位）
    年營收_萬元      REAL,           -- 年營收（萬元/單位）
    年維運成本_萬元  REAL,           -- 年維運成本
    使用年限_年      INTEGER,        -- 預估使用年限
    殘值率           REAL DEFAULT 0.1,
    折現率           REAL DEFAULT 0.05,
    備註             TEXT
);
""")

financial_defaults = [
    ("地面型太陽能",  "MW",  3000, 400, 50,  20, 0.05, 0.05, "1MW約1公頃，FIT約4元/度"),
    ("農業溫室",      "公頃", 800, 120, 30,  15, 0.10, 0.05, "含水電設備"),
    ("工業廠房",      "坪",   15,   3,  0.5, 30, 0.20, 0.05, "乙丁種建地適用"),
    ("倉儲物流",      "坪",   10,   2,  0.3, 30, 0.15, 0.05, "近道路優先"),
    ("農舍",          "坪",   12,   0,  0.2, 50, 0.30, 0.05, "自用為主，限農民申請"),
    ("再生能源（屋頂）","MW", 1500, 350, 30, 20, 0.05, 0.05, "屋頂型，低建設成本"),
]

for f in financial_defaults:
    conn.execute("""
        INSERT OR IGNORE INTO financial_params
        (用途類型,單位,建設成本_萬元,年營收_萬元,年維運成本_萬元,使用年限_年,殘值率,折現率,備註)
        VALUES (?,?,?,?,?,?,?,?,?)
    """, f)

# ══════════════════════════════════════════════════════
# 4. evaluation_results — 完整評估結果明細
# ══════════════════════════════════════════════════════
conn.executescript("""
CREATE TABLE IF NOT EXISTS evaluation_results (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    場址編號         TEXT NOT NULL,
    評估版本         TEXT DEFAULT '1.0',
    評估時間         TEXT DEFAULT (datetime('now')),

    -- Step 1
    通過硬性篩選     INTEGER,
    淘汰原因         TEXT,

    -- Step 2
    加權總分         REAL,
    加權明細_json    TEXT,   -- [{條件,得分,權重,加權後}, ...]

    -- Step 3
    可行項目_json    TEXT,   -- [{代碼,名稱,許可狀態,附條件}, ...]
    可行項目數        INTEGER,

    -- Step 4
    財務試算_json    TEXT,   -- [{用途,面積_公頃,建設成本,年營收,ROI,回收年限,NPV}, ...]
    最佳用途         TEXT,
    最佳ROI          REAL,
    最佳回收年限     REAL,
    最佳NPV          REAL,

    FOREIGN KEY (場址編號) REFERENCES parcels(場址編號)
);
CREATE INDEX IF NOT EXISTS idx_eval_landno ON evaluation_results(場址編號);
""")

conn.commit()

# 確認
print("\n=== 資料庫現有 tables ===")
for (t,) in conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall():
    n = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    cols = len(conn.execute(f"PRAGMA table_info({t})").fetchall())
    print(f"  {t:30s} {n:4d} 筆  {cols} 欄")

conn.close()
print("\n✅ Phase 3 資料庫遷移完成")
