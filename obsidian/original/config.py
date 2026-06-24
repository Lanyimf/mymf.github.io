"""
全域設定：所有路徑、參數集中在這裡改
"""
from pathlib import Path

BASE = Path(__file__).parent

# ── Layer 1：資料層路徑 ────────────────────────────────────────────
DATA = BASE / "data"

GIS = {
    "地號圖層":   DATA / "地號圖層"  / "landno.shp",
    "國土分區":   DATA / "國土分區"  / "natl_land.shp",
    "林地":       DATA / "林地"      / "forest.shp",
    "道路":       DATA / "道路"      / "road.shp",
    "台電設施":   DATA / "台電設施"  / "taipower.shp",
}

DB_PATH          = BASE / "src" / "layer1_data" / "parcels.db"
EVAL_DB_PATH     = BASE / "src" / "layer3_output" / "evaluation.db"
LANCEDB_PATH     = BASE / "src" / "layer1_data" / "lancedb"
C_LIST_PATH      = DATA / "C項目許可清單" / "c_items.csv"
LAW_DOCS_DIR     = DATA / "法規條文"
OUTPUT_DIR       = DATA / "輸出結果"

# ── Layer 2：運算參數 ──────────────────────────────────────────────
TARGET_CRS          = "EPSG:3826"   # TWD97 TM2
TAIPOWER_BUFFER_M   = 50            # 台電設施緩衝距離（公尺）
ROAD_BUFFER_M       = 30            # 道路緩衝距離

# ── Layer 3：輸出設定 ──────────────────────────────────────────────
REPORT_TEMPLATE     = BASE / "src" / "layer3_output" / "templates" / "report.md"
CLAUDE_MODEL        = "claude-sonnet-4-6"
