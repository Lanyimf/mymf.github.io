"""
從 115年更新場址資料（套圖）.xlsx 匯入三層資料：
  1. merged sheet      → SQLite parcels 表（342 筆場址）
  2. 總表 sheet        → SQLite c_items 表（C項目許可清單）
  3. EE/EP/ED sheets   → LanceDB law_chunks 表（評估指標法規）
"""
import sys
import sqlite3
import lancedb
import pandas as pd
from pathlib import Path
from sentence_transformers import SentenceTransformer

# ── 路徑設定 ──────────────────────────────────────────────────────
BASE      = Path(__file__).parent.parent
DATA_DIR  = BASE / "src" / "layer1_data"
XLSX      = next(DATA_DIR.glob("*.xlsx"))
DB_PATH   = DATA_DIR / "parcels.db"
LANCE_DIR = DATA_DIR / "lancedb"
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
# ─────────────────────────────────────────────────────────────────

print(f"來源檔案：{XLSX.name}")

# ════════════════════════════════════════════════════════════════
# Step 1：merged → SQLite parcels
# ════════════════════════════════════════════════════════════════
def import_parcels():
    df = pd.read_excel(XLSX, sheet_name="merged")
    print(f"\n[1/3] merged sheet：{len(df)} 筆 x {len(df.columns)} 欄")

    conn = sqlite3.connect(DB_PATH)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS parcels (
            場址編號    TEXT PRIMARY KEY,
            主管機關    TEXT,
            鄉鎮市區    TEXT,
            場址名稱    TEXT,
            場址面積    REAL,
            場址地址    TEXT,
            場址地號    TEXT,
            場址類別    TEXT,
            列管狀態    TEXT,
            列管日期    TEXT,
            整治階段    TEXT,
            程序代碼    TEXT,
            程序名稱    TEXT,
            座標x       REAL,
            座標y       REAL,
            使用地類別  TEXT,
            使用地      TEXT,
            非都使用分區 TEXT,
            非都分區代碼 TEXT,
            都市計畫區名稱 TEXT,
            都市計畫區代碼 TEXT,
            土壤污染物及濃度 TEXT,
            地下水污染物及濃度 TEXT,
            場址土地類型 TEXT,
            改善整治進度百分比 REAL,
            資料建立日期 TEXT
        );
    """)

    col_map = {
        "場址編號": "場址編號", "主管機關": "主管機關", "鄉鎮市區": "鄉鎮市區",
        "場址名稱": "場址名稱", "場址面積": "場址面積", "場址地址": "場址地址",
        "場址地號": "場址地號", "場址類別": "場址類別", "列管狀態": "列管狀態",
        "列管日期": "列管日期", "整治階段": "整治階段", "程序代碼": "程序代碼",
        "程序名稱": "程序名稱", "座標x": "座標x", "座標y": "座標y",
        "使用地類別": "使用地類別", "使用地": "使用地",
        "非都使用分區_2": "非都使用分區", "非都分區代碼": "非都分區代碼",
        "都市計畫區名稱": "都市計畫區名稱", "都市計畫區代碼": "都市計畫區代碼",
        "土壤污染物及濃度": "土壤污染物及濃度", "地下水污染物及濃度": "地下水污染物及濃度",
        "場址土地類型": "場址土地類型", "改善整治進度百分比": "改善整治進度百分比",
        "資料建立日期": "資料建立日期",
    }

    inserted = skipped = 0
    for _, row in df.iterrows():
        vals = {db_col: row.get(xlsx_col) for xlsx_col, db_col in col_map.items()}
        try:
            conn.execute(
                f"INSERT OR REPLACE INTO parcels ({','.join(vals.keys())})"
                f" VALUES ({','.join(['?']*len(vals))})",
                list(vals.values())
            )
            inserted += 1
        except Exception as e:
            skipped += 1
    conn.commit()
    conn.close()
    print(f"  ✅ 匯入 {inserted} 筆，跳過 {skipped} 筆")


# ════════════════════════════════════════════════════════════════
# Step 2：總表 → SQLite c_items
# ════════════════════════════════════════════════════════════════
def import_c_items():
    df = pd.read_excel(XLSX, sheet_name="總表")
    print(f"\n[2/3] 總表 sheet：{len(df)} 筆 x {len(df.columns)} 欄")

    conn = sqlite3.connect(DB_PATH)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS c_items (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            用地類別    TEXT,
            項目編號    TEXT,
            項目名稱    TEXT,
            許可狀態    TEXT
        );
        DELETE FROM c_items;
    """)

    # 總表：第一欄=用地類別，其他欄=各項目許可狀態（✓/△/X/空）
    # 轉成長表格式
    inserted = 0
    用地欄 = df.columns[0]
    for _, row in df.iterrows():
        用地 = row[用地欄]
        if pd.isna(用地):
            continue
        for col in df.columns[1:]:
            狀態 = str(row[col]).strip() if not pd.isna(row[col]) else ""
            if 狀態 and 狀態 not in ("nan", ""):
                conn.execute(
                    "INSERT INTO c_items (用地類別, 項目名稱, 許可狀態) VALUES (?,?,?)",
                    (str(用地), str(col), 狀態)
                )
                inserted += 1
    conn.commit()
    conn.close()
    print(f"  ✅ 匯入 {inserted} 筆 C 項目許可記錄")


# ════════════════════════════════════════════════════════════════
# Step 3：EE / EP / ED → LanceDB law_chunks
# ════════════════════════════════════════════════════════════════
def import_laws():
    sheets = {
        "EE":  "農牧用地評估指標",
        "EP":  "特定目的事業用地評估指標",
        "ED":  "工業發展用地評估指標",
    }
    print(f"\n[3/3] 法規評估指標 → LanceDB")
    print("  載入 embedding 模型...")
    model = SentenceTransformer(MODEL_NAME)

    records = []
    for sheet, desc in sheets.items():
        try:
            df = pd.read_excel(XLSX, sheet_name=sheet)
        except Exception:
            print(f"  ⚠ Sheet {sheet} 不存在，略過")
            continue

        # 找法規規範欄
        law_col = next((c for c in df.columns if "法規" in str(c)), None)
        cond_col = next((c for c in df.columns if "量化" in str(c) or "條件" in str(c)), None)
        item_col = df.columns[0]

        for _, row in df.iterrows():
            parts = []
            item = str(row.get(item_col, "")).strip()
            if item and item not in ("nan", ""):
                parts.append(f"項目：{item}")
            if cond_col and not pd.isna(row.get(cond_col)):
                parts.append(f"量化指標：{row[cond_col]}")
            if law_col and not pd.isna(row.get(law_col)):
                parts.append(f"法規依據：{row[law_col]}")
            text = "\n".join(parts).strip()
            if len(text) < 10:
                continue
            records.append({
                "source":   f"{sheet}-{desc}",
                "item":     item,
                "text":     text,
            })

    if not records:
        print("  ⚠ 沒有可索引的法規文字")
        return

    print(f"  向量化 {len(records)} 段文字...")
    texts = [r["text"] for r in records]
    vecs = model.encode(texts, show_progress_bar=True, batch_size=32).tolist()
    for r, v in zip(records, vecs):
        r["vector"] = v

    LANCE_DIR.mkdir(parents=True, exist_ok=True)
    db = lancedb.connect(str(LANCE_DIR))
    db.create_table("law_chunks", data=records, mode="overwrite")
    print(f"  ✅ LanceDB law_chunks：{len(records)} 筆")


# ════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import_parcels()
    import_c_items()
    import_laws()
    print("\n🎉 全部匯入完成")
    print(f"  SQLite : {DB_PATH}")
    print(f"  LanceDB: {LANCE_DIR}")
