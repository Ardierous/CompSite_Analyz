@echo off
chcp 65001 >nul
echo ============================================================
echo 🚀 Публикация Docker образа на Docker Hub
echo ============================================================
echo.

REM Проверка наличия Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не найден! Установите Python для запуска скрипта.
    pause
    exit /b 1
)

REM Запуск Python скрипта из папки scripts
cd /d "%~dp0"
python push_to_dockerhub.py

pause

