@echo off
echo ========================================
echo Настройка Git и подключение к GitHub
echo ========================================
echo.

REM Проверка наличия git
git --version >nul 2>&1
if errorlevel 1 (
    echo ОШИБКА: Git не установлен!
    echo Установите Git с https://git-scm.com/
    pause
    exit /b 1
)

echo [1/5] Инициализация Git репозитория...
if exist .git (
    echo Git репозиторий уже инициализирован
) else (
    git init
    echo Git репозиторий инициализирован
)

echo.
echo [2/5] Добавление файлов...
git add .

echo.
echo [3/5] Создание коммита...
git commit -m "Initial commit: Company Site Analyzer with CrewAI"

echo.
echo [4/5] Настройка основной ветки...
git branch -M main

echo.
echo [5/5] Подключение к GitHub...
echo.
echo ВАЖНО: Создайте репозиторий на GitHub:
echo 1. Перейдите на https://github.com/new
echo 2. Название репозитория: CompSite_Analyz
echo 3. НЕ добавляйте README, .gitignore или лицензию
echo 4. Нажмите "Create repository"
echo.
echo После создания репозитория выполните:
echo.
echo git remote add origin https://github.com/Ardierous/CompSite_Analyz.git
echo git push -u origin main
echo.
echo (Замените YOUR_USERNAME на ваш GitHub username)
echo.

pause

