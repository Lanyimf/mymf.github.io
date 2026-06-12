"""
從 generate_eval_sheets.py 的 SHEETS 資料匯入 SQLite，
再結合 laws/ .md 法條文字，重建所有 72 個 rules .md
"""
import os, re, sys, sqlite3, warnings
warnings.filterwarnings('ignore')

BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
DB_PATH   = os.path.join(BASE_DIR, 'land.db')
VAULT     = os.path.join(BASE_DIR, '../../土開')
RULES_DIR = os.path.join(VAULT, 'rules')
LAWS_DIR  = os.path.join(VAULT, 'laws')

# ── Step 1: 匯入 SHEETS 資料 ────────────────────────────────────
sys.path.insert(0, BASE_DIR)

# 動態 exec generate_eval_sheets 取 SHEETS dict（避免執行 main）
src_path = os.path.join(BASE_DIR, 'generate_eval_sheets.py')
src = open(src_path, encoding='utf-8').read()
# 截斷 main() 以下不執行，並替換 __file__ 參照
src = src[:src.rfind('def main()')]
src = src.replace('__file__', f'"{src_path}"')
ns = {'__file__': src_path}
exec(src, ns)
SHEETS = ns['SHEETS']
print(f'SHEETS 資料：{len(SHEETS)} 個評估代號')

# ── Step 2: 寫入 SQLite ─────────────────────────────────────────
conn = sqlite3.connect(DB_PATH)
cur  = conn.cursor()

try:
    cur.execute("ALTER TABLE eval_conditions ADD COLUMN regulation_ids TEXT")
except:
    pass

# 只新增不在 DB 的 eval_code
cur.execute("SELECT DISTINCT eval_code FROM eval_conditions")
existing = {r[0] for r in cur.fetchall()}
print(f'DB 已有：{sorted(existing)}')

imported = 0
for eval_code, info in SHEETS.items():
    if eval_code in existing:
        continue
    for cat in info.get('categories', []):
        cat_name = cat.get('category_name', '')
        # 移除「第X類 」前綴，取後半當 note
        note = re.sub(r'^第[一二三四五六七八九十]+類\s*', '', cat_name)
        for item in cat.get('items', []):
            no, name, itype, std = item[0], item[1], item[2], item[3]
            db_type = 'hard' if itype == '硬性門檻' else 'weighted'
            cur.execute("""
                INSERT INTO eval_conditions
                    (eval_code, condition_no, condition_name, condition_type, threshold, note)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (eval_code, no, name, db_type, std, note))
            imported += 1

conn.commit()
print(f'匯入 {imported} 筆條件到 SQLite')

# ── Step 3: 建立法規關鍵字索引 ─────────────────────────────────
# 讀取 laws/ 抓第一段有實質內容的說明
LAW_SNIPPETS = {}
for fname in os.listdir(LAWS_DIR):
    if not fname.endswith('.md'):
        continue
    law = fname.replace('.md', '')
    text = open(os.path.join(LAWS_DIR, fname), encoding='utf-8').read()
    # 取前 3 條有內容的條文摘要
    articles = re.findall(r'## 第(\d+)條\n(.+?)(?=\n##|\Z)', text, re.DOTALL)
    snippets = []
    for art_no, body in articles[:5]:
        body = body.strip().replace('\n', ' ')[:120]
        if len(body) > 20:
            snippets.append(f'第{art_no}條：{body}')
    LAW_SNIPPETS[law] = snippets

# ── Step 4: 法規對照表（每個 eval_code 對應的核心法規） ─────────
TYPE_LAWS = {
    'EE': ['農業發展條例', '非都市土地使用管制規則',
           '申請農業用地作農業設施容許使用審查辦法',
           '水土保持法', '土壤及地下水污染整治法', '國土計畫法'],
    'EB': ['建築法', '建築技術規則建築設計施工編', '非都市土地使用管制規則',
           '土壤及地下水污染整治法', '國土計畫法'],
    'ED': ['建築法', '廢棄物清理法', '水污染防治法', '環境影響評估法',
           '非都市土地使用管制規則', '土壤及地下水污染整治法', '國土計畫法'],
    'EH': ['水利法', '非都市土地使用管制規則',
           '土壤及地下水污染整治法', '國土計畫法'],
    'EG': ['非都市土地使用管制規則', '國土計畫法',
           '土壤及地下水污染整治法'],
    'EP': ['非都市土地使用管制規則', '環境影響評估法',
           '水土保持法', '國土計畫法', '土壤及地下水污染整治法'],
    'EN': ['殯葬管理條例', '非都市土地使用管制規則',
           '建築法', '土壤及地下水污染整治法', '國土計畫法'],
}

EXTRA_LAWS = {
    'EE-4': ['畜牧法', '畜牧場主要設施設置標準', '動物傳染病防治條例', '水污染防治法'],
    'EE-5': ['漁業法', '水利法', '水污染防治法'],
    'EE-6': ['山坡地保育利用條例'],
    'EE-7': ['休閒農業輔導管理辦法', '消防法'],
    'EE-8': ['再生能源發展條例'],
    'EE-10':['再生能源發展條例', '環境影響評估法'],
    'EE-11':['水利法', '水土保持法'],
    'EE-12':['土石採取法', '環境影響評估法'],
    'EE-14':['溫泉法', '水利法'],
    'EE-15':['農村再生條例'],
    'EE-16':['野生動物保育法'],
    'EE-17':['野生動物保育法', '動物傳染病防治條例'],
    'EE-19':['廢棄物清理法', '空氣污染防制法'],
    'EE-20':['廢棄物清理法', '水污染防治法'],
    'EE-21':['休閒農業輔導管理辦法', '消防法'],
    'EB-2': ['畜牧法', '動物傳染病防治條例'],
    'EB-3': ['漁業法', '水利法'],
    'EB-17':['再生能源發展條例'],
    'EB-19':['溫泉法'],
    'EB-20':['野生動物保育法', '動物傳染病防治條例'],
    'ED-3': ['廢棄物清理法', '空氣污染防制法'],
    'ED-6': ['再生能源發展條例'],
    'EH-1': ['再生能源發展條例'],
    'EH-2': ['土石採取法'],
    'EG-3': ['再生能源發展條例'],
    'EN-4': ['再生能源發展條例'],
    'EN-5': ['殯葬管理條例', '環境影響評估法'],
}

RELATED_RULES = {
    'EE-1': ['EE-2','EE-3','EE-6'],
    'EE-2': ['EE-1','EB-5'],
    'EE-3': ['EE-1','EE-4','EB-1'],
    'EE-4': ['EE-3','EE-5','EB-2'],
    'EE-5': ['EE-4','EH-3'],
    'EE-6': ['EE-1','EN-1','EN-2'],
    'EE-7': ['EE-21','EH-3','EB-12'],
    'EE-8': ['EE-10','EB-17','ED-6','EH-1','EG-3','EN-4'],
    'EE-10':['EE-8','EB-17','ED-6','EH-1','EG-3','EN-4'],
    'EE-11':['EH-7','EH-9'],
    'EE-12':['EH-2','EE-19','ED-7'],
    'EE-14':['EH-5'],
    'EE-15':['EH-6','EG-5'],
    'EE-16':['EE-17','EB-20'],
    'EE-17':['EE-16','EB-20'],
    'EE-19':['EE-12','ED-7','ED-8'],
    'EE-20':['ED-8','EH-8'],
    'EE-21':['EE-7','EH-3','EH-4'],
    'EE-22':['EH-4'],
    'EB-1': ['EE-3','EB-4'],
    'EB-2': ['EE-4','ED-1'],
    'EB-3': ['EE-5'],
    'EB-5': ['EE-2'],
    'EB-12':['EE-7','EH-3','EH-4'],
    'EB-17':['EE-8','EE-10','ED-6','EH-1','EN-4'],
    'EB-19':['EE-14','EH-5'],
    'EB-20':['EE-16','EE-17'],
    'ED-1': ['ED-2','ED-4'],
    'ED-2': ['ED-1','ED-4'],
    'ED-3': ['EE-19','EE-20'],
    'ED-6': ['EE-8','EE-10','EH-1'],
    'ED-7': ['EE-12','EE-19','EH-2'],
    'ED-8': ['EE-20','EH-8'],
    'EH-1': ['EE-8','EE-10','EG-3'],
    'EH-2': ['EE-12','ED-7'],
    'EH-3': ['EH-4','EE-7','EE-21'],
    'EH-4': ['EH-3','EE-21','EE-22'],
    'EH-5': ['EE-14','EB-19'],
    'EH-6': ['EE-15','EG-5'],
    'EH-7': ['EH-9','EH-8'],
    'EH-9': ['EH-7','EE-11'],
    'EG-3': ['EE-8','EH-1'],
    'EG-5': ['EE-15','EH-6'],
    'EN-1': ['EE-6','EN-2'],
    'EN-2': ['EN-1'],
    'EN-4': ['EE-8','EE-10','EB-17'],
    'EN-5': ['EN-6'],
    'EN-6': ['EN-5'],
}

# ── Step 5: 重建所有 72 個 rules .md ───────────────────────────
cur.execute("""
    SELECT DISTINCT m.eval_code, lt.type_code, lt.type_name, ui.item_name
    FROM use_matrix m
    JOIN land_types lt ON m.type_code = lt.type_code
    JOIN use_items  ui ON m.item_no   = ui.item_no
    ORDER BY m.eval_code
""")
eval_meta = {r[0]: {'type_code':r[1],'type_name':r[2],'use_item':r[3]}
             for r in cur.fetchall()}

cur.execute("""
    SELECT eval_code, condition_no, condition_name, condition_type, threshold, note
    FROM eval_conditions ORDER BY eval_code, condition_no
""")
all_conds = {}
for row in cur.fetchall():
    all_conds.setdefault(row[0],[]).append({
        'no':row[1],'name':row[2],'type':row[3],
        'std':row[4] or '','note':row[5] or ''
    })
conn.close()

ICON = {'hard':'🔴 硬性門檻', 'weighted':'🟡 加權指標'}

def build_md(eval_code, meta, conds):
    type_code = meta['type_code']
    hard  = [c for c in conds if c['type']=='hard']
    soft  = [c for c in conds if c['type']!='hard']

    # frontmatter
    lines = [
        '---',
        f'eval_code: {eval_code}',
        f'type_code: {type_code}',
        f'type_name: {meta["type_name"]}',
        f'use_item: {meta["use_item"]}',
        f'hard_count: {len(hard)}',
        f'weighted_count: {len(soft)}',
        f'tags: [評估規則, {type_code}, {eval_code}]',
        '---','',
        f'# {eval_code} {meta["type_name"]}－{meta["use_item"]}','',
        f'- 用地類型：**{type_code} {meta["type_name"]}**',
        f'- 使用項目：**{meta["use_item"]}**',
        f'- 硬性門檻：{len(hard)} 條 ｜ 加權指標：{len(soft)} 條','',
    ]

    # 條件依 note 分組
    cats = {}
    for c in conds:
        cats.setdefault(c['note'] or '一般條件', []).append(c)

    for cat_name, items in cats.items():
        lines.append(f'## {cat_name}')
        lines.append('')
        lines.append('| # | 指標項目 | 類型 | 評估標準 |')
        lines.append('|---|---------|------|---------|')
        for c in items:
            std = c['std'].replace('\n',' ').replace('|','｜')
            icon = ICON.get(c['type'], '🟡 加權指標')
            lines.append(f'| {c["no"]} | {c["name"]} | {icon} | {std} |')
        lines.append('')

    # 相關法規
    law_list = list(dict.fromkeys(
        TYPE_LAWS.get(type_code, []) + EXTRA_LAWS.get(eval_code, [])
    ))
    lines.append('## 相關法規')
    lines.append('')
    for law in law_list:
        snippets = LAW_SNIPPETS.get(law, [])
        hint = f'（{snippets[0][:60]}...）' if snippets else ''
        lines.append(f'- [[laws/{law}]] {hint}')
    lines.append('')

    # 相關評估代號
    related = RELATED_RULES.get(eval_code, [])
    if related:
        lines.append('## 相關評估代號')
        lines.append('')
        for r in related:
            lines.append(f'- [[rules/{r}]]')
        lines.append('')

    return '\n'.join(lines)

count = 0
for eval_code, meta in eval_meta.items():
    conds = all_conds.get(eval_code, [])
    md    = build_md(eval_code, meta, conds)
    path  = os.path.join(RULES_DIR, f'{eval_code}.md')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(md)
    status = f'{len(conds)} 條' if conds else '⚠️ 空'
    print(f'  {eval_code}: {status}')
    count += 1

print(f'\n✅ 重建完成：{count} 個 rules .md')
