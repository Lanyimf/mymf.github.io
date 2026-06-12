"""
自動監聽專案變更並推送到 GitHub
監聽對象：scripts/, src/, config.py, requirements.txt（排除資料庫與 Excel）
用法：python scripts/auto_push.py
儲存任何 .py / .md / .txt / .csv / .json 檔案後，
等待 DEBOUNCE_SEC 秒確認沒有連續變更，再自動 commit + push
"""
import time
import subprocess
import hashlib
from pathlib import Path
from datetime import datetime

BASE         = Path(__file__).parent.parent
WATCH_EXTS   = {".py", ".md", ".txt", ".csv", ".json", ".sql"}
IGNORE_DIRS  = {"venv", "__pycache__", ".git", "lancedb"}
IGNORE_FILES = {"parcels.db", "欄位清單.txt", "merged_preview.csv"}
DEBOUNCE_SEC = 5    # 變更後等幾秒確認無後續變更才 commit
POLL_SEC     = 2


def git(args: list[str]) -> tuple[int, str]:
    r = subprocess.run(
        ["git"] + args,
        cwd=BASE,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    return r.returncode, (r.stdout + r.stderr).strip()


def scan_hash() -> str:
    """掃描所有受監聽檔案的聯合 hash"""
    h = hashlib.md5()
    for path in sorted(BASE.rglob("*")):
        if path.is_dir():
            continue
        if any(d in path.parts for d in IGNORE_DIRS):
            continue
        if path.suffix not in WATCH_EXTS:
            continue
        if path.name in IGNORE_FILES:
            continue
        try:
            h.update(path.read_bytes())
        except Exception:
            pass
    return h.hexdigest()


def has_changes() -> bool:
    code, out = git(["status", "--porcelain"])
    return bool(out.strip())


def commit_and_push():
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Stage 所有變更（.gitignore 會自動排除資料庫與 Excel）
    git(["add", "-A"])

    # 取得 diff 摘要當 commit message
    _, diff_stat = git(["diff", "--cached", "--stat"])
    changed_files = [
        line.split("|")[0].strip()
        for line in diff_stat.splitlines()
        if "|" in line
    ]
    summary = ", ".join(changed_files[:5])
    if len(changed_files) > 5:
        summary += f" 等 {len(changed_files)} 個檔案"

    msg = f"auto: {summary} [{ts}]" if summary else f"auto: update [{ts}]"

    code, out = git(["commit", "-m", msg])
    if code != 0:
        print(f"  commit 失敗：{out}")
        return

    code, out = git(["push", "-u", "origin", "main"])
    if code == 0:
        print(f"  ✅ 已推送：{msg}")
    else:
        print(f"  ❌ push 失敗：{out}")
        print("     請確認 GitHub 登入狀態（gh auth login 或 credential manager）")


def watch():
    print(f"👁  監聽專案變更：{BASE}")
    print(f"   副檔名：{', '.join(sorted(WATCH_EXTS))}")
    print(f"   變更後 {DEBOUNCE_SEC}s 無新變更時自動 commit + push")
    print("   Ctrl+C 停止\n")

    current_hash = scan_hash()
    pending_since: float | None = None

    while True:
        time.sleep(POLL_SEC)
        new_hash = scan_hash()

        if new_hash != current_hash:
            current_hash = new_hash
            pending_since = time.time()
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 偵測到變更，等待 {DEBOUNCE_SEC}s...")
            continue

        # hash 穩定了，檢查是否已過 debounce 時間
        if pending_since and (time.time() - pending_since) >= DEBOUNCE_SEC:
            pending_since = None
            if has_changes():
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 推送中...")
                commit_and_push()
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 無 git 變更，略過")


if __name__ == "__main__":
    # 首次執行：確認 git remote 已設定
    code, out = git(["remote", "get-url", "origin"])
    if code != 0:
        print("❌ 尚未設定 git remote，請先執行：")
        print("   git remote add origin https://github.com/karajankuo/land-evaluation-system.git")
    else:
        print(f"Remote: {out}")
        watch()
