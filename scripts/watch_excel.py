"""
監聽 Excel 檔案變更，自動 diff 並更新資料庫
用法：python scripts/watch_excel.py
儲存 Excel 後會自動偵測，只更新有差異的列
"""
import time
import hashlib
import sqlite3
import lancedb
import pandas as pd
from pathlib import Path
from sentence_transformers import SentenceTransformer

BASE      = Path(__file__).parent.parent
DATA_DIR  = BASE / "src" / "layer1_data"
XLSX      = next(DATA_DIR.glob("*.xlsx"))
DB_PATH   = DATA_DIR / "parcels.db"
LANCE_DIR = DATA_DIR / "lancedb"
POLL_SEC  = 3   # 每幾秒掃描一次

_last_hash = None
_model = None


def file_hash(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def get_model():
    global _model
    if _model is None:
        print("  載入 embedding 模型...")
        _model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
    return _model


# ── Diff 工具 ─────────────────────────────────────────────────────
def diff_and_update_parcels(df_new: pd.DataFrame):
    conn = sqlite3.connect(DB_PATH)
    df_old = pd.read_sql("SELECT * FROM parcels", conn)
    conn.close()

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

    # 新增 / 修改的列（以場址編號為 key）
    old_ids = set(df_old["場址編號"].astype(str))
    new_ids = set(df_new["場址編號"].astype(str))

    added   = new_ids - old_ids
    removed = old_ids - new_ids
    updated = 0

    conn = sqlite3.connect(DB_PATH)

    # 刪除不再存在的列
    for rid in removed:
        conn.execute("DELETE FROM parcels WHERE 場址編號=?", (rid,))

    # 新增 / 更新
    for _, row in df_new.iterrows():
        vals = {db_col: row.get(xlsx_col) for xlsx_col, db_col in col_map.items()}
        conn.execute(
            f"INSERT OR REPLACE INTO parcels ({','.join(vals.keys())})"
            f" VALUES ({','.join(['?']*len(vals))})",
            list(vals.values())
        )
        if str(row.get("場址編號")) not in added:
            updated += 1

    conn.commit()
    conn.close()
    print(f"    parcels → +{len(added)} 新增  ~{updated} 更新  -{len(removed)} 刪除")


def diff_and_update_c_items(df_new: pd.DataFrame):
    conn = sqlite3.connect(DB_PATH)
    df_old = pd.read_sql("SELECT 用地類別, 項目名稱, 許可狀態 FROM c_items", conn)

    old_set = set(zip(df_old["用地類別"], df_old["項目名稱"], df_old["許可狀態"]))
    new_rows = []
    用地欄 = df_new.columns[0]
    for _, row in df_new.iterrows():
        用地 = str(row[用地欄]).strip()
        if not 用地 or 用地 == "nan":
            continue
        for col in df_new.columns[1:]:
            val = str(row[col]).strip() if not pd.isna(row[col]) else ""
            if val and val != "nan":
                new_rows.append((用地, str(col), val))

    new_set = set(new_rows)
    added   = new_set - old_set
    removed = old_set - new_set

    for r in removed:
        conn.execute("DELETE FROM c_items WHERE 用地類別=? AND 項目名稱=? AND 許可狀態=?", r)
    for r in added:
        conn.execute("INSERT INTO c_items (用地類別, 項目名稱, 許可狀態) VALUES (?,?,?)", r)

    conn.commit()
    conn.close()
    print(f"    c_items → +{len(added)} 新增  -{len(removed)} 刪除")


def refresh_laws():
    """EE/EP/ED 有變動時重新全量索引（通常改動少，全量即可）"""
    from scripts.import_excel import import_laws
    import_laws()


# ── 主監聽迴圈 ────────────────────────────────────────────────────
def watch():
    global _last_hash
    print(f"👁  監聽中：{XLSX.name}")
    print(f"   每 {POLL_SEC} 秒檢查一次，儲存 Excel 後自動更新資料庫")
    print("   Ctrl+C 停止\n")

    _last_hash = file_hash(XLSX)

    while True:
        time.sleep(POLL_SEC)
        try:
            current_hash = file_hash(XLSX)
        except PermissionError:
            # Excel 正在寫入中，跳過這輪
            continue

        if current_hash == _last_hash:
            continue

        _last_hash = current_hash
        print(f"[{pd.Timestamp.now().strftime('%H:%M:%S')}] 偵測到 Excel 變更，更新中...")

        try:
            xl = pd.ExcelFile(XLSX)
            diff_and_update_parcels(xl.parse("merged"))
            diff_and_update_c_items(xl.parse("總表"))
            print("  ✅ 資料庫已同步")
        except Exception as e:
            print(f"  ❌ 更新失敗：{e}")


if __name__ == "__main__":
    watch()
