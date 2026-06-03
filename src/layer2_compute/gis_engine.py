"""
Layer 2 — GIS 疊合引擎
負責：讀取 SHP、計算每筆地號的分區/重疊率/距離，寫回 DB
"""
import sqlite3
import geopandas as gpd
from shapely.ops import unary_union
from config import GIS, TARGET_CRS, DB_PATH, TAIPOWER_BUFFER_M


def _load(key: str) -> gpd.GeoDataFrame:
    path = GIS[key]
    if not path.exists():
        raise FileNotFoundError(f"圖層不存在：{path}")
    return gpd.read_file(path).to_crs(TARGET_CRS)


def _detect_col(gdf: gpd.GeoDataFrame, candidates: list[str]) -> str:
    for c in candidates:
        if c in gdf.columns:
            return c
    return gdf.columns[1]


def run_overlay() -> gpd.GeoDataFrame:
    """執行全部疊合，回傳含屬性的地號 GeoDataFrame"""
    print("📂 讀取圖層...")
    地號 = _load("地號圖層")
    國土分區 = _load("國土分區")
    林地 = _load("林地")
    道路 = _load("道路")

    分區欄位 = _detect_col(國土分區, ["分區名稱", "ZONE_NAME", "ZONING", "USE_ZONE"])
    地號欄位 = _detect_col(地號, ["地號", "LANDNO", "PARCEL_NO"])

    # 國土分區套疊
    print("🗺  套疊國土分區...")
    result = gpd.sjoin(
        地號,
        國土分區[["geometry", 分區欄位]].rename(columns={分區欄位: "zone"}),
        how="left", predicate="intersects"
    ).drop_duplicates(subset=地號欄位, keep="first")

    # 林地重疊率
    print("🌲 計算林地重疊率...")
    林地聯集 = unary_union(林地.geometry)
    result["forest_pct"] = (
        result.geometry.intersection(林地聯集).area / result.geometry.area * 100
    ).round(1).fillna(0)

    # 距道路距離
    print("🛣  計算距道路距離...")
    道路聯集 = unary_union(道路.geometry)
    result["road_dist_m"] = result.geometry.distance(道路聯集).round(0)

    # 台電設施距離（若圖層存在）
    if GIS["台電設施"].exists():
        print("⚡ 計算台電設施距離...")
        台電 = _load("台電設施")
        台電聯集 = unary_union(台電.geometry)
        result["taipower_dist_m"] = result.geometry.distance(台電聯集).round(0)
    else:
        result["taipower_dist_m"] = None
        print("  ⚠ 台電設施圖層不存在，略過")

    result["landno"] = result[地號欄位]
    return result[["landno", "zone", "forest_pct", "road_dist_m", "taipower_dist_m"]]


def save_to_db(result_gdf):
    """把疊合結果寫入 SQLite"""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM overlay_results")
    rows = result_gdf.to_dict("records")
    conn.executemany(
        "INSERT INTO overlay_results (landno, zone, forest_pct, road_dist_m, taipower_dist_m)"
        " VALUES (:landno, :zone, :forest_pct, :road_dist_m, :taipower_dist_m)",
        rows
    )
    conn.commit()
    conn.close()
    print(f"✅ 疊合結果已寫入 DB（{len(rows)} 筆）")


if __name__ == "__main__":
    df = run_overlay()
    save_to_db(df)
