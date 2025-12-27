# Инструкция по подключению к GitHub

## Шаг 1: Создайте репозиторий на GitHub

1. Перейдите на https://github.com/new
2. **Repository name**: `CompSite_Analyz`
3. **Описание** (опционально): "Веб-приложение для анализа корпоративных сайтов с использованием AI-агентов CrewAI"
4. Выберите **Public** или **Private**
5. **НЕ** добавляйте README, .gitignore или лицензию (они уже есть в проекте)
6. Нажмите **"Create repository"**

## Шаг 2: Выполните команды в терминале

Откройте терминал (PowerShell или CMD) в папке проекта и выполните:

### Если Git репозиторий еще не инициализирован:

```bash
# Инициализация репозитория
git init

# Добавление всех файлов
git add .

# Создание первого коммита
git commit -m "Initial commit: Company Site Analyzer with CrewAI"

# Настройка основной ветки
git branch -M main

# Подключение к GitHub (замените YOUR_USERNAME на ваш GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/CompSite_Analyz.git

# Отправка кода на GitHub
git push -u origin main
```

### Если Git репозиторий уже инициализирован:

```bash
# Проверка статуса
git status

# Добавление всех файлов
git add .

# Создание коммита (если есть изменения)
git commit -m "Update: Refactored code and added Docker support"

# Подключение к GitHub (если еще не подключен)
git remote add origin https://github.com/YOUR_USERNAME/CompSite_Analyz.git

# Или обновление URL (если уже подключен)
git remote set-url origin https://github.com/YOUR_USERNAME/CompSite_Analyz.git

# Отправка кода на GitHub
git push -u origin main
```

## Шаг 3: Проверка

После выполнения команд проверьте:
- Откройте https://github.com/YOUR_USERNAME/CompSite_Analyz
- Убедитесь, что все файлы загружены

## Альтернативный способ (через скрипт)

Запустите файл `push_git.bat` двойным кликом. Он автоматически выполнит все необходимые шаги.

## Важные замечания

- **НЕ коммитьте** файл `.env` с API ключами (он уже в .gitignore)
- **НЕ коммитьте** файлы `task_*.md` (результаты анализа, уже в .gitignore)
- **НЕ коммитьте** папку `__pycache__` (кэш Python, уже в .gitignore)
- **НЕ коммитьте** папку `logs/` (логи приложения, уже в .gitignore)
- **НЕ коммитьте** файлы `.cursor/debug.log` (логи отладки, уже в .gitignore)

## Если возникли проблемы

### Ошибка: "remote origin already exists"
```bash
git remote remove origin
git remote add origin https://github.com/YOUR_USERNAME/CompSite_Analyz.git
```

### Ошибка аутентификации
Используйте Personal Access Token вместо пароля:
1. GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Создайте новый token с правами `repo`
3. Используйте token как пароль при push

### Ошибка: "failed to push some refs"
```bash
git pull origin main --allow-unrelated-histories
git push -u origin main
```

