"""
Layer 2 — 法規條文向量資料庫（RAG）
使用 LanceDB + sentence-transformers
負責：索引法規 PDF/TXT、依地號情境查詢相關條文
"""
import lancedb
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
from config import LANCEDB_PATH, LAW_DOCS_DIR

MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
TABLE_NAME = "law_chunks"
CHUNK_SIZE = 300    # 每段字數

_model: SentenceTransformer | None = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def _embed(texts: list[str]) -> list[list[float]]:
    return _get_model().encode(texts, show_progress_bar=False).tolist()


def _chunk_text(text: str, size: int = CHUNK_SIZE) -> list[str]:
    """以句子為邊界切段"""
    sentences = text.replace("。", "。\n").split("\n")
    chunks, buf = [], ""
    for s in sentences:
        if len(buf) + len(s) > size and buf:
            chunks.append(buf.strip())
            buf = s
        else:
            buf += s
    if buf.strip():
        chunks.append(buf.strip())
    return chunks


def index_laws():
    """掃描 data/法規條文/ 底下的 .txt 檔，建立 LanceDB 索引"""
    LANCEDB_PATH.mkdir(parents=True, exist_ok=True)
    db = lancedb.connect(str(LANCEDB_PATH))

    files = list(LAW_DOCS_DIR.glob("*.txt"))
    if not files:
        print(f"⚠ {LAW_DOCS_DIR} 下沒有 .txt 法規條文，略過索引")
        return

    records = []
    for fp in files:
        text = fp.read_text(encoding="utf-8-sig")
        for i, chunk in enumerate(_chunk_text(text)):
            records.append({
                "source":    fp.stem,
                "chunk_id":  i,
                "text":      chunk,
                "vector":    _embed([chunk])[0],
            })

    tbl = db.create_table(TABLE_NAME, data=records, mode="overwrite")
    print(f"✅ 法規索引完成：{len(records)} 段，來源：{[f.stem for f in files]}")


def query_laws(query: str, top_k: int = 5) -> list[dict]:
    """依查詢字串找最相關的法規條文段落"""
    try:
        db = lancedb.connect(str(LANCEDB_PATH))
        tbl = db.open_table(TABLE_NAME)
    except Exception:
        return [{"source": "（法規庫尚未建立）", "text": "請先執行 index_laws()", "score": 0}]

    vec = _embed([query])[0]
    results = tbl.search(vec).limit(top_k).to_list()
    return [{"source": r["source"], "text": r["text"], "score": round(1 - r.get("_distance", 0), 3)}
            for r in results]


if __name__ == "__main__":
    index_laws()
    # 測試查詢
    hits = query_laws("農牧用地太陽能設置條件")
    for h in hits:
        print(f"[{h['source']}] score={h['score']}\n{h['text'][:100]}\n")
