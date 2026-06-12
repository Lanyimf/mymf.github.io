"""
1. 為 rules/ 每個指標項目加入權重欄位
2. 建立 finance/ 財務試算模型資料夾
"""
import os, re, sqlite3, warnings
warnings.filterwarnings('ignore')

BASE      = '/Users/luoyiran/Documents/土開/obsidian'
VAULT     = f'{BASE}/土開'
RULES_DIR = f'{VAULT}/rules'
FIN_DIR   = f'{VAULT}/finance'
os.makedirs(FIN_DIR, exist_ok=True)

# ── 各分類的權重分配邏輯 ──────────────────────────────────────
# 區位條件：各佔 20% 等分（共 6 條 → 各約 3.3%）
# 空間條件：各佔 15% 等分
# 特定條件（主要）：15%，次要：10%
# 參考指標：各 5%
CAT_WEIGHT = {
    '法規資格條件':  None,       # 硬性，不計分
    '區位條件':      'high',     # 20% 均分
    '空間條件':      'medium',   # 15% 均分
    '農業生產條件':  'low',      # 5% 均分
    '特定條件':      'high',
    '法規資格':      None,
    '計畫符合':      'medium',
    '環境影響':      'medium',
    '執行管理':      'low',
    '一般條件':      'medium',
}

def get_weight_tier(note):
    for key, tier in CAT_WEIGHT.items():
        if key in (note or ''):
            return tier
    return 'medium'

def calc_weights(conditions):
    """計算每個 weighted 條件的分數（硬性=必要，其餘分配 100 分）"""
    weighted = [c for c in conditions if c['type'] != 'hard']
    if not weighted:
        return {c['no']: None for c in conditions}

    # 依 tier 分配比重
    tier_pts = {'high': 3, 'medium': 2, 'low': 1}
    tiers    = [get_weight_tier(c['note']) for c in weighted]
    total    = sum(tier_pts.get(t or 'medium', 2) for t in tiers)

    weights  = {}
    for c, t in zip(weighted, tiers):
        pts = tier_pts.get(t or 'medium', 2)
        w   = round(pts / total * 100, 1)
        weights[c['no']] = w

    # 確保加總=100（調整最大值）
    s = sum(weights.values())
    if s != 100.0:
        max_no = max(weights, key=weights.get)
        weights[max_no] = round(weights[max_no] + (100.0 - s), 1)

    for c in conditions:
        if c['type'] == 'hard':
            weights[c['no']] = None
    return weights

# ── Step 1: 從 DB 讀取所有條件 ───────────────────────────────
conn = sqlite3.connect(f'{BASE}/src/layer2_compute/land.db')
cur  = conn.cursor()
cur.execute("""
    SELECT eval_code, condition_no, condition_name, condition_type, note
    FROM eval_conditions ORDER BY eval_code, condition_no
""")
all_conds = {}
for r in cur.fetchall():
    all_conds.setdefault(r[0],[]).append({
        'no': r[1], 'name': r[2], 'type': r[3], 'note': r[4] or ''
    })
conn.close()

# ── Step 2: 更新 rules .md 加入權重欄位 ──────────────────────
updated = 0
for fname in os.listdir(RULES_DIR):
    if not fname.endswith('.md'):
        continue

    # 從檔名抓 eval_code（R-001_EE-1 → EE-1）
    m = re.search(r'_([A-Z]+-\d+)$', fname.replace('.md',''))
    if not m:
        continue
    eval_code = m.group(1)
    conds     = all_conds.get(eval_code, [])
    if not conds:
        continue

    weights = calc_weights(conds)
    path    = os.path.join(RULES_DIR, fname)
    content = open(path, encoding='utf-8').read()

    # 若已有 權重 欄位就跳過
    if '| 權重 |' in content:
        continue

    # 插入權重欄：| # | 項目 | 類型 | 評估標準 | → | # | 項目 | 類型 | 權重 | 評估標準 |
    content = content.replace(
        '| # | 指標項目 | 類型 | 評估標準 |',
        '| # | 指標項目 | 類型 | 權重 | 評估標準 |'
    )
    content = content.replace(
        '|---|---------|------|---------|',
        '|---|---------|------|------|---------|'
    )

    # 為每個資料列加入權重
    def add_weight(match):
        no_str = match.group(1)
        rest   = match.group(2)
        try:
            no = int(float(no_str.strip()))
        except:
            return match.group(0)
        w = weights.get(no)
        if w is None:
            w_str = '必要'
        else:
            w_str = f'{w}%'
        # 在第3個 | 後插入權重
        parts = rest.split(' | ')
        if len(parts) >= 3:
            parts.insert(2, w_str)
            return f'| {no_str} | {" | ".join(parts)}'
        return match.group(0)

    content = re.sub(
        r'^\| (\d+) \| (.+)$',
        add_weight,
        content,
        flags=re.M
    )

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    updated += 1

print(f'✅ rules/ 權重加入：{updated} 個檔案')

# ── Step 3: 建立 finance/ 財務試算模型 ────────────────────────

MODELS = {
    'F-001_地面型太陽能': {
        'title': 'F-001 地面型太陽能',
        'unit': 'MW', 'build': 3000, 'revenue': 400, 'opex': 50,
        'life': 20, 'salvage': 0.05, 'discount': 0.05,
        'note': '1MW約1公頃，FIT約4元/度',
        'rules': ['R-008_EE-8','R-010_EE-10','R-042_EB-17'],
        'desc': '農牧用地或乙種建築用地設置地面型太陽能，需確認台電饋線容量及農電共生規劃。',
    },
    'F-002_農業溫室': {
        'title': 'F-002 農業溫室',
        'unit': '公頃', 'build': 800, 'revenue': 120, 'opex': 30,
        'life': 15, 'salvage': 0.10, 'discount': 0.05,
        'note': '含水電設備',
        'rules': ['R-001_EE-1','R-003_EE-3'],
        'desc': '農牧用地設置溫室農業設施，需符合農業設施容許使用規定。',
    },
    'F-003_工業廠房': {
        'title': 'F-003 工業廠房',
        'unit': '坪', 'build': 15, 'revenue': 3, 'opex': 0.5,
        'life': 30, 'salvage': 0.20, 'discount': 0.05,
        'note': '乙丁種建地適用',
        'rules': ['R-043_ED-1','R-044_ED-2','R-027_EB-5'],
        'desc': '丁種建築用地設置工業廠房，需符合建築法及工廠管理輔導法規定。',
    },
    'F-004_倉儲物流': {
        'title': 'F-004 倉儲物流',
        'unit': '坪', 'build': 10, 'revenue': 2, 'opex': 0.3,
        'life': 30, 'salvage': 0.15, 'discount': 0.05,
        'note': '近道路優先',
        'rules': ['R-043_ED-1','R-045_ED-3'],
        'desc': '丁種建築用地設置倉儲物流設施，需重視聯外道路條件。',
    },
    'F-005_休閒農場': {
        'title': 'F-005 休閒農場',
        'unit': '公頃', 'build': 600, 'revenue': 200, 'opex': 60,
        'life': 15, 'salvage': 0.10, 'discount': 0.05,
        'note': '最小面積0.5公頃',
        'rules': ['R-007_EE-7','R-021_EE-21'],
        'desc': '農牧用地設置休閒農場，需依休閒農業輔導管理辦法申請籌設許可。',
    },
    'F-006_殯葬設施': {
        'title': 'F-006 殯葬設施',
        'unit': '公頃', 'build': 5000, 'revenue': 800, 'opex': 150,
        'life': 50, 'salvage': 0.30, 'discount': 0.05,
        'note': '含靈骨塔及公墓',
        'rules': ['R-071_EN-5','R-072_EN-6'],
        'desc': '殯葬用地設置殯葬設施，需依殯葬管理條例取得設置許可，選址有距離限制。',
    },
}

def npv(revenue, opex, build, discount, life, salvage):
    net_annual = revenue - opex
    pv_annuity = net_annual * (1 - (1+discount)**(-life)) / discount
    pv_salvage = build * salvage * (1+discount)**(-life)
    return pv_annuity + pv_salvage - build

def roi(revenue, opex, build):
    return (revenue - opex) / build * 100

def payback(revenue, opex, build):
    return build / (revenue - opex)

for key, m in MODELS.items():
    _npv     = npv(m['revenue'], m['opex'], m['build'], m['discount'], m['life'], m['salvage'])
    _roi     = roi(m['revenue'], m['opex'], m['build'])
    _payback = payback(m['revenue'], m['opex'], m['build'])
    rule_links = '  '.join(f'[[rules/{r}]]' for r in m['rules'])

    content = f"""---
finance_id: {key.split('_')[0]}
title: {m['title']}
unit: {m['unit']}
build_cost: {m['build']}
annual_revenue: {m['revenue']}
annual_opex: {m['opex']}
life_years: {m['life']}
discount_rate: {m['discount']}
tags: [財務模型, {key.split('_')[1]}]
---

# {m['title']}

> {m['desc']}

## 基本參數

| 項目 | 數值 | 說明 |
|------|------|------|
| 計算單位 | {m['unit']} | |
| 建設成本 | {m['build']:,} 萬元/{m['unit']} | |
| 年收益 | {m['revenue']:,} 萬元/{m['unit']} | |
| 年維運成本 | {m['opex']:,} 萬元/{m['unit']} | |
| 使用年限 | {m['life']} 年 | |
| 折現率 | {m['discount']*100:.0f}% | |
| 殘值率 | {m['salvage']*100:.0f}% | |
| 備註 | {m['note']} | |

## 財務試算結果

| 指標 | 數值 | 說明 |
|------|------|------|
| **ROI（年報酬率）** | **{_roi:.1f}%** | (年收益－維運成本) / 建設成本 |
| **回收年限** | **{_payback:.1f} 年** | 建設成本 / 年淨收益 |
| **NPV（{m['life']}年）** | **{_npv:,.0f} 萬元** | 折現率 {m['discount']*100:.0f}%，含殘值 |

## 試算公式

```
年淨收益　= 年收益 - 年維運成本
         = {m['revenue']:,} - {m['opex']:,} = {m['revenue']-m['opex']:,} 萬元

ROI　　　 = {m['revenue']-m['opex']:,} / {m['build']:,} × 100 = {_roi:.1f}%

回收年限　= {m['build']:,} / {m['revenue']-m['opex']:,} = {_payback:.1f} 年

NPV　　　 = Σ(年淨收益 × 折現因子) + 殘值現值 - 建設成本
         = {_npv:,.0f} 萬元（{m['life']}年期，折現率{m['discount']*100:.0f}%）
```

## 場址套入試算

> 將實際場址面積代入以下公式：

| 欄位 | 公式 |
|------|------|
| 實際建設成本 | `場址面積（{m['unit']}）× {m['build']:,} 萬元` |
| 實際年收益 | `場址面積（{m['unit']}）× {m['revenue']:,} 萬元` |
| 實際年維運 | `場址面積（{m['unit']}）× {m['opex']:,} 萬元` |

## 適用評估規則

{rule_links}

## 相關法規

- [[laws/L-10_土壤及地下水污染整治法]]
- [[laws/L-22_非都市土地使用管制規則]]

## 風險提醒

- 以上數值為參考基準，實際建設成本依地形、工程難度調整
- 場址若為污染整治場址，需額外計入整治完成成本
- 法規審查時程（6~18個月）未計入回收年限
"""
    path = os.path.join(FIN_DIR, f'{key}.md')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

print(f'✅ finance/ 建立：{len(MODELS)} 個財務模型')
for k in MODELS:
    m = MODELS[k]
    _roi = roi(m['revenue'], m['opex'], m['build'])
    _pb  = payback(m['revenue'], m['opex'], m['build'])
    print(f'  {k} → ROI {_roi:.1f}%，回收 {_pb:.1f}年')
EOF
