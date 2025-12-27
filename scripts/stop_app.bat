@echo off
REM Скрипт для принудительного завершения приложения Company Analyzer
cd /d "%~dp0"
python stop_app.py
pause

