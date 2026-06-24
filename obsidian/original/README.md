# land-evaluation-system
土地開發評估系統

## 目錄結構

```
土開/
├── .git/                        ← Git 版本控制
└── obsidian/                    ← 所有專案資料
    ├── 土開/                    ← Obsidian Vault（知識庫）
    │   ├── lands/（342）        ← 污染場址
    │   ├── rules/（72）         ← 評估指標規則
    │   ├── laws/（44）          ← 法規全文
    │   └── cases/（5）          ← 評估案例
    ├── src/                     ← 程式碼
    │   └── layer2_compute/      ← 評估引擎、資料庫建置腳本
    ├── quartz/                  ← 靜態網站（Quartz v4）
    ├── 原始法規資料/              ← 法規 PDF（44 部）
    ├── 場址資料（套圖）.xlsx     ← 342 筆場址 GIS 套圖資料
    ├── 人工總表.xlsx             ← 場址主資料表
    ├── 評估指標表_全覆蓋.xlsx    ← 72 份評估指標表
    └── config.py                ← 設定檔
```

## 資料庫

| 資料庫 | 路徑 | 說明 |
|--------|------|------|
| SQLite | `src/layer2_compute/land.db` | 土地條件、評估規則、場址資料 |
| LanceDB | `src/layer2_compute/regulations_lancedb/` | 法規向量資料庫（RAG） |

## 本地服務

| 服務 | 網址 | 說明 |
|------|------|------|
| Quartz 知識庫 | http://localhost:8888 | 靜態網站預覽 |
| RAG 查詢介面 | http://localhost:8002 | 法規向量搜尋 |
| Datasette | http://localhost:8001 | SQLite 資料庫瀏覽 |

## 快速啟動

```bash
# 啟動 Quartz 預覽
cd obsidian/quartz && npx quartz build --serve --port 8888

# 啟動 RAG 查詢介面
cd obsidian/src/layer2_compute && /opt/anaconda3/bin/python3 rag_search.py

# 重建 LanceDB
cd obsidian/src/layer2_compute && /opt/anaconda3/bin/python3 build_lancedb.py
```
