@echo off
chcp 65001 >nul
echo ================================================
echo  土地評估系統 — 環境安裝腳本
echo ================================================
echo.

REM 建立 venv
echo [1/3] 建立 Python 虛擬環境...
python -m venv venv
if errorlevel 1 (
    echo 錯誤：找不到 Python，請先安裝 Python 3.11+
    pause & exit /b 1
)

REM 安裝套件
echo.
echo [2/3] 安裝套件（geopandas / lancedb / sentence-transformers / anthropic）...
venv\Scripts\python.exe -m pip install --upgrade pip --quiet
venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 (
    echo 錯誤：套件安裝失敗，請檢查網路或 requirements.txt
    pause & exit /b 1
)

REM 預下載 embedding 模型
echo.
echo [3/3] 下載 Embedding 模型（首次約 90 MB）...
venv\Scripts\python.exe -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2'); print('模型就緒')"

echo.
echo ================================================
echo  安裝完成！
echo.
echo  啟動方式：
echo    監聽 Excel 變更  ^> python scripts/watch_excel.py
echo    自動推送 GitHub  ^> python scripts/auto_push.py
echo    重新匯入資料庫   ^> python scripts/import_excel.py
echo ================================================
pause
