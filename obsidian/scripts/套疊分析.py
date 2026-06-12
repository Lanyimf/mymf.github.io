"""
國土功能分區套疊分析腳本
用法：python scripts/套疊分析.py
"""

import sys
import geopandas as gpd
import pandas as pd
from pathlib import Path
from shapely.ops import unary_union

# ── 設定資料路徑（改這裡）────────────────────────────────────────────
BASE = Path("C:/Users/XH610G2/Documents/landevaluationBot")

地號圖層路徑  = BASE / "data" / "地號圖層"  / "landno.shp"
國土分區路徑  = BASE / "data" / "國土分區"  / "natl_land.shp"
林地路徑      = BASE / "data" / "林地"      / "forest.shp"
道路路徑      = BASE / "data" / "道路"      / "road.shp"
輸出CSV路徑   = BASE / "data" / "輸出結果"  / "地號屬性結果.csv"
# ─────────────────────────────────────────────────────────────────────

TARGET_CRS = "EPSG:3826"   # TWD97 TM2


def 確認檔案存在():
    缺少 = []
    for 名稱, 路徑 in [("地號圖層", 地號圖層路徑),
                       ("國土分區", 國土分區路徑),
                       ("林地",     林地路徑),
                       ("道路",     道路路徑)]:
        if not 路徑.exists():
            缺少.append(f"  ✗ {名稱}: {路徑}")
    if 缺少:
        print("❌ 以下 SHP 檔案不存在：")
        print("\n".join(缺少))
        print("\n請先下載並放置到對應資料夾，再執行本腳本。")
        sys.exit(1)


def 計算林地重疊率(地號gdf: gpd.GeoDataFrame, 林地gdf: gpd.GeoDataFrame) -> pd.Series:
    """向量化計算每筆地號與林地的面積重疊率（%）"""
    print("  建立林地空間索引...")
    林地聯集 = unary_union(林地gdf.geometry)
    print("  計算每筆地號重疊面積...")
    重疊面積 = 地號gdf.geometry.intersection(林地聯集).area
    自身面積 = 地號gdf.geometry.area
    比率 = (重疊面積 / 自身面積 * 100).round(1).fillna(0)
    return 比率


def main():
    確認檔案存在()

    # ── 讀取並統一投影 ───────────────────────────────────────────────
    print("📂 讀取圖層中...")
    地號   = gpd.read_file(地號圖層路徑).to_crs(TARGET_CRS)
    國土分區 = gpd.read_file(國土分區路徑).to_crs(TARGET_CRS)
    林地   = gpd.read_file(林地路徑).to_crs(TARGET_CRS)
    道路   = gpd.read_file(道路路徑).to_crs(TARGET_CRS)
    print(f"  地號筆數：{len(地號)}")

    # ── 偵測欄位名稱（不同來源欄位名稱可能不同）────────────────────
    分區欄位候選 = ["分區名稱", "ZONE_NAME", "ZONING", "USE_ZONE", "名稱"]
    地號欄位候選 = ["地號", "LANDNO", "PARCEL_NO", "LAND_NO"]

    分區欄位 = next((c for c in 分區欄位候選 if c in 國土分區.columns), 國土分區.columns[1])
    地號欄位 = next((c for c in 地號欄位候選 if c in 地號.columns), 地號.columns[0])
    print(f"  偵測到分區欄位：{分區欄位}，地號欄位：{地號欄位}")

    # ── 套疊國土功能分區 ─────────────────────────────────────────────
    print("🗺  套疊國土功能分區...")
    套疊結果 = gpd.sjoin(
        地號,
        國土分區[["geometry", 分區欄位]].rename(columns={分區欄位: "國土分區"}),
        how="left",
        predicate="intersects"
    ).drop_duplicates(subset=地號欄位, keep="first")   # 跨分區取第一筆

    # ── 林地重疊率 ───────────────────────────────────────────────────
    print("🌲 計算林地重疊率...")
    套疊結果 = 套疊結果.copy()
    套疊結果["林地重疊率%"] = 計算林地重疊率(套疊結果, 林地)

    # ── 距道路距離 ───────────────────────────────────────────────────
    print("🛣  計算距道路距離...")
    道路聯集 = unary_union(道路.geometry)
    套疊結果["距道路距離(m)"] = 套疊結果.geometry.distance(道路聯集).round(0).astype(int)

    # ── 輸出 ─────────────────────────────────────────────────────────
    輸出欄位 = [地號欄位, "國土分區", "林地重疊率%", "距道路距離(m)"]
    輸出欄位 = [c for c in 輸出欄位 if c in 套疊結果.columns]
    輸出CSV路徑.parent.mkdir(parents=True, exist_ok=True)
    套疊結果[輸出欄位].to_csv(輸出CSV路徑, index=False, encoding="utf-8-sig")

    print(f"\n✅ 完成！共處理 {len(套疊結果)} 筆地號")
    print(f"   結果已儲存：{輸出CSV路徑}")
    print(套疊結果[輸出欄位].head(5).to_string(index=False))


if __name__ == "__main__":
    main()
