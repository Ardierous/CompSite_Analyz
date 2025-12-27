@echo off
REM ========================================
REM Скрипт для отправки кода в GitHub
REM Запускает Python скрипт push_to_github.py
REM ========================================

REM Установка кодировки UTF-8 для правильного отображения кириллицы
chcp 65001 >nul 2>&1

echo ========================================
echo Отправка кода в GitHub
echo ========================================
echo.
echo Запуск Python скрипта для отправки кода...
echo.

REM Запуск Python скрипта из папки scripts
cd /d "%~dp0"
py -3.11 push_to_github.py

if errorlevel 1 (
    echo.
    echo ОШИБКА при выполнении скрипта!
    echo.
    echo Убедитесь, что:
    echo   1. Python 3.11 установлен
    echo   2. Git установлен
    echo   3. Репозиторий создан на GitHub
    echo.
    pause
    exit /b 1
)

echo.
pause

