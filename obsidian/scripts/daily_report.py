"""
每日變更報告：彙整 revision_log 並發送到 Discord
用法：
  手動執行：python scripts/daily_report.py
  排程執行：加入 Windows 工作排程器，每天 08:00 執行
"""
import sqlite3, sys, requests, os
from pathlib import Path
from datetime import datetime, timedelta
from collections import Counter

BASE    = Path(__file__).parent.parent
L1_DB   = BASE / "src" / "layer1_data"  / "parcels.db"
L3_DB   = BASE / "src" / "layer3_output" / "evaluation.db"
LOG_DIR = BASE / "src" / "layer3_output" / "reports"

# 讀取 .env
_env = BASE / ".env"
if _env.exists():
    for line in _env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

DISCORD_BOT_TOKEN  = os.environ.get("DISCORD_BOT_TOKEN", "")
DISCORD_CHANNEL_ID = os.environ.get("DISCORD_CHANNEL_ID", "1511374222243532880")


def get_revision_summary(days: int = 1) -> dict:
    """取得過去 N 天的變更摘要"""
    conn = sqlite3.connect(L3_DB)
    since = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")

    rows = conn.execute("""
        SELECT sheet, table_name, action, row_key, field, old_value, new_value, timestamp, source
        FROM revision_log
        WHERE timestamp >= ?
        ORDER BY timestamp DESC
    """, (since,)).fetchall()
    conn.close()

    by_sheet   = Counter()
    by_action  = Counter()
    by_field   = Counter()
    changes    = []

    for sheet, table, action, key, field, old, new, ts, src in rows:
        by_sheet[sheet]  += 1
        by_action[action] += 1
        if field:
            by_field[field] += 1
        changes.append({
            "time": ts, "sheet": sheet, "action": action,
            "key": key, "field": field, "old": old, "new": new
        })

    return {
        "total":     len(rows),
        "period":    f"過去 {days} 天",
        "by_sheet":  dict(by_sheet.most_common()),
        "by_action": dict(by_action),
        "by_field":  dict(by_field.most_common(10)),
        "recent":    changes[:20],
    }


def get_db_stats() -> dict:
    """取得各資料庫目前筆數"""
    stats = {}
    for label, db, tables in [
        ("Layer1", L1_DB, ["parcels", "c_items"]),
        ("Layer3", L3_DB, ["evaluation_criteria", "financial_params", "evaluation_results"]),
    ]:
        conn = sqlite3.connect(db)
        for t in tables:
            try:
                n = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                stats[f"{label}/{t}"] = n
            except Exception:
                pass
        conn.close()
    return stats


def build_report(summary: dict, db_stats: dict) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    total = summary["total"]

    lines = [
        f"📊 **土地評估系統 每日變更報告**",
        f"🕐 {now}（{summary['period']}）",
        "",
    ]

    if total == 0:
        lines.append("✅ 今日無任何資料變更")
    else:
        lines.append(f"**總計變更：{total} 筆**")
        lines.append("")

        # by action
        a = summary["by_action"]
        parts = []
        if a.get("INSERT"): parts.append(f"➕ 新增 {a['INSERT']}")
        if a.get("UPDATE"): parts.append(f"✏️ 修改 {a['UPDATE']}")
        if a.get("DELETE"): parts.append(f"🗑️ 刪除 {a['DELETE']}")
        if parts:
            lines.append("  " + "  ".join(parts))
        lines.append("")

        # by sheet
        lines.append("**各 Sheet 變更：**")
        for sheet, n in summary["by_sheet"].items():
            lines.append(f"  • {sheet}：{n} 筆")
        lines.append("")

        # top changed fields
        if summary["by_field"]:
            lines.append("**最常修改欄位：**")
            for field, n in list(summary["by_field"].items())[:5]:
                lines.append(f"  • {field}：{n} 次")
            lines.append("")

        # recent changes
        if summary["recent"]:
            lines.append("**最新 5 筆異動：**")
            for c in summary["recent"][:5]:
                t = c["time"][11:16]
                act = {"INSERT": "➕", "UPDATE": "✏️", "DELETE": "🗑️"}.get(c["action"], "•")
                if c["field"]:
                    lines.append(f"  {act} [{t}] {c['sheet']} | {c['key']} | {c['field']}: {c['old']} → {c['new']}")
                else:
                    lines.append(f"  {act} [{t}] {c['sheet']} | {c['key']} | {c['action']}")

    lines.append("")
    lines.append("**資料庫現況：**")
    for k, n in db_stats.items():
        lines.append(f"  • {k}：{n} 筆")

    return "\n".join(lines)


def save_report(report: str):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    fname = LOG_DIR / f"report_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
    fname.write_text(report, encoding="utf-8")
    print(f"報告已存：{fname}")
    return fname


def send_to_discord(text: str):
    if not DISCORD_BOT_TOKEN:
        print("⚠ 未設定 DISCORD_BOT_TOKEN 環境變數，跳過發送")
        return False
    url = f"https://discord.com/api/v10/channels/{DISCORD_CHANNEL_ID}/messages"
    # Discord 訊息上限 2000 字元，超過則截斷
    chunks = [text[i:i+1900] for i in range(0, len(text), 1900)]
    for chunk in chunks:
        r = requests.post(url,
            headers={"Authorization": f"Bot {DISCORD_BOT_TOKEN}",
                     "Content-Type": "application/json"},
            json={"content": chunk},
            timeout=10
        )
        if r.status_code not in (200, 201):
            print(f"Discord 發送失敗：{r.status_code} {r.text}")
            return False
    return True


def run(days: int = 1):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 產生每日報告...")
    summary  = get_revision_summary(days)
    db_stats = get_db_stats()
    report   = build_report(summary, db_stats)

    print(report)
    save_report(report)

    ok = send_to_discord(report)
    if ok:
        print("✅ 已發送到 Discord")
    else:
        print("ℹ️  報告已存檔，Discord 未發送（需設定 DISCORD_BOT_TOKEN）")


if __name__ == "__main__":
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    run(days)
