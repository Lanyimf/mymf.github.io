"""
Layer 1 — 地號資料庫（SQLite）
負責：建表、匯入 CSV、查詢單筆或批次地號
"""
import sqlite3
import csv
from pathlib import Path
from config import DB_PATH, C_LIST_PATH


def get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """建立資料表（首次執行）"""
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS parcels (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            landno      TEXT UNIQUE NOT NULL,   -- 地號
            county      TEXT,                   -- 縣市
            district    TEXT,                   -- 鄉鎮市區
            section     TEXT,                   -- 段名
            area_m2     REAL,                   -- 面積（平方公尺）
            owner       TEXT,                   -- 所有人（選填）
            note        TEXT
        );

        CREATE TABLE IF NOT EXISTS overlay_results (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            landno          TEXT NOT NULL,
            zone            TEXT,               -- 國土分區
            forest_pct      REAL,               -- 林地重疊率%
            road_dist_m     REAL,               -- 距道路距離(m)
            taipower_dist_m REAL,               -- 距台電設施距離(m)
            updated_at      TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS c_items (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            zone        TEXT NOT NULL,          -- 適用分區
            item_code   TEXT NOT NULL,          -- 項目代碼
            item_name   TEXT NOT NULL,          -- 項目名稱
            condition   TEXT                    -- 附帶條件
        );
    """)
    conn.commit()
    conn.close()
    print("✅ 資料庫初始化完成")


def import_parcels_csv(csv_path: Path):
    """匯入地號清單 CSV（欄位：地號, 縣市, 鄉鎮市區, 段名, 面積）"""
    conn = get_conn()
    inserted = 0
    with open(csv_path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO parcels (landno, county, district, section, area_m2)"
                    " VALUES (?, ?, ?, ?, ?)",
                    (row.get("地號"), row.get("縣市"), row.get("鄉鎮市區"),
                     row.get("段名"), row.get("面積"))
                )
                inserted += 1
            except Exception as e:
                print(f"  ⚠ 跳過 {row}: {e}")
    conn.commit()
    conn.close()
    print(f"✅ 匯入 {inserted} 筆地號")


def import_c_items_csv(csv_path: Path = C_LIST_PATH):
    """匯入 C 項目許可清單 CSV（欄位：分區, 項目代碼, 項目名稱, 附帶條件）"""
    conn = get_conn()
    with open(csv_path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            conn.execute(
                "INSERT INTO c_items (zone, item_code, item_name, condition)"
                " VALUES (?, ?, ?, ?)",
                (row.get("分區"), row.get("項目代碼"),
                 row.get("項目名稱"), row.get("附帶條件"))
            )
    conn.commit()
    conn.close()
    print("✅ C 項目清單匯入完成")


def get_parcel(landno: str) -> dict | None:
    conn = get_conn()
    row = conn.execute(
        "SELECT p.*, o.zone, o.forest_pct, o.road_dist_m, o.taipower_dist_m"
        " FROM parcels p"
        " LEFT JOIN overlay_results o ON p.landno = o.landno"
        " WHERE p.landno = ?", (landno,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_c_items_for_zone(zone: str) -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM c_items WHERE zone = ?", (zone,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


if __name__ == "__main__":
    init_db()
