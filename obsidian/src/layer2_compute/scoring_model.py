"""
Layer 2 — 適宜性評分模型
輸入：單筆地號的疊合屬性
輸出：0~100 分 + 風險標記清單
"""
from dataclasses import dataclass, field
from config import TAIPOWER_BUFFER_M, ROAD_BUFFER_M


@dataclass
class ScoreResult:
    landno:      str
    total:       float           # 0~100
    zone_score:  float
    access_score: float
    constraint_score: float
    risks:       list[str] = field(default_factory=list)
    flags:       list[str] = field(default_factory=list)   # 高風險標記


# 分區基礎分數（可依實際需求調整）
ZONE_BASE = {
    "農業發展地區第一類": 20,
    "農業發展地區第二類": 40,
    "農業發展地區第三類": 55,
    "農業發展地區第四類": 65,
    "農業發展地區第五類": 70,
    "城鄉發展地區第一類": 85,
    "城鄉發展地區第二類": 75,
    "國土保育地區第一類": 10,
    "國土保育地區第二類": 25,
    "海洋資源地區":       15,
}
DEFAULT_ZONE_SCORE = 50


def score_parcel(parcel: dict) -> ScoreResult:
    """
    parcel 需含欄位：
      landno, zone, forest_pct, road_dist_m, taipower_dist_m
    """
    landno   = parcel.get("landno", "?")
    zone     = parcel.get("zone") or "未知"
    forest   = float(parcel.get("forest_pct") or 0)
    road_d   = float(parcel.get("road_dist_m") or 9999)
    tp_d     = parcel.get("taipower_dist_m")
    tp_d     = float(tp_d) if tp_d is not None else None

    risks, flags = [], []

    # 1. 分區評分
    zone_score = ZONE_BASE.get(zone, DEFAULT_ZONE_SCORE)

    # 2. 林地扣分
    if forest > 50:
        zone_score = max(zone_score - 30, 5)
        flags.append(f"⚠ 林地重疊率 {forest}%（超過 50%）")
    elif forest > 20:
        zone_score = max(zone_score - 15, 5)
        risks.append(f"林地重疊率 {forest}%")

    # 3. 道路可及性評分（0~20）
    if road_d <= 50:
        access_score = 20
    elif road_d <= 200:
        access_score = 15
    elif road_d <= 500:
        access_score = 10
    elif road_d <= 1000:
        access_score = 5
    else:
        access_score = 0
        risks.append(f"距道路 {road_d:.0f}m，開發成本高")

    # 4. 台電設施限制評分（0~10）
    if tp_d is None:
        constraint_score = 5
    elif tp_d < TAIPOWER_BUFFER_M:
        constraint_score = 0
        flags.append(f"⚠ 台電設施緩衝區內（{tp_d:.0f}m < {TAIPOWER_BUFFER_M}m）")
    elif tp_d < 200:
        constraint_score = 3
        risks.append(f"接近台電設施（{tp_d:.0f}m）")
    else:
        constraint_score = 10

    total = round(zone_score * 0.7 + access_score + constraint_score, 1)

    # 國土保育地區直接標記
    if "國土保育" in zone:
        flags.append("🔴 國土保育地區，開發許可極嚴格")
    if "農業發展地區第一類" in zone:
        flags.append("🔴 優良農地，原則禁止變更")

    return ScoreResult(
        landno=landno,
        total=min(total, 100),
        zone_score=zone_score,
        access_score=access_score,
        constraint_score=constraint_score,
        risks=risks,
        flags=flags,
    )
