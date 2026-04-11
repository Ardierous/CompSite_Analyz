@echo off
chcp 65001 >nul
echo ============================================================
echo 🚀 Публикация Docker образа на Docker Hub
echo ============================================================
echo.

REM Переходим в папку scripts
cd /d "%~dp0"

REM Проверяем py launcher (предпочтительно) и python (fallback)
py -3.11 --version >nul 2>&1
if %errorlevel%==0 (
    py -3.11 -u push_to_dockerhub.py
) else (
    python --version >nul 2>&1
    if errorlevel 1 (
        echo ❌ Python/py launcher не найден! Установите Python 3.11 для запуска скрипта.
        pause
        exit /b 1
    )
    python -u push_to_dockerhub.py
)

pause

