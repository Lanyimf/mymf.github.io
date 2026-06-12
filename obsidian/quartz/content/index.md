---
title: 土地開發評估系統
---

# 土地開發評估系統 知識庫

## 結構說明

| 資料夾 | 說明 | 檔案數 |
|--------|------|--------|
| [[lands/]] | 342 筆污染場址基本資料 | 342 |
| [[rules/]] | 72 份評估指標（EE/EB/ED/EH/EG/EP/EN） | 72 |
| [[laws/]] | 44 部法規完整條文 | 44 |
| [[cases/]] | 評估案例模板 | 5 |

## 快速查詢

### 農牧用地（EE）
[[rules/EE-1]] [[rules/EE-2]] [[rules/EE-3]] [[rules/EE-4]] [[rules/EE-5]]
[[rules/EE-6]] [[rules/EE-7]] [[rules/EE-8]] [[rules/EE-9]] [[rules/EE-10]]

### 乙種建築用地（EB）
[[rules/EB-1]] [[rules/EB-2]] [[rules/EB-3]] [[rules/EB-4]] [[rules/EB-5]]

### 丁種建築用地（ED）
[[rules/ED-1]] [[rules/ED-2]] [[rules/ED-3]] [[rules/ED-4]]

### 水利用地（EH）
[[rules/EH-1]] [[rules/EH-7]] [[rules/EH-9]]

### 殯葬用地（EN）
[[rules/EN-5]] [[rules/EN-6]]

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
Quartz 靜態網站（http://localhost:8888）
```

## 法規覆蓋狀態

- ✅ 44 部法規全部有完整條文
- ✅ 44 部全部被 rules/ 引用
- ✅ 72 個評估代號全部有硬性門檻
- ✅ 無斷連連結、無孤島法規
