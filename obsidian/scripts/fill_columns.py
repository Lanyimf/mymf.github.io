"""
依現有資料填充 Layer 2 所需欄位：
  - 國土功能分區 / 國土分區細類  ← 從 非都使用分區 + 使用地 對應
  - 開發項目類型                ← 從 場址類別 對應
  - 評估分數 / 風險等級          ← scoring_model 初步計算
"""
import sys
import sqlite3
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.layer2_compute.scoring_model import score_parcel

DB = Path(r'C:\Users\XH610G2\Documents\landevaluationBot\src\layer1_data\parcels.db')

# ── 對照表 ─────────────────────────────────────────────────────────

# 非都使用分區 → (國土功能分區, 國土分區細類)
# 依「全國國土計畫」土地使用分區劃設原則對照
ZONE_MAP = {
    "特定農業區":     ("農業發展地區", "第一類"),
    "一般農業區":     ("農業發展地區", "第二類"),
    "鄉村區":         ("城鄉發展地區", "第二類"),
    "工業區":         ("城鄉發展地區", "第一類"),
    "森林區":         ("國土保育地區", "第一類"),
    "山坡地保育區":   ("國土保育地區", "第二類"),
    "河川區":         ("農業發展地區", "第四類"),
    "特定專用區":     ("城鄉發展地區", "第二類"),
    "鹽業用地":       ("農業發展地區", "第五類"),
    "礦業用地":       ("國土保育地區", "第二類"),
    "保護區":         ("國土保育地區", "第一類"),
}

# 使用地代碼 → (國土功能分區, 國土分區細類) (當非都使用分區為空時使用)
USAGE_ZONE_MAP = {
    "EE": ("農業發展地區", "第二類"),   # 農牧用地
    "EF": ("國土保育地區", "第一類"),   # 林業用地
    "EH": ("農業發展地區", "第四類"),   # 水利用地
    "EG": ("城鄉發展地區", "第一類"),   # 交通用地
    "ED": ("城鄉發展地區", "第一類"),   # 丁種建築用地
    "EC": ("城鄉發展地區", "第二類"),   # 丙種建築用地
    "EB": ("城鄉發展地區", "第二類"),   # 乙種建築用地
    "EA": ("城鄉發展地區", "第一類"),   # 甲種建築用地
    "EJ": ("國土保育地區", "第一類"),   # 國土保安用地
    "EI": ("城鄉發展地區", "第二類"),   # 遊憩用地
    "EN": ("城鄉發展地區", "第二類"),   # 殯葬用地
    "EP": ("城鄉發展地區", "第一類"),   # 特定目的事業用地
}

# 都市計畫分區 → 國土功能分區（當都市計畫且無非都編定時）
URBAN_ZONE_MAP = {
    "住宅區":         ("城鄉發展地區", "第一類"),
    "乙種工業區":     ("城鄉發展地區", "第一類"),
    "商業區":         ("城鄉發展地區", "第一類"),
    "農業區":         ("農業發展地區", "第二類"),
    "保護區":         ("國土保育地區", "第一類"),
    "工業區":         ("城鄉發展地區", "第一類"),
    "河川區":         ("農業發展地區", "第四類"),
    "主要計畫道路用地": ("城鄉發展地區", "第一類"),
}

# 場址類別 → 開發項目類型
SITE_TYPE_MAP = {
    "工廠":       "工業設施",
    "加油站":     "加油站/儲油設施",
    "農地":       "農業用地",
    "儲槽":       "儲油/儲液設施",
    "非法棄置場址": "廢棄物處理",
    "其他":       "其他",
}


def derive_zone(row: dict) -> tuple[str, str]:
    """推導 國土功能分區 和 國土分區細類"""
    非都 = str(row.get("非都使用分區") or "").strip()
    使用地 = str(row.get("使用地") or "").strip().upper()
    使用地類別 = str(row.get("使用地類別") or "").strip()

    # 優先：非都使用分區
    if 非都 and 非都 != "None":
        for key, val in ZONE_MAP.items():
            if key in 非都:
                return val

    # 次選：使用地代碼
    if 使用地 in USAGE_ZONE_MAP:
        return USAGE_ZONE_MAP[使用地]

    # 次選：都市計畫分區（從使用地類別判斷）
    for key, val in URBAN_ZONE_MAP.items():
        if key in 使用地類別:
            return val

    # 補充：有都市計畫區名稱但無其他編定 → 城鄉發展地區
    都計 = str(row.get("都市計畫區名稱") or "").strip()
    if 都計 and 都計 != "None":
        # 特定區計畫通常為工業/特殊用途
        if "特定區" in 都計 or "工業" in 都計:
            return ("城鄉發展地區", "第一類")
        return ("城鄉發展地區", "第二類")

    return ("待確認", "")


def run():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM parcels").fetchall()

    updated = 0
    zone_stats = {}

    for row in rows:
        d = dict(row)
        zone, sub = derive_zone(d)
        site_type = SITE_TYPE_MAP.get(d.get("場址類別") or "", "其他")

        # 用現有欄位做初步評分
        score_input = {
            "landno":          d.get("場址編號"),
            "zone":            zone,
            "forest_pct":      d.get("林地重疊率") or 0,
            "road_dist_m":     d.get("距道路距離_m") or 500,
            "taipower_dist_m": d.get("距台電饋線距離_km"),
        }
        result = score_parcel(score_input)

        conn.execute("""
            UPDATE parcels SET
                國土功能分區 = ?,
                國土分區細類 = ?,
                開發項目類型 = ?,
                評估分數 = ?,
                風險等級 = ?
            WHERE 場址編號 = ?
        """, (zone, sub, site_type, result.total,
              "低風險" if result.total >= 70 else "中等風險" if result.total >= 45 else "高風險",
              d["場址編號"]))
        updated += 1
        zone_stats[zone] = zone_stats.get(zone, 0) + 1

    conn.commit()
    conn.close()

    print(f"✅ 更新 {updated} 筆\n")
    print("國土功能分區分布：")
    for z, n in sorted(zone_stats.items(), key=lambda x: -x[1]):
        print(f"  {z:20s} {n} 筆")


if __name__ == "__main__":
    run()
