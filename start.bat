@echo off
chcp 65001 > nul
echo ============================================================
echo   ポケモン シルエットクイズ 〜だ〜れだ？〜 (SQLite連動)
echo ============================================================
echo.
echo サーバーを起動しています...

set "PYTHON_EXE=C:\Users\cre\AppData\Local\Programs\Python\Python312\python.exe"
if not exist "%PYTHON_EXE%" (
    set "PYTHON_EXE=python"
)

start "" http://127.0.0.1:5000
"%PYTHON_EXE%" app.py
pause
