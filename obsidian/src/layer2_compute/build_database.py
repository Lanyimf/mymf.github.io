"""
Layer 2 資料庫建立腳本
建立兩個資料庫：
1. land.db (SQLite) - 土地條件主資料庫
2. regulations/ (LanceDB) - 法規向量資料庫（結構預留）
"""

import sqlite3
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "land.db")

# ── 用地類別對照 (1-51) ──────────────────────────────────────
USE_ITEMS = {
    1:  "農作使用(含牧草)",
    2:  "農舍",
    3:  "農作產銷設施",
    4:  "畜牧設施",
    5:  "水產養殖設施",
    6:  "林業使用(造林、苗圃)",
    7:  "林業設施",
    8:  "休閒農業設施",
    9:  "農產品集散批發運銷設施",
    10: "綠能設施",
    11: "住宅",
    12: "鄉村教育設施",
    13: "行政及文教設施",
    14: "衛生及福利設施",
    15: "安全設施",
    16: "宗教建築",
    17: "日用品零售及服務設施",
    18: "遊憩設施",
    19: "兒童課後照顧服務中心",
    20: "工業設施(廠房等)",
    21: "工業社區",
    22: "無公害性小型工業設施",
    23: "廢棄物回收貯存清除處理設施",
    24: "依產業創新條例核定之用地使用",
    25: "公用事業設施",
    26: "交通設施",
    27: "交通設施(貨運停車場)",
    28: "電信微波收發站(含基地臺)",
    29: "再生能源相關設施",
    30: "再生能源相關設施(限太陽光電)",
    31: "水源保護及水土保持設施",
    32: "採取土石",
    33: "水岸遊憩設施",
    34: "戶外遊憩設施",
    35: "戶外廣告物設施",
    36: "溫泉井及溫泉儲槽",
    37: "農村再生設施",
    38: "自然保育設施",
    39: "動物保護相關設施",
    40: "按現況或水利計畫使用",
    41: "按現況或交通計畫使用",
    42: "按特定目的事業計畫使用",
    43: "其他經河川或排水管理機關核准",
    44: "滯洪設施",
    45: "殯葬設施",
    46: "寵物骨灰灑葬區",
    47: "私設通路",
    48: "臨時堆置收納營建剩餘土石方",
    49: "水庫河川湖泊淤泥資源再生利用臨時處理設施",
    50: "露營相關設施",
    51: "無動力飛行運動相關設施",
}

# ── 用地類型基本資料 ──────────────────────────────────────────
LAND_TYPES = [
    ("EE", "農牧用地"),
    ("EB", "乙種建築用地"),
    ("ED", "丁種建築用地"),
    ("EH", "水利用地"),
    ("EG", "交通用地"),
    ("EP", "特定目的事業用地"),
    ("EN", "殯葬用地"),
]

# ── 對應矩陣：用地類型 → {使用項目編號: 評估代號} ────────────────
# None 表示 "—" 不可申請
MATRIX = {
    "EE": {
        1: "EE-1",  2: "EE-2",  3: "EE-3",  4: "EE-4",  5: "EE-5",
        6: "EE-6",  8: "EE-7",  10: "EE-8", 25: "EE-9", 29: "EE-10",
        31: "EE-11", 32: "EE-12", 35: "EE-13", 36: "EE-14", 37: "EE-15",
        38: "EE-16", 39: "EE-17", 47: "EE-18", 48: "EE-19", 49: "EE-20",
        50: "EE-21", 51: "EE-22",
    },
    "EB": {
        3: "EB-1",  4: "EB-2",  5: "EB-3",  9: "EB-4",  11: "EB-5",
        12: "EB-6", 13: "EB-7", 14: "EB-8", 15: "EB-9", 16: "EB-10",
        17: "EB-11", 18: "EB-12", 19: "EB-13", 22: "EB-14", 25: "EB-15",
        26: "EB-16", 29: "EB-17", 31: "EB-18", 36: "EB-19", 39: "EB-20",
    },
    "ED": {
        20: "ED-1", 21: "ED-2", 23: "ED-3", 24: "ED-4", 27: "ED-5",
        29: "ED-6", 48: "ED-7", 49: "ED-8",
    },
    "EH": {
        29: "EH-1", 32: "EH-2", 33: "EH-3", 34: "EH-4", 36: "EH-5",
        37: "EH-6", 40: "EH-7", 43: "EH-8", 44: "EH-9",
    },
    "EG": {
        25: "EG-1", 26: "EG-2", 29: "EG-3", 34: "EG-4", 37: "EG-5",
        41: "EG-6",
    },
    "EP": {
        42: "EP-1",
    },
    "EN": {
        6: "EN-1",  7: "EN-2",  28: "EN-3", 30: "EN-4", 45: "EN-5",
        46: "EN-6",
    },
}


def build_sqlite():
    print(f"建立 SQLite 資料庫：{DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # 表一：用地類型
    cur.execute("""
        CREATE TABLE IF NOT EXISTS land_types (
            type_code   TEXT PRIMARY KEY,
            type_name   TEXT NOT NULL
        )
    """)

    # 表二：使用項目
    cur.execute("""
        CREATE TABLE IF NOT EXISTS use_items (
            item_no     INTEGER PRIMARY KEY,
            item_name   TEXT NOT NULL
        )
    """)

    # 表三：對應矩陣（總表）
    cur.execute("""
        CREATE TABLE IF NOT EXISTS use_matrix (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            type_code       TEXT NOT NULL,
            item_no         INTEGER NOT NULL,
            eval_code       TEXT NOT NULL,
            FOREIGN KEY (type_code) REFERENCES land_types(type_code),
            FOREIGN KEY (item_no)   REFERENCES use_items(item_no),
            UNIQUE (type_code, item_no)
        )
    """)

    # 表四：評估細項條件（每個 eval_code 的詳細條件，之後從 Excel 匯入）
    cur.execute("""
        CREATE TABLE IF NOT EXISTS eval_conditions (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            eval_code       TEXT NOT NULL,
            condition_no    INTEGER NOT NULL,
            condition_name  TEXT,
            condition_type  TEXT,   -- 'hard' | 'weighted'
            threshold       TEXT,
            weight          REAL,
            data_source     TEXT,
            note            TEXT,
            enabled         INTEGER DEFAULT 1
        )
    """)

    # ── 寫入資料 ──────────────────────────────────────────────
    cur.executemany("INSERT OR REPLACE INTO land_types VALUES (?,?)", LAND_TYPES)

    cur.executemany(
        "INSERT OR REPLACE INTO use_items VALUES (?,?)",
        USE_ITEMS.items()
    )

    matrix_rows = []
    for type_code, mapping in MATRIX.items():
        for item_no, eval_code in mapping.items():
            matrix_rows.append((type_code, item_no, eval_code))

    cur.executemany(
        "INSERT OR IGNORE INTO use_matrix (type_code, item_no, eval_code) VALUES (?,?,?)",
        matrix_rows
    )

    conn.commit()
    conn.close()

    total = sum(len(v) for v in MATRIX.values())
    print(f"  ✓ land_types：{len(LAND_TYPES)} 筆")
    print(f"  ✓ use_items：{len(USE_ITEMS)} 筆")
    print(f"  ✓ use_matrix：{total} 筆對應關係")
    print(f"  ✓ eval_conditions：結構建立完成（待 Excel 匯入）")


def build_lancedb_structure():
    """建立 LanceDB 資料夾結構（實際向量寫入等法規 PDF 備齊後執行）"""
    lance_dir = os.path.join(BASE_DIR, "regulations_lancedb")
    os.makedirs(lance_dir, exist_ok=True)

    readme = {
        "description": "LanceDB 法規向量資料庫",
        "tables": [
            {
                "name": "regulations",
                "columns": [
                    "id          - 條文唯一ID",
                    "law_name    - 法規名稱",
                    "article_no  - 條號（如 第12條第1項）",
                    "eval_code   - 對應評估代號（如 EE-1）",
                    "type_code   - 用地類型代碼",
                    "content     - 條文內容",
                    "vector      - 向量（384維，all-MiniLM-L6-v2）",
                    "source_file - 原始 PDF 檔名",
                ]
            }
        ],
        "status": "結構預留，待法規 PDF 備齊後執行 build_regulations.py 匯入"
    }

    with open(os.path.join(lance_dir, "README.json"), "w", encoding="utf-8") as f:
        json.dump(readme, f, ensure_ascii=False, indent=2)

    print(f"  ✓ LanceDB 結構預留：{lance_dir}")


if __name__ == "__main__":
    build_sqlite()
    print()
    build_lancedb_structure()
    print()
    print("完成！下一步：執行 import_eval_conditions.py 從 Excel 匯入各評估代號細項條件")
