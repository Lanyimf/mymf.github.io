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
[[rules/R-001_EE-1]] [[rules/R-002_EE-2]] [[rules/R-003_EE-3]] [[rules/R-004_EE-4]] [[rules/R-005_EE-5]]
[[rules/R-006_EE-6]] [[rules/R-007_EE-7]] [[rules/R-008_EE-8]] [[rules/R-009_EE-9]] [[rules/R-010_EE-10]]

### 乙種建築用地（EB）
[[rules/R-023_EB-1]] [[rules/R-024_EB-2]] [[rules/R-025_EB-3]] [[rules/R-026_EB-4]] [[rules/R-027_EB-5]]

### 丁種建築用地（ED）
[[rules/R-043_ED-1]] [[rules/R-044_ED-2]] [[rules/R-045_ED-3]] [[rules/R-046_ED-4]]

### 水利用地（EH）
[[rules/R-051_EH-1]] [[rules/R-057_EH-7]] [[rules/R-059_EH-9]]

### 殯葬用地（EN）
[[rules/R-071_EN-5]] [[rules/R-072_EN-6]]

## 核心法規

- [[laws/L-42_非都市土地使用管制規則]]
- [[laws/L-36_農業發展條例]]
- [[laws/L-09_國土計畫法]]
- [[laws/L-10_土壤及地下水污染整治法]]
- [[laws/L-17_建築法]]
- [[laws/L-28_環境影響評估法]]

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
