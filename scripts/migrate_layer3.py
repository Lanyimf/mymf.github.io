"""
把 Phase 3 的 3 張表 + parcels 的 8 個評估欄位
從 layer1_data/parcels.db 搬到 layer3_output/evaluation.db
"""
import sqlite3, json, shutil
from pathlib import Path

LAYER1_DB = Path(r'C:\Users\XH610G2\Documents\landevaluationBot\src\layer1_data\parcels.db')
LAYER3_DIR = Path(r'C:\Users\XH610G2\Documents\landevaluationBot\src\layer3_output')
LAYER3_DB  = LAYER3_DIR / 'evaluation.db'

LAYER3_DIR.mkdir(parents=True, exist_ok=True)

# ── Step 1：建立 layer3 evaluation.db ─────────────────────────────
l3 = sqlite3.connect(LAYER3_DB)

l3.executescript("""
-- 硬性 / 加權評估條件定義
CREATE TABLE IF NOT EXISTS evaluation_criteria (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    條件代碼        TEXT UNIQUE NOT NULL,
    條件名稱        TEXT NOT NULL,
    類型            TEXT NOT NULL,
    說明            TEXT,
    硬性門檻        TEXT,
    權重            REAL DEFAULT 1.0,
    滿分            REAL DEFAULT 10.0,
    資料來源欄位    TEXT,
    啟用            INTEGER DEFAULT 1
);

-- 財務試算參數
CREATE TABLE IF NOT EXISTS financial_params (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    用途類型            TEXT UNIQUE NOT NULL,
    單位                TEXT,
    建設成本_萬元       REAL,
    年營收_萬元         REAL,
    年維運成本_萬元     REAL,
    使用年限_年         INTEGER,
    殘值率              REAL DEFAULT 0.1,
    折現率              REAL DEFAULT 0.05,
    備註                TEXT
);

-- 完整評估結果明細
CREATE TABLE IF NOT EXISTS evaluation_results (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    場址編號            TEXT NOT NULL,
    評估版本            TEXT DEFAULT '1.0',
    評估時間            TEXT DEFAULT (datetime('now')),
    通過硬性篩選        INTEGER,
    淘汰原因            TEXT,
    加權總分            REAL,
    加權明細_json       TEXT,
    可行項目_json       TEXT,
    可行項目數          INTEGER,
    財務試算_json       TEXT,
    最佳用途            TEXT,
    最佳ROI             REAL,
    最佳回收年限        REAL,
    最佳NPV             REAL
);
CREATE INDEX IF NOT EXISTS idx_eval_landno ON evaluation_results(場址編號);
""")

# ── Step 2：從 layer1 複製資料到 layer3 ──────────────────────────
l1 = sqlite3.connect(LAYER1_DB)

for table in ['evaluation_criteria', 'financial_params', 'evaluation_results']:
    rows = l1.execute(f"SELECT * FROM {table}").fetchall()
    if rows:
        cols = [c[1] for c in l1.execute(f"PRAGMA table_info({table})").fetchall()]
        ph = ','.join(['?'] * len(cols))
        l3.executemany(f"INSERT OR REPLACE INTO {table} VALUES ({ph})", rows)
        print(f"  複製 {table}: {len(rows)} 筆")
    else:
        print(f"  {table}: 空表，略過")

l3.commit()

# ── Step 3：從 parcels 移除 Phase 3 欄位 ─────────────────────────
phase3_cols = [
    '通過硬性篩選', '淘汰原因', '加權分數明細',
    '可行項目數', '財務試算結果', '最佳用途', '最佳ROI', '最佳回收年限'
]
removed = []
for col in phase3_cols:
    try:
        l1.execute(f"ALTER TABLE parcels DROP COLUMN {col}")
        removed.append(col)
    except sqlite3.OperationalError as e:
        print(f"  {col}: {e}")

l1.commit()
print(f"\n  parcels 移除欄位：{removed}")

# ── Step 4：從 layer1 刪除已搬走的 3 張表 ────────────────────────
for table in ['evaluation_criteria', 'financial_params', 'evaluation_results']:
    l1.execute(f"DROP TABLE IF EXISTS {table}")
l1.commit()
print("  layer1 已移除 evaluation_criteria / financial_params / evaluation_results")

l1.close()

# ── 確認結果 ─────────────────────────────────────────────────────
print("\n=== layer1_data/parcels.db ===")
l1 = sqlite3.connect(LAYER1_DB)
for (t,) in l1.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall():
    n = l1.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    c = len(l1.execute(f"PRAGMA table_info({t})").fetchall())
    print(f"  {t:30s} {n:4d} 筆  {c} 欄")
l1.close()

print("\n=== layer3_output/evaluation.db ===")
for (t,) in l3.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall():
    n = l3.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    c = len(l3.execute(f"PRAGMA table_info({t})").fetchall())
    print(f"  {t:30s} {n:4d} 筆  {c} 欄")
l3.close()

print("\n✅ 搬移完成")
