"""
建立 Obsidian Vault 全面連結
① lands → rules   (依使用地類別)
② rules → laws    (依評估條件引用)
③ laws  → laws    (法規互引關係)
④ rules → rules   (同類/相關用途互連)
⑤ cases → all     (案例串聯)
"""

import os, re, sqlite3, warnings
warnings.filterwarnings('ignore')

VAULT = '/Users/luoyiran/Documents/土開/土開'

# ── 輔助函式 ────────────────────────────────────────────────────

def read_md(path):
    with open(path, encoding='utf-8') as f:
        return f.read()

def write_md(path, content):
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def add_links_section(content, section_title, new_links):
    """在「## 相關法規」或指定區塊插入連結，去重"""
    existing = set(re.findall(r'\[\[([^\]]+)\]\]', content))
    to_add = [l for l in new_links if l.split('|')[0] not in existing]
    if not to_add:
        return content, 0

    lines_to_add = '\n'.join(f'- [[{l}]]' for l in to_add)

    if section_title in content:
        content = content.replace(
            section_title,
            f'{section_title}\n{lines_to_add}'
        )
    else:
        content += f'\n\n## {section_title}\n\n{lines_to_add}\n'
    return content, len(to_add)


# ══════════════════════════════════════════════════════════════════
# ① lands → rules
# ══════════════════════════════════════════════════════════════════

# 使用地類別 → type_code
USE_TO_CODE = {
    '農牧用地': 'EE', '乙種建築用地': 'EB', '丁種建築用地': 'ED',
    '水利用地': 'EH', '交通用地': 'EG', '特定目的事業用地': 'EP',
    '殯葬用地': 'EN',
}

# type_code → 所有 eval_code（從 rules/ 讀取）
CODE_TO_EVALS = {}
rules_dir = os.path.join(VAULT, 'rules')
for fname in os.listdir(rules_dir):
    if fname.endswith('.md'):
        eval_code = fname.replace('.md', '')
        type_code = eval_code.split('-')[0]
        CODE_TO_EVALS.setdefault(type_code, []).append(eval_code)
for k in CODE_TO_EVALS:
    CODE_TO_EVALS[k].sort()

# 額外的法規連結（所有場址都要有）
LAND_BASE_LAWS = [
    'laws/土壤及地下水污染整治法',
    'laws/國土計畫法',
    'laws/非都市土地使用管制規則',
]

lands_dir = os.path.join(VAULT, 'lands')
lands_updated = 0
for fname in os.listdir(lands_dir):
    if not fname.endswith('.md'):
        continue
    path = os.path.join(lands_dir, fname)
    content = read_md(path)

    # 從 frontmatter 讀 use_class
    m = re.search(r'use_class:\s*(.+)', content)
    use_class = m.group(1).strip() if m else ''
    type_code = USE_TO_CODE.get(use_class, '')

    added = 0
    if type_code and type_code in CODE_TO_EVALS:
        rule_links = [f'rules/{ec}' for ec in CODE_TO_EVALS[type_code]]
        content, n = add_links_section(content, '## 評估資料', [])
        # 替換評估資料區塊
        existing_rules = set(re.findall(r'rules/([A-Z]+-\d+)', content))
        new_rules = [f'rules/{ec}' for ec in CODE_TO_EVALS[type_code]
                     if ec not in existing_rules]
        if new_rules:
            rule_str = '  '.join(f'[[{r}]]' for r in new_rules)
            if '- 適用評估系列：' in content:
                content = re.sub(
                    r'- 適用評估系列：.*',
                    f'- 適用評估系列：{"  ".join(f"[[{r}]]" for r in [f"rules/{ec}" for ec in CODE_TO_EVALS[type_code]])}',
                    content
                )
            added += len(new_rules)

    # 加入基礎法規連結
    content, n = add_links_section(content, '## 相關法規', LAND_BASE_LAWS)
    added += n

    if added > 0:
        write_md(path, content)
        lands_updated += 1

print(f'① lands → rules/laws：{lands_updated}/{len(os.listdir(lands_dir))} 筆場址更新')


# ══════════════════════════════════════════════════════════════════
# ② rules → laws（依評估代號對應的法規）
# ══════════════════════════════════════════════════════════════════

# 每個 eval_code 對應的核心法規
RULE_LAWS = {
    # EE 農牧用地 共通
    'EE': ['laws/農業發展條例', 'laws/非都市土地使用管制規則',
           'laws/申請農業用地作農業設施容許使用審查辦法',
           'laws/水土保持法', 'laws/土壤及地下水污染整治法', 'laws/國土計畫法'],
    # EE 特定
    'EE-2': ['laws/農業用地興建農舍辦法', 'laws/建築法'],
    'EE-3': ['laws/申請農業用地作農業設施容許使用審查辦法', 'laws/食品安全衛生管理法'],
    'EE-4': ['laws/畜牧法', 'laws/畜牧場主要設施設置標準',
             'laws/水污染防治法', 'laws/動物傳染病防治條例'],
    'EE-5': ['laws/漁業法', 'laws/水利法', 'laws/水污染防治法'],
    'EE-6': ['laws/山坡地保育利用條例', 'laws/水土保持法'],
    'EE-7': ['laws/休閒農業輔導管理辦法', 'laws/消防法', 'laws/水污染防治法'],
    'EE-8': ['laws/再生能源發展條例', 'laws/農業發展條例'],
    'EE-10':['laws/再生能源發展條例', 'laws/環境影響評估法'],
    'EE-11':['laws/水土保持法', 'laws/水利法'],
    'EE-12':['laws/土石採取法', 'laws/水土保持法', 'laws/環境影響評估法'],
    'EE-14':['laws/溫泉法', 'laws/水利法', 'laws/水污染防治法'],
    'EE-15':['laws/農村再生條例'],
    'EE-16':['laws/野生動物保育法'],
    'EE-17':['laws/動物傳染病防治條例', 'laws/野生動物保育法'],
    'EE-19':['laws/廢棄物清理法', 'laws/空氣污染防制法'],
    'EE-20':['laws/廢棄物清理法', 'laws/水污染防治法'],
    'EE-21':['laws/休閒農業輔導管理辦法', 'laws/消防法', 'laws/水污染防治法'],
    # EB 乙種建築用地 共通
    'EB': ['laws/建築法', 'laws/非都市土地使用管制規則',
           'laws/土壤及地下水污染整治法', 'laws/國土計畫法',
           'laws/建築技術規則建築設計施工編'],
    'EB-2': ['laws/畜牧法', 'laws/水污染防治法', 'laws/動物傳染病防治條例'],
    'EB-3': ['laws/漁業法', 'laws/水利法'],
    'EB-5': ['laws/建築法', 'laws/建築技術規則建築設計施工編'],
    'EB-14':['laws/廢棄物清理法', 'laws/水污染防治法', 'laws/空氣污染防制法'],
    'EB-17':['laws/再生能源發展條例'],
    'EB-19':['laws/溫泉法', 'laws/水利法'],
    'EB-20':['laws/動物傳染病防治條例', 'laws/野生動物保育法'],
    # ED 丁種建築用地 共通
    'ED': ['laws/建築法', 'laws/非都市土地使用管制規則',
           'laws/廢棄物清理法', 'laws/水污染防治法',
           'laws/土壤及地下水污染整治法', 'laws/國土計畫法',
           'laws/環境影響評估法'],
    'ED-3':['laws/廢棄物清理法', 'laws/空氣污染防制法', 'laws/水污染防治法'],
    'ED-6':['laws/再生能源發展條例'],
    # EH 水利用地 共通
    'EH': ['laws/水利法', 'laws/非都市土地使用管制規則',
           'laws/土壤及地下水污染整治法', 'laws/國土計畫法'],
    'EH-1':['laws/再生能源發展條例'],
    'EH-2':['laws/土石採取法', 'laws/環境影響評估法'],
    # EG 交通用地 共通
    'EG': ['laws/非都市土地使用管制規則', 'laws/國土計畫法',
           'laws/土壤及地下水污染整治法'],
    'EG-3':['laws/再生能源發展條例'],
    # EP 特定目的事業用地
    'EP': ['laws/非都市土地使用管制規則', 'laws/環境影響評估法',
           'laws/水土保持法', 'laws/國土計畫法',
           'laws/土壤及地下水污染整治法'],
    # EN 殯葬用地 共通
    'EN': ['laws/殯葬管理條例', 'laws/非都市土地使用管制規則',
           'laws/建築法', 'laws/土壤及地下水污染整治法', 'laws/國土計畫法'],
    'EN-4':['laws/再生能源發展條例'],
    'EN-5':['laws/殯葬管理條例', 'laws/建築法', 'laws/環境影響評估法'],
    'EN-6':['laws/殯葬管理條例'],
}

rules_updated = 0
for fname in os.listdir(rules_dir):
    if not fname.endswith('.md'):
        continue
    eval_code = fname.replace('.md', '')
    type_code = eval_code.split('-')[0]
    path = os.path.join(rules_dir, fname)
    content = read_md(path)

    # 共通 + 特定法規
    law_links = list(dict.fromkeys(
        RULE_LAWS.get(type_code, []) + RULE_LAWS.get(eval_code, [])
    ))

    content, n = add_links_section(content, '## 相關法規', law_links)
    if n > 0:
        write_md(path, content)
        rules_updated += 1

print(f'② rules → laws：{rules_updated}/{len(os.listdir(rules_dir))} 個規則更新')


# ══════════════════════════════════════════════════════════════════
# ③ laws → laws（法規互引）
# ══════════════════════════════════════════════════════════════════

LAW_REFS = {
    '農業發展條例':       ['非都市土地使用管制規則', '農業用地興建農舍辦法',
                          '申請農業用地作農業設施容許使用審查辦法', '國土計畫法', '農田水利法'],
    '非都市土地使用管制規則': ['農業發展條例', '國土計畫法', '區域計畫法', '建築法'],
    '國土計畫法':         ['區域計畫法', '非都市土地使用管制規則', '環境影響評估法'],
    '土壤及地下水污染整治法': ['農業發展條例', '水污染防治法', '廢棄物清理法',
                              '土壤污染監測標準', '環境影響評估法'],
    '水土保持法':         ['山坡地保育利用條例', '區域計畫法', '環境影響評估法'],
    '建築法':             ['建築技術規則建築設計施工編', '消防法', '區域計畫法'],
    '畜牧法':             ['農業發展條例', '水污染防治法', '動物傳染病防治條例',
                          '畜牧場主要設施設置標準', '廢棄物清理法'],
    '水污染防治法':       ['放流水標準', '廢棄物清理法', '水利法'],
    '廢棄物清理法':       ['水污染防治法', '空氣污染防制法', '環境影響評估法'],
    '再生能源發展條例':   ['電業法', '環境影響評估法', '農業發展條例'],
    '殯葬管理條例':       ['建築法', '環境影響評估法', '水污染防治法'],
    '休閒農業輔導管理辦法': ['農業發展條例', '建築法', '水污染防治法', '消防法'],
    '農村再生條例':       ['農業發展條例', '非都市土地使用管制規則'],
    '漁業法':             ['水利法', '水污染防治法', '農業發展條例'],
    '溫泉法':             ['水利法', '水污染防治法', '建築法'],
    '土石採取法':         ['水土保持法', '環境影響評估法', '廢棄物清理法'],
    '野生動物保育法':     ['農業發展條例', '環境影響評估法'],
    '環境影響評估法':     ['水污染防治法', '空氣污染防制法', '廢棄物清理法',
                          '國土計畫法', '水土保持法'],
    '動物傳染病防治條例': ['畜牧法', '野生動物保育法'],
    '申請農業用地作農業設施容許使用審查辦法': ['農業發展條例', '水土保持法',
                                               '非都市土地使用管制規則'],
    '農業用地興建農舍辦法': ['農業發展條例', '建築法', '非都市土地使用管制規則'],
    '農田水利法':         ['水利法', '農業發展條例', '水污染防治法'],
}

laws_dir = os.path.join(VAULT, 'laws')
laws_updated = 0
for fname in os.listdir(laws_dir):
    if not fname.endswith('.md'):
        continue
    law_name = fname.replace('.md', '')
    if law_name not in LAW_REFS:
        continue
    path = os.path.join(laws_dir, fname)
    content = read_md(path)

    ref_links = [f'laws/{r}' for r in LAW_REFS[law_name]]
    content, n = add_links_section(content, '## 相關法規', ref_links)
    if n > 0:
        write_md(path, content)
        laws_updated += 1

print(f'③ laws → laws：{laws_updated} 部法規加入互引連結')


# ══════════════════════════════════════════════════════════════════
# ④ rules → rules（同類/相關互連）
# ══════════════════════════════════════════════════════════════════

RULE_REFS = {
    # 農牧用地同類互連
    'EE-1': ['rules/EE-2', 'rules/EE-3', 'rules/EE-6'],
    'EE-2': ['rules/EE-1', 'rules/EB-5'],
    'EE-3': ['rules/EE-1', 'rules/EE-4', 'rules/EB-1'],
    'EE-4': ['rules/EE-3', 'rules/EE-5', 'rules/EB-2'],
    'EE-5': ['rules/EE-4', 'rules/EH-3'],
    'EE-6': ['rules/EE-1', 'rules/EN-1', 'rules/EN-2'],
    'EE-7': ['rules/EE-1', 'rules/EE-21', 'rules/EB-12'],
    # 綠能/再生能源
    'EE-8': ['rules/EE-10', 'rules/EB-17', 'rules/ED-6',
             'rules/EH-1', 'rules/EG-3', 'rules/EN-4'],
    'EE-10':['rules/EE-8', 'rules/EB-17', 'rules/ED-6',
             'rules/EH-1', 'rules/EG-3', 'rules/EN-4'],
    'EB-17':['rules/EE-8', 'rules/EE-10', 'rules/ED-6', 'rules/EN-4'],
    'ED-6': ['rules/EE-8', 'rules/EE-10', 'rules/EH-1'],
    'EH-1': ['rules/EE-8', 'rules/EE-10', 'rules/EG-3'],
    'EG-3': ['rules/EE-8', 'rules/EH-1'],
    'EN-4': ['rules/EE-8', 'rules/EE-10'],
    # 殯葬
    'EN-5': ['rules/EN-6', 'rules/EN-1', 'rules/EN-4'],
    'EN-6': ['rules/EN-5'],
    # 廢棄物/土石
    'EE-12':['rules/EE-19', 'rules/EH-2', 'rules/ED-7'],
    'EE-19':['rules/EE-12', 'rules/EH-2', 'rules/ED-7', 'rules/ED-8'],
    'ED-3': ['rules/EE-20', 'rules/ED-7', 'rules/ED-8'],
    'EH-2': ['rules/EE-12', 'rules/EE-19'],
    # 農村再生
    'EE-15':['rules/EH-6', 'rules/EG-5'],
    'EH-6': ['rules/EE-15', 'rules/EG-5'],
    'EG-5': ['rules/EE-15', 'rules/EH-6'],
    # 自然保育/動物保護
    'EE-16':['rules/EE-17', 'rules/EB-20'],
    'EE-17':['rules/EE-16', 'rules/EB-20'],
    'EB-20':['rules/EE-17', 'rules/EE-16'],
    # 遊憩
    'EE-7': ['rules/EE-21', 'rules/EH-3', 'rules/EH-4', 'rules/EG-4'],
    'EE-21':['rules/EE-7', 'rules/EH-3', 'rules/EH-4'],
    'EH-3': ['rules/EH-4', 'rules/EE-21', 'rules/EG-4'],
    'EH-4': ['rules/EH-3', 'rules/EE-21'],
    # 工業
    'ED-1': ['rules/ED-2', 'rules/ED-4'],
    'ED-2': ['rules/ED-1', 'rules/ED-4'],
    # 交通
    'EB-16':['rules/EG-2', 'rules/EG-6'],
    'EG-2': ['rules/EB-16', 'rules/EG-6'],
}

rules_ref_updated = 0
for fname in os.listdir(rules_dir):
    if not fname.endswith('.md'):
        continue
    eval_code = fname.replace('.md', '')
    if eval_code not in RULE_REFS:
        continue
    path = os.path.join(rules_dir, fname)
    content = read_md(path)

    content, n = add_links_section(content, '## 相關評估代號', RULE_REFS[eval_code])
    if n > 0:
        write_md(path, content)
        rules_ref_updated += 1

print(f'④ rules → rules：{rules_ref_updated} 個評估代號加入互連')


# ══════════════════════════════════════════════════════════════════
# ⑤ cases → all
# ══════════════════════════════════════════════════════════════════

CASE_LINKS = {
    'Case001_農牧用地轉型太陽光電': {
        'rules': ['rules/EE-8', 'rules/EE-10', 'rules/EB-17'],
        'laws':  ['laws/再生能源發展條例', 'laws/農業發展條例',
                  'laws/申請農業用地作農業設施容許使用審查辦法',
                  'laws/土壤及地下水污染整治法'],
    },
    'Case002_農牧用地休閒農場申請': {
        'rules': ['rules/EE-7', 'rules/EE-21'],
        'laws':  ['laws/休閒農業輔導管理辦法', 'laws/農業發展條例',
                  'laws/建築法', 'laws/水污染防治法'],
    },
    'Case003_乙種建築用地殯葬設施': {
        'rules': ['rules/EN-5', 'rules/EN-6'],
        'laws':  ['laws/殯葬管理條例', 'laws/建築法',
                  'laws/環境影響評估法', 'laws/土壤及地下水污染整治法'],
    },
    'Case004_丁種建築用地廢棄物處理': {
        'rules': ['rules/ED-3', 'rules/ED-7', 'rules/ED-8'],
        'laws':  ['laws/廢棄物清理法', 'laws/水污染防治法',
                  'laws/空氣污染防制法', 'laws/環境影響評估法'],
    },
    'Case005_水利用地滯洪設施': {
        'rules': ['rules/EH-9', 'rules/EH-7', 'rules/EH-8'],
        'laws':  ['laws/水利法', 'laws/區域計畫法',
                  'laws/環境影響評估法', 'laws/土壤及地下水污染整治法'],
    },
}

cases_dir = os.path.join(VAULT, 'cases')
cases_updated = 0
for fname in os.listdir(cases_dir):
    if not fname.endswith('.md'):
        continue
    case_name = fname.replace('.md', '')
    if case_name not in CASE_LINKS:
        continue
    path = os.path.join(cases_dir, fname)
    content = read_md(path)

    links = CASE_LINKS[case_name]
    content, n1 = add_links_section(content, '## 適用評估規則', links['rules'])
    content, n2 = add_links_section(content, '## 相關法規', links['laws'])
    if n1 + n2 > 0:
        write_md(path, content)
        cases_updated += 1

print(f'⑤ cases → all：{cases_updated} 個案例更新')


# ── 統計最終結果 ────────────────────────────────────────────────
print('\n── 最終連結統計 ──')
all_content = {}
for d in ['lands', 'rules', 'laws', 'cases']:
    dpath = os.path.join(VAULT, d)
    for fname in os.listdir(dpath):
        if fname.endswith('.md'):
            p = os.path.join(dpath, fname)
            all_content[f'{d}/{fname}'] = read_md(p)

total_links = sum(
    len(re.findall(r'\[\[', c)) for c in all_content.values()
)
has_links = sum(1 for c in all_content.values() if '[[' in c)
print(f'  總連結數：{total_links}')
print(f'  有連結的檔案：{has_links}/{len(all_content)}')
print(f'  孤島（無連結）：{len(all_content) - has_links}')
print('\n✅ 完成！')
