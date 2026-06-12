"""
重建 LanceDB 法規向量資料庫
主要來源：原始法規資料/ 25 份 PDF
補充來源：EE 總表法規欄、eval_conditions threshold
"""

import os, re, json, sqlite3, sys

import pandas as pd
import pdfplumber
import lancedb
from sentence_transformers import SentenceTransformer

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
LAND_DIR   = os.path.join(BASE_DIR, "../..")
DB_PATH    = os.path.join(BASE_DIR, "land.db")
LANCE_DIR  = os.path.join(BASE_DIR, "regulations_lancedb")
EXCEL      = os.path.join(LAND_DIR, "場址資料（套圖） .xlsx")
PDF_DIR    = os.path.join(LAND_DIR, "原始法規資料")
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"


def clean(text):
    if not text or str(text).strip() in ("nan", ""):
        return ""
    return re.sub(r"\s+", " ", str(text).replace("<br>", "\n")).strip()


def chunk_by_article(text, law_name, max_chars=600):
    """依「第X條」切段，每段不超過 max_chars"""
    chunks = []
    articles = re.split(r"(?=第\s*\d+\s*條)", text)
    for art in articles:
        art = art.strip()
        if len(art) < 10:
            continue
        art_no_m = re.match(r"第\s*(\d+)\s*條", art)
        art_no   = art_no_m.group(0).replace(" ", "") if art_no_m else ""

        # 超長條文再切段
        if len(art) <= max_chars:
            chunks.append((art_no, art))
        else:
            paragraphs = re.split(r"\n", art)
            buf = ""
            for p in paragraphs:
                if len(buf) + len(p) > max_chars and buf:
                    chunks.append((art_no, buf.strip()))
                    buf = p
                else:
                    buf += "\n" + p
            if buf.strip():
                chunks.append((art_no, buf.strip()))
    return chunks


# ── 來源 1：原始法規 PDF ────────────────────────────────────────
def load_pdf_regulations():
    rows = []
    pdfs = sorted([f for f in os.listdir(PDF_DIR) if f.endswith(".pdf")])
    print(f"  找到 {len(pdfs)} 份 PDF")

    for fname in pdfs:
        law_name = fname.replace(".pdf", "")
        path     = os.path.join(PDF_DIR, fname)
        try:
            with pdfplumber.open(path) as pdf:
                full_text = "\n".join(
                    p.extract_text() or "" for p in pdf.pages
                )
        except Exception as e:
            print(f"    ⚠️  {fname} 讀取失敗：{e}")
            continue

        if not full_text.strip():
            print(f"    ⚠️  {fname} 無文字（可能為掃描圖檔）")
            continue

        chunks = chunk_by_article(full_text, law_name)
        for art_no, content in chunks:
            rows.append({
                "source":     "原始法規",
                "law_name":   law_name,
                "eval_code":  "",
                "condition":  law_name,
                "law_ref":    f"{law_name} {art_no}".strip(),
                "article_no": art_no,
                "content":    content,
            })
        print(f"    ✓ {law_name}：{len(chunks)} 段")

    return rows


# ── 來源 2：EE 總表法規欄 ──────────────────────────────────────
def load_ee_matrix_regulations():
    rows = []
    try:
        wb      = pd.read_excel(EXCEL, sheet_name="EE")
        law_col = next((c for c in wb.columns if "法規" in str(c)), None)
        if not law_col:
            return []
        for _, row in wb.iterrows():
            cond = clean(row.iloc[0])
            law  = clean(row[law_col])
            if not cond or not law or law in ("由Gemini生成", "nan"):
                continue
            rows.append({
                "source":     "EE總表",
                "law_name":   "EE選址條件",
                "eval_code":  "",
                "condition":  cond,
                "law_ref":    law,
                "article_no": "",
                "content":    f"【選址條件：{cond}】\n法規依據：{law}",
            })
        print(f"    ✓ EE總表法規欄：{len(rows)} 筆")
    except Exception as e:
        print(f"    ⚠️  EE總表讀取失敗：{e}")
    return rows


# ── 來源 3：eval_conditions threshold ──────────────────────────
def load_condition_regulations():
    rows = []
    try:
        conn = sqlite3.connect(DB_PATH)
        cur  = conn.cursor()
        cur.execute("""
            SELECT eval_code, condition_no, condition_name, condition_type, threshold
            FROM eval_conditions
            WHERE threshold IS NOT NULL AND threshold != ''
        """)
        for eval_code, no, name, ctype, threshold in cur.fetchall():
            t = clean(threshold)
            if not t:
                continue
            rows.append({
                "source":     "評估條件",
                "law_name":   eval_code,
                "eval_code":  eval_code,
                "condition":  f"{eval_code}-{no:02d} {name}",
                "law_ref":    "",
                "article_no": f"{eval_code}-{no:02d}",
                "content":    f"【{eval_code} {name}】（{ctype}）\n{t}",
            })
        conn.close()
        print(f"    ✓ eval_conditions：{len(rows)} 筆")
    except Exception as e:
        print(f"    ⚠️  eval_conditions 讀取失敗：{e}")
    return rows


# ── 主程式 ─────────────────────────────────────────────────────
def main():
    print("載入 Embedding 模型...")
    model = SentenceTransformer(MODEL_NAME)

    print("\n收集法規資料：")
    src1 = load_pdf_regulations()
    print("\n補充來源：")
    src2 = load_ee_matrix_regulations()
    src3 = load_condition_regulations()

    all_rows = src1 + src2 + src3
    print(f"\n總計：{len(all_rows)} 筆")
    print(f"  原始法規 PDF：{len(src1)} 筆")
    print(f"  EE總表：{len(src2)} 筆")
    print(f"  評估條件：{len(src3)} 筆")

    if not all_rows:
        print("無資料，結束。")
        return

    print(f"\n向量化中...")
    contents = [r["content"] for r in all_rows]
    vectors  = model.encode(contents, show_progress_bar=True, batch_size=32)

    print(f"\n寫入 LanceDB：{LANCE_DIR}")
    db = lancedb.connect(LANCE_DIR)

    table_data = []
    for i, (row, vec) in enumerate(zip(all_rows, vectors)):
        table_data.append({
            "id":         i,
            "source":     row["source"],
            "law_name":   row["law_name"],
            "eval_code":  row["eval_code"],
            "condition":  row["condition"],
            "law_ref":    row["law_ref"],
            "article_no": row["article_no"],
            "content":    row["content"],
            "vector":     vec.tolist(),
        })

    try:
        db.drop_table("regulations")
    except Exception:
        pass
    db.create_table("regulations", data=table_data)
    print(f"  ✓ regulations：{len(table_data)} 筆寫入完成")

    # 更新 SQLite regulation_ids
    print("\n更新 SQLite regulation_ids...")
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    try:
        cur.execute("ALTER TABLE eval_conditions ADD COLUMN regulation_ids TEXT")
    except sqlite3.OperationalError:
        pass
    cur.execute("UPDATE eval_conditions SET regulation_ids = NULL")
    for i, row in enumerate(all_rows):
        if row["source"] != "評估條件" or not row["article_no"]:
            continue
        parts     = row["article_no"].rsplit("-", 1)
        eval_code = "-".join(parts[0].split("-")[:2])
        try:
            cond_no = int(parts[-1])
        except ValueError:
            continue
        cur.execute(
            "UPDATE eval_conditions SET regulation_ids=? WHERE eval_code=? AND condition_no=?",
            (json.dumps([i]), eval_code, cond_no)
        )
    conn.commit()
    conn.close()
    print("  ✓ regulation_ids 更新完成")

    # 驗證搜尋
    print("\n驗證搜尋「農牧用地饋線申請」...")
    tbl     = db.open_table("regulations")
    vec     = model.encode("農牧用地饋線申請條件").tolist()
    results = tbl.search(vec).limit(3).to_list()
    for r in results:
        score = round(1 - r["_distance"], 3)
        print(f"  [{score}] [{r['source']}] {r['law_ref']} → {r['content'][:60]}...")

    print(f"\n✅ 完成！LanceDB 共 {len(table_data)} 筆法規向量")


if __name__ == "__main__":
    main()
