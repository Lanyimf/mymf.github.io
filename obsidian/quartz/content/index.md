---
title: 土地開發評估系統
---

<div class="hero">
  <h1>土地開發評估系統</h1>
  <p>整合 342 筆場址資料、72 條評估規則與 44 部法規，協助你快速查找與評估土地開發可行性。</p>
</div>

<div class="stat-strip">
  <div class="stat-item"><span class="stat-num">342</span><span class="stat-label">場址資料</span></div>
  <div class="stat-item"><span class="stat-num">72</span><span class="stat-label">評估規則</span></div>
  <div class="stat-item"><span class="stat-num">44</span><span class="stat-label">完整法規</span></div>
  <div class="stat-item"><span class="stat-num">5</span><span class="stat-label">評估案例</span></div>
</div>

<div class="feature-cards">
  <a class="feature-card" href="找地搜尋">
    <div class="feature-icon">🔍</div>
    <div class="feature-title">找地搜尋</div>
    <p>用縣市、用地類別、列管狀態、面積等條件篩選，不用打完整句子。</p>
  </a>
  <a class="feature-card" href="用地評估">
    <div class="feature-icon">📋</div>
    <div class="feature-title">用地評估</div>
    <p>選一個地點，自動跑過全部 72 條規則，列出符合／不符合／資料不足。</p>
  </a>
</div>

## 快速查詢

<div class="rule-groups">

<div class="rule-group">
<h4>農牧用地（EE）</h4>
<div class="rule-chips">

[[rules/EE-1|EE-1]] [[rules/EE-2|EE-2]] [[rules/EE-3|EE-3]] [[rules/EE-4|EE-4]] [[rules/EE-5|EE-5]] [[rules/EE-6|EE-6]] [[rules/EE-7|EE-7]] [[rules/EE-8|EE-8]] [[rules/EE-9|EE-9]] [[rules/EE-10|EE-10]]

</div>
</div>

<div class="rule-group">
<h4>乙種建築用地（EB）</h4>
<div class="rule-chips">

[[rules/EB-1|EB-1]] [[rules/EB-2|EB-2]] [[rules/EB-3|EB-3]] [[rules/EB-4|EB-4]] [[rules/EB-5|EB-5]]

</div>
</div>

<div class="rule-group">
<h4>丁種建築用地（ED）</h4>
<div class="rule-chips">

[[rules/ED-1|ED-1]] [[rules/ED-2|ED-2]] [[rules/ED-3|ED-3]] [[rules/ED-4|ED-4]]

</div>
</div>

<div class="rule-group">
<h4>水利用地（EH）</h4>
<div class="rule-chips">

[[rules/EH-1|EH-1]] [[rules/EH-7|EH-7]] [[rules/EH-9|EH-9]]

</div>
</div>

<div class="rule-group">
<h4>國土保育用地（EN）</h4>
<div class="rule-chips">

[[rules/EN-5|EN-5]] [[rules/EN-6|EN-6]]

</div>
</div>

</div>

## 核心法規

- [[laws/非都市土地使用管制規則]]
- [[laws/農業發展條例]]
- [[laws/國土計畫法]]
- [[laws/土壤及地下水污染整治法]]
- [[laws/建築法]]
- [[laws/環境影響評估法]]

## 系統架構

```
原始法規 PDF（44部）
    ↓
LanceDB 向量資料庫（RAG）
    ↓
評估引擎（Python）← SQLite land.db（952筆條件）
    ↓
Obsidian Vault（本知識庫）
    ↓
Quartz 靜態網站
```

## 法規覆蓋狀態

- ✅ 44 部法規全部有完整條文
- ✅ 44 部全部被 rules/ 引用
- ✅ 72 個評估代號全部有硬性門檻
- ✅ 無斷連連結、無孤島法規
