@echo off
chcp 65001 >nul
echo ================================================
echo  設定每日報告排程（每天 08:00 發送到 Discord）
echo ================================================

set TASK_NAME=LandEval_DailyReport
set SCRIPT=%~dp0scripts\daily_report.py
set PYTHON=python

REM 先刪除舊排程（若存在）
schtasks /delete /tn "%TASK_NAME%" /f 2>nul

REM 建立新排程：每天 08:00，僅在登入時執行
schtasks /create ^
  /tn "%TASK_NAME%" ^
  /tr "cmd /c \"cd /d %~dp0 && set PYTHONUTF8=1 && %PYTHON% %SCRIPT% >> %~dp0logs\daily_report.log 2>&1\"" ^
  /sc DAILY ^
  /st 08:00 ^
  /ru "%USERNAME%" ^
  /rl HIGHEST ^
  /f

if %errorlevel%==0 (
    echo.
    echo ✅ 排程建立成功！
    echo    任務名稱：%TASK_NAME%
    echo    執行時間：每天 08:00
    echo    記錄檔：logs\daily_report.log
    echo.
    echo 請記得先建立 .env 檔並填入 DISCORD_BOT_TOKEN
) else (
    echo.
    echo ❌ 排程建立失敗，請用系統管理員身份執行
)

mkdir "%~dp0logs" 2>nul
pause
