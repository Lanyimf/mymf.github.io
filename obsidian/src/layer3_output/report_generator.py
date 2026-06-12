"""
Layer 3 — 評估報告產生器
輸入：地號屬性 + 評分結果 + 法規命中段落
輸出：Markdown 報告（可選：Claude API 潤稿）
"""
import anthropic
from datetime import datetime
from pathlib import Path
from config import OUTPUT_DIR, CLAUDE_MODEL
from src.layer1_data.db import get_parcel, get_c_items_for_zone
from src.layer2_compute.scoring_model import score_parcel, ScoreResult
from src.layer2_compute.rag_engine import query_laws


def _law_section(hits: list[dict]) -> str:
    if not hits:
        return "（查無相關法規）\n"
    lines = []
    for h in hits:
        lines.append(f"**【{h['source']}】** (相似度 {h['score']})\n> {h['text'][:200]}…\n")
    return "\n".join(lines)


def generate_report(landno: str, use_claude: bool = False) -> str:
    """產生單筆地號的 Markdown 評估報告"""
    parcel = get_parcel(landno)
    if not parcel:
        return f"# ❌ 地號不存在\n地號 `{landno}` 在資料庫中找不到。"

    score: ScoreResult = score_parcel(parcel)
    zone = parcel.get("zone") or "未知"
    c_items = get_c_items_for_zone(zone)
    law_hits = query_laws(f"{zone} 土地使用 開發許可 條件", top_k=4)

    # 風險等級
    if score.total >= 70:
        risk_level = "🟢 低風險"
    elif score.total >= 45:
        risk_level = "🟡 中等風險"
    else:
        risk_level = "🔴 高風險"

    c_table = ""
    if c_items:
        rows = "\n".join(f"| {i['item_code']} | {i['item_name']} | {i['condition'] or '—'} |"
                         for i in c_items)
        c_table = f"""
## 可行 C 項目（{zone}）

| 代碼 | 項目名稱 | 附帶條件 |
|------|----------|----------|
{rows}
"""
    else:
        c_table = f"\n## 可行 C 項目\n\n（{zone} 無對應 C 項目，或清單尚未匯入）\n"

    report = f"""# 土地評估報告

**地號：** {landno}
**產出日期：** {datetime.now().strftime('%Y-%m-%d %H:%M')}

---

## 基本資訊

| 欄位 | 數值 |
|------|------|
| 縣市 | {parcel.get('county', '—')} |
| 鄉鎮市區 | {parcel.get('district', '—')} |
| 段名 | {parcel.get('section', '—')} |
| 面積 | {parcel.get('area_m2', '—')} m² |

---

## 國土分區

**{zone}**

---

## GIS 屬性

| 項目 | 數值 |
|------|------|
| 林地重疊率 | {parcel.get('forest_pct', '—')} % |
| 距道路距離 | {parcel.get('road_dist_m', '—')} m |
| 距台電設施 | {parcel.get('taipower_dist_m', '（未計算）')} m |

---

## 適宜性評分

**總分：{score.total} / 100　{risk_level}**

| 項目 | 分數 |
|------|------|
| 分區評分 | {score.zone_score} |
| 道路可及性 | {score.access_score} |
| 限制條件 | {score.constraint_score} |

{"### 🚨 高風險標記" if score.flags else ""}
{"".join(f"- {f}" + chr(10) for f in score.flags)}
{"### ⚠ 注意事項" if score.risks else ""}
{"".join(f"- {r}" + chr(10) for r in score.risks)}

---
{c_table}
---

## 相關法規條文

{_law_section(law_hits)}

---
*本報告由土地評估系統自動產生，僅供參考，實際開發許可請洽主管機關。*
"""

    if use_claude:
        report = _polish_with_claude(report, parcel, score)

    # 存檔
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / f"{landno.replace('/', '_')}_報告.md"
    out_path.write_text(report, encoding="utf-8-sig")
    print(f"✅ 報告已儲存：{out_path}")
    return report


def _polish_with_claude(draft: str, parcel: dict, score: ScoreResult) -> str:
    """呼叫 Claude API 對報告做一段綜合判斷摘要"""
    client = anthropic.Anthropic()
    prompt = f"""以下是一筆土地的 GIS 評估報告草稿，請在報告最前面加上一段 150 字內的「綜合判斷摘要」，
說明這筆土地的開發可行性、主要限制、和最值得關注的風險。用專業但易讀的繁體中文書寫。

---
{draft[:2000]}
"""
    msg = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}]
    )
    summary = msg.content[0].text
    return f"## 綜合判斷摘要\n\n{summary}\n\n---\n\n" + draft


if __name__ == "__main__":
    # 測試：印出第一筆地號的報告
    import sqlite3
    from config import DB_PATH
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT landno FROM parcels LIMIT 1").fetchone()
    conn.close()
    if row:
        print(generate_report(row[0]))
    else:
        print("資料庫尚無地號資料，請先匯入。")
