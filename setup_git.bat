@echo off
echo ========================================
echo Отправка кода в GitHub
echo ========================================
echo.
echo Запуск Python скрипта для отправки кода...
echo.

REM Запуск Python скрипта
py -3.11 push_to_github.py

if errorlevel 1 (
    echo.
    echo ОШИБКА при выполнении скрипта!
    echo Убедитесь, что:
    echo 1. Python 3.11 установлен
    echo 2. Git установлен
    echo 3. Репозиторий создан на GitHub
    echo.
    pause
    exit /b 1
)

echo.
pause

