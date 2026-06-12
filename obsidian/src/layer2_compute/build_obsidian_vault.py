"""
建立 Obsidian Vault 完整結構
土地開發Vault/
├─ lands/    ← 342 筆場址
├─ rules/    ← 68 份評估代號 YAML
├─ laws/     ← 23 部法規 .md
└─ cases/    ← 案例模板
"""

import os, re, sys, yaml, sqlite3
sys.path.insert(0, '/opt/anaconda3/lib/python3.12/site-packages')
import pandas as pd
import pdfplumber
import warnings
warnings.filterwarnings('ignore')

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
LAND_DIR  = os.path.join(BASE_DIR, "../..")
VAULT     = os.path.join(LAND_DIR, "土開")
DB_PATH   = os.path.join(BASE_DIR, "land.db")
EXCEL     = os.path.join(LAND_DIR, "場址資料（套圖） .xlsx")
PDF_DIR   = os.path.join(LAND_DIR, "原始法規資料")

for d in ["lands", "rules", "laws", "cases"]:
    os.makedirs(os.path.join(VAULT, d), exist_ok=True)

print(f"Vault 位置：{VAULT}\n")

# ══════════════════════════════════════════════════════════════════
# 1. rules/ ─ 每個 eval_code 一個 YAML
# ══════════════════════════════════════════════════════════════════
print("── 1. 生成 rules/ ──")

conn = sqlite3.connect(DB_PATH)
cur  = conn.cursor()

# 取得所有 eval_code
cur.execute("""
    SELECT DISTINCT m.eval_code, lt.type_code, lt.type_name, ui.item_name
    FROM use_matrix m
    JOIN land_types lt ON m.type_code = lt.type_code
    JOIN use_items  ui ON m.item_no   = ui.item_no
    ORDER BY m.eval_code
""")
eval_meta = {row[0]: {"type_code": row[1], "type_name": row[2], "use_item": row[3]}
             for row in cur.fetchall()}

# 取得各 eval_code 的條件
cur.execute("""
    SELECT eval_code, condition_no, condition_name, condition_type,
           threshold, note, regulation_ids
    FROM eval_conditions
    ORDER BY eval_code, condition_no
""")
all_conditions = {}
for row in cur.fetchall():
    code = row[0]
    all_conditions.setdefault(code, []).append({
        "no":       row[1],
        "name":     row[2],
        "type":     row[3],
        "standard": row[4] or "",
        "category": row[5] or "",
    })

conn.close()

for eval_code, meta in eval_meta.items():
    conditions = all_conditions.get(eval_code, [])
    data = {
        "eval_code":  eval_code,
        "type_code":  meta["type_code"],
        "type_name":  meta["type_name"],
        "use_item":   meta["use_item"],
        "conditions": []
    }
    # 分組
    cats = {}
    for c in conditions:
        cat = c["category"] or "一般條件"
        cats.setdefault(cat, []).append({
            "no":       c["no"],
            "name":     c["name"],
            "type":     c["type"],
            "standard": c["standard"][:200] if c["standard"] else "",
        })
    data["condition_groups"] = [
        {"category": k, "items": v} for k, v in cats.items()
    ]
    data["hard_count"]     = sum(1 for c in conditions if c["type"] == "hard")
    data["weighted_count"] = sum(1 for c in conditions if c["type"] != "hard")
    data["laws"]           = []  # 後續可補充

    fname = os.path.join(VAULT, "rules", f"{eval_code}.yaml")
    with open(fname, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True, default_flow_style=False,
                  sort_keys=False, indent=2)

print(f"  ✓ {len(eval_meta)} 個 YAML 寫入 rules/")


# ══════════════════════════════════════════════════════════════════
# 2. laws/ ─ 每部法規一個 .md
# ══════════════════════════════════════════════════════════════════
print("\n── 2. 生成 laws/ ──")

# 現有 PDF 法規
PDF_LAWS = {
    f.replace(".pdf", ""): os.path.join(PDF_DIR, f)
    for f in os.listdir(PDF_DIR) if f.endswith(".pdf")
}

# 缺少的法規（根據評估條件引用但 PDF 資料夾沒有的）
MISSING_LAWS = {
    "都市計畫法":      "https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=D0070001",
    "區域計畫法施行細則": "https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=D0070017",
    "溫泉法":          "https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=D0070119",
    "殯葬管理條例":    "https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=D0050046",
    "漁業法":          "https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=M0050001",
    "電業法":          "https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=J0030011",
    "再生能源發展條例": "https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=J0130015",
    "噪音管制法":      "https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=O0020002",
    "飲用水管理條例":  "https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=O0040001",
    "環境影響評估法":  "https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=O0090001",
    "電信管理法":      "https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=K0060111",
    "休閒農業輔導管理辦法": "https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=M0090031",
    "農村再生條例":    "https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=M0090058",
    "野生動物保育法":  "https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=M0060027",
    "動物保護法":      "https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=M0060027",
    "土石採取法":      "https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=D0070166",
    "建築法":          "（已有 PDF）",
    "公路法":          "https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=K0040001",
    "戶外廣告物管理辦法": "https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=D0070144",
    "森林法":          "https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=M0040001",
    "工廠管理輔導法":  "https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=J0040003",
    "產業創新條例":    "https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode=J0040051",
    "營建剩餘土石方處理方案": "（行政規則，非法律）",
}

# 從 PDF 生成 .md
for law_name, pdf_path in PDF_LAWS.items():
    try:
        with pdfplumber.open(pdf_path) as pdf:
            full_text = "\n".join(p.extract_text() or "" for p in pdf.pages)
    except Exception as e:
        print(f"  ⚠️  {law_name} PDF 讀取失敗：{e}")
        continue

    # 切成條文段落
    articles = re.split(r"(?=第\s*\d+\s*條)", full_text)
    md_lines = [
        f"# {law_name}",
        "",
        f"> 來源：原始法規資料/{law_name}.pdf",
        f"> 匯入日期：2026-06-12",
        "",
        "---",
        "",
    ]
    for art in articles:
        art = art.strip()
        if len(art) < 5:
            continue
        art_no = re.match(r"第\s*(\d+)\s*條", art)
        if art_no:
            md_lines.append(f"## 第{art_no.group(1)}條")
            body = art[art_no.end():].strip()
            md_lines.append(body)
        else:
            md_lines.append(art)
        md_lines.append("")

    fname = os.path.join(VAULT, "laws", f"{law_name}.md")
    with open(fname, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))
    print(f"  ✓ {law_name}.md（{len(articles)} 條）")

# 缺少法規生成佔位 .md（標記需補充）
missing_md_count = 0
for law_name, url in MISSING_LAWS.items():
    if law_name in PDF_LAWS or law_name == "建築法":
        continue
    fname = os.path.join(VAULT, "laws", f"{law_name}.md")
    if os.path.exists(fname):
        continue
    content = f"""# {law_name}

> ⚠️ **尚未匯入完整條文**
> 請至以下網址下載 PDF 後重新執行匯入：
> {url}
>
> 匯入方式：將 PDF 放入 `原始法規資料/` 資料夾，重新執行 `build_lancedb.py`

---

## 法規用途

此法規在本系統中用於以下評估代號之判斷依據，完整條文請至全國法規資料庫查詢。

"""
    with open(fname, "w", encoding="utf-8") as f:
        f.write(content)
    missing_md_count += 1

print(f"  ✓ 缺少法規佔位檔：{missing_md_count} 個（標記需補充）")


# ══════════════════════════════════════════════════════════════════
# 3. lands/ ─ 342 筆場址
# ══════════════════════════════════════════════════════════════════
print("\n── 3. 生成 lands/ ──")

df = pd.read_excel(EXCEL, sheet_name="merged")

STATUS_MAP = {
    "公告為控制場址": "🟡 控制場址",
    "公告為整治場址": "🔴 整治場址",
    "部分解列": "🟢 部分解列",
    "解除控制": "🟢 解除控制",
    "解除整治": "🟢 解除整治",
}

for _, row in df.iterrows():
    sid    = str(row.get("場址編號", "")).strip()
    name   = str(row.get("場址名稱", "")).strip()
    area   = row.get("場址面積", "")
    addr   = str(row.get("場址地址", "")).strip()
    parcel = str(row.get("場址地號", "")).strip()
    status = str(row.get("列管狀態", "")).strip()
    prog   = row.get("改善整治進度百分比", "")
    land_t = str(row.get("場址土地類型", "")).strip()
    zoning = str(row.get("非都使用分區_2", "")).strip()
    use_cl = str(row.get("使用地類別", "")).strip()
    water  = str(row.get("是否為水源水質保護區", "")).strip()
    cx     = row.get("座標x", "")
    cy     = row.get("座標y", "")

    status_icon = STATUS_MAP.get(status, f"⚪ {status}")

    # 判斷可用評估代號（根據使用地類別）
    code_map = {
        "農牧用地": "EE", "乙種建築用地": "EB", "丁種建築用地": "ED",
        "水利用地": "EH", "交通用地": "EG", "特定目的事業用地": "EP",
        "殯葬用地": "EN",
    }
    type_code = code_map.get(use_cl.replace("（", "(").replace("）", ")"), "")
    eval_link = f"[[rules/{type_code}]]" if type_code else "（待確認）"

    content = f"""---
id: {sid}
name: {name}
area_m2: {area}
address: {addr}
parcel: {parcel}
status: {status}
progress_pct: {prog}
land_type: {land_t}
zoning: {zoning}
use_class: {use_cl}
water_protection: {water}
coord_x: {cx}
coord_y: {cy}
tags: [場址, {status}, {use_cl}]
---

# {sid} {name}

## 基本資料

| 項目 | 內容 |
|------|------|
| 場址編號 | `{sid}` |
| 列管狀態 | {status_icon} |
| 場址面積 | {area} m² |
| 地址 | {addr} |
| 地號 | {parcel} |
| 土地類型 | {land_t} |
| 使用分區 | {zoning} |
| 使用地類別 | {use_cl} |
| 水源保護區 | {water} |
| 整治進度 | {prog}% |

## 座標

- X：{cx}
- Y：{cy}

## 評估資料

- 適用評估系列：{eval_link}
- 評估結果：（待執行評估引擎）

## 相關法規

- [[laws/土壤及地下水污染整治法]]

## 備註

"""
    fname = os.path.join(VAULT, "lands", f"{sid}.md")
    with open(fname, "w", encoding="utf-8") as f:
        f.write(content)

print(f"  ✓ {len(df)} 筆場址 .md 寫入 lands/")


# ══════════════════════════════════════════════════════════════════
# 4. cases/ ─ 案例模板
# ══════════════════════════════════════════════════════════════════
print("\n── 4. 生成 cases/ ──")

CASE_TEMPLATES = [
    ("Case001_農牧用地轉型太陽光電", "EE-8", "EE-10",
     "台南市某農牧用地（EE）申請設置地面型太陽光電（EE-8）評估案例。\n重點：台電饋線容量確認、農電共生規劃、農業主管機關同意。"),
    ("Case002_農牧用地休閒農場申請", "EE-7", None,
     "申請休閒農場設置許可（EE-7）之評估案例。\n重點：面積≥0.5公頃、農業經營事實、住宿設施面積上限。"),
    ("Case003_乙種建築用地殯葬設施", "EN-5", None,
     "殯葬用地申請殯葬設施設置許可（EN-5）評估案例。\n重點：選址距離限制、水源保護距離、殯葬管理條例合規。"),
    ("Case004_丁種建築用地廢棄物處理", "ED-3", None,
     "丁種建築用地申請廢棄物回收貯存清除處理設施（ED-3）評估案例。\n重點：環評、廢棄物處理許可、距住宅距離。"),
    ("Case005_水利用地滯洪設施", "EH-9", None,
     "水利用地設置滯洪設施（EH-9）評估案例。\n重點：水利主管機關同意、行水功能不妨礙、防洪安全確認。"),
]

for case_name, primary_rule, secondary_rule, desc in CASE_TEMPLATES:
    links = [f"[[rules/{primary_rule}]]"]
    if secondary_rule:
        links.append(f"[[rules/{secondary_rule}]]")

    content = f"""---
case_id: {case_name.split('_')[0]}
title: {case_name.split('_', 1)[1]}
primary_rule: {primary_rule}
status: 模板
tags: [案例, {primary_rule}]
---

# {case_name.split('_', 1)[1]}

## 案例說明

{desc}

## 適用評估規則

- 主要規則：{links[0]}
{"- 次要規則：" + links[1] if len(links) > 1 else ""}

## 場址連結

- 場址：（請連結對應 [[lands/場址編號]]）

## 評估流程

### Layer 1：硬性門檻篩選

- [ ] 用地編定確認
- [ ] 污染場址身份確認
- [ ] 環境敏感地區確認

### Layer 2：加權評分

| 條件 | 權重 | 得分 | 說明 |
|------|------|------|------|
| 國土功能分區 | 30% | - | 待 GIS 套疊 |
| 道路可及性 | 20% | - | 待 GIS 套疊 |
| 台電饋線 | 20% | - | 待確認 |
| 林地重疊率 | 15% | - | 待 GIS 套疊 |
| 整治進度 | 10% | - | 見場址資料 |
| 土地面積 | 5% | - | 見場址資料 |

### Layer 3：財務試算

- 總投入成本：（待試算）
- 預估年收益：（待試算）
- ROI：（待試算）
- 回收年限：（待試算）

## 相關法規

- [[laws/非都市土地使用管制規則]]
- [[laws/土壤及地下水污染整治法]]
- [[laws/申請農業用地作農業設施容許使用審查辦法]]

## 結論

（待評估引擎輸出）

"""
    fname = os.path.join(VAULT, "cases", f"{case_name}.md")
    with open(fname, "w", encoding="utf-8") as f:
        f.write(content)

print(f"  ✓ {len(CASE_TEMPLATES)} 個案例模板寫入 cases/")


# ══════════════════════════════════════════════════════════════════
# 5. README 首頁
# ══════════════════════════════════════════════════════════════════
readme = """# 土地開發評估系統 知識庫

## 結構說明

| 資料夾 | 說明 | 檔案數 |
|--------|------|--------|
| [[lands/]] | 342 筆污染場址基本資料 | 342 |
| [[rules/]] | 68 份評估指標 YAML（EE/EB/ED/EH/EG/EP/EN） | 68 |
| [[laws/]] | 23 部法規全文 + 缺少法規佔位檔 | 40+ |
| [[cases/]] | 評估案例模板 | 5+ |

## 快速查詢

- 農牧用地評估規則：[[rules/EE-1]] [[rules/EE-7]] [[rules/EE-8]]
- 殯葬設施評估：[[rules/EN-5]] [[rules/EN-6]]
- 核心法規：[[laws/非都市土地使用管制規則]] [[laws/農業發展條例]] [[laws/土壤及地下水污染整治法]]

## 缺少法規（需補充）

以下法規尚未有 PDF，已建立佔位檔，請至全國法規資料庫下載：

- [[laws/都市計畫法]]
- [[laws/殯葬管理條例]]
- [[laws/再生能源發展條例]]
- [[laws/環境影響評估法]]
- [[laws/農村再生條例]]
- [[laws/休閒農業輔導管理辦法]]
- [[laws/土石採取法]]
- [[laws/溫泉法]]
- [[laws/漁業法]]
- [[laws/野生動物保育法]]
- [[laws/動物保護法]]
- [[laws/噪音管制法]]

## 系統架構

```
評估引擎（Python）→ SQLite land.db → LanceDB regulations
         ↓
  Obsidian Vault（本知識庫）
```

"""
with open(os.path.join(VAULT, "README.md"), "w", encoding="utf-8") as f:
    f.write(readme)

print("\n  ✓ README.md 首頁生成完成")
print(f"\n✅ Obsidian Vault 建立完成：{VAULT}")
