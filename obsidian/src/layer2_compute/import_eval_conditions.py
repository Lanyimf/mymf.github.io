"""
從 Excel 匯入 EE 評估細項條件到 SQLite eval_conditions 表
每個工作表有兩段：簡版（上）和詳版（下），只取詳版。
"""

import sqlite3
import pandas as pd
import os
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "land.db")
EXCEL    = os.path.join(BASE_DIR, "../../115年更新場址資料（套圖）.xlsx")

EE_SHEETS = {
    "EE-1 農牧用地-農作使用（中興範本）":     "EE-1",
    "EE-2 農牧用地－農舍使用(半里月新增":      "EE-2",
    "EE-3 農牧用地－農作產銷設施(半里月新增":  "EE-3",
    "EE-4 農牧用地-作畜牧設施(半里月新增":     "EE-4",
}

TYPE_MAP = {
    "硬性門檻": "hard",
    "重要指標": "weighted",
    "條件性指標": "weighted",
    "參考指標": "weighted",
    "一般指標": "weighted",
}


def find_second_header(df: pd.DataFrame) -> int:
    """找第二個標頭列（行號，其第一欄為 '#'，且 row index > 5）"""
    for i, row in df.iterrows():
        val = str(row.iloc[0]).strip()
        if i > 5 and val == "#":
            return i
    return None


def parse_detail_section(df: pd.DataFrame, eval_code: str, header_row: int) -> list[dict]:
    """解析詳版段落（header_row 之後），支援分類列（第一欄為文字、其餘為空）"""
    rows = []
    current_category = None

    for i in range(header_row + 1, len(df)):
        row = df.iloc[i]
        col0 = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
        col1 = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
        col2 = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else ""
        col3 = str(row.iloc[3]).strip() if pd.notna(row.iloc[3]) else ""

        # 略過空列或備注列
        if not col0 or col0 in ("nan",):
            continue
        if col0.startswith("【") or col0.startswith("\n"):
            continue

        # 分類列：col0 是文字（非數字），col1 為空
        try:
            no = int(float(col0))
        except (ValueError, TypeError):
            # 可能是分類標題列（如「第一類 法規資格條件」）
            if col1 == "" or col1 == "nan":
                current_category = re.sub(r"第[一二三四五]類\s*", "", col0).strip()
            continue

        name  = col1 if col1 not in ("", "nan") else None
        ctype = col2 if col2 not in ("", "nan") else None
        std   = col3 if col3 not in ("", "nan") else None

        if not name:
            continue

        rows.append({
            "eval_code":      eval_code,
            "condition_no":   no,
            "condition_name": name,
            "condition_type": TYPE_MAP.get(ctype, ctype),
            "threshold":      std,
            "note":           current_category,  # 所屬分類存入 note
        })

    return rows


def main():
    wb   = pd.read_excel(EXCEL, sheet_name=None)
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()

    # 先清掉舊資料（只清 EE 系列）
    cur.execute("DELETE FROM eval_conditions WHERE eval_code LIKE 'EE-%'")

    total = 0
    for sheet_name, eval_code in EE_SHEETS.items():
        if sheet_name not in wb:
            print(f"  ⚠️  找不到工作表：{sheet_name}")
            continue

        df = wb[sheet_name]
        header_row = find_second_header(df)
        if header_row is None:
            print(f"  ⚠️  {eval_code} 找不到詳版標頭，跳過")
            continue

        rows = parse_detail_section(df, eval_code, header_row)
        cur.executemany("""
            INSERT INTO eval_conditions
                (eval_code, condition_no, condition_name, condition_type, threshold, note)
            VALUES (:eval_code, :condition_no, :condition_name, :condition_type, :threshold, :note)
        """, rows)

        hard = sum(1 for r in rows if r["condition_type"] == "hard")
        soft = len(rows) - hard
        print(f"  ✓ {eval_code}：{len(rows)} 條（硬性 {hard} / 加權 {soft}）")
        total += len(rows)

    conn.commit()
    conn.close()
    print(f"\n完成！共匯入 {total} 筆詳版評估條件")


if __name__ == "__main__":
    main()
