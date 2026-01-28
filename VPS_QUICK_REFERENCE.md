# Быстрая справка: VPS настройка

## 🔑 1. Передача API ключа на VPS

### Вариант А: Создание .env на VPS
```bash
ssh Service
cd ~/Company  # или ваш путь к проекту
nano .env
# Добавьте:
# OPENAI_API_KEY=sk-ваш-ключ
# OPENAI_API_BASE=https://api.proxyapi.ru/openai/v1
chmod 600 .env
```

### Вариант Б: Копирование с локального компьютера
```powershell
# На Windows (PowerShell)
scp .env Service:~/Company/
```

---

## ✅ 2. Проверка CrewAI на VPS

### Быстрая проверка (одна команда):
```bash
python3 -c "import crewai; print(f'CrewAI: {crewai.__version__}')"
```

### Полная диагностика:
```bash
# Скопируйте check_crewai.py на VPS, затем:
python check_crewai.py
```

### Ручная проверка:
```bash
pip list | grep crewai
pip show crewai
```

---

## 📦 Установка CrewAI (если не установлен)

```bash
source venv/bin/activate  # если используете venv
pip install --upgrade pip
pip install 'crewai[tools]>=0.11.2'
python check_crewai.py  # проверка
```

---

## 🚀 Запуск приложения

```bash
cd ~/Company
source venv/bin/activate  # если используете venv
python main.py
```

---

## 📋 Чек-лист

- [ ] Подключился к VPS (`ssh Service`)
- [ ] Создал `.env` файл с `OPENAI_API_KEY`
- [ ] Проверил установку CrewAI (`python check_crewai.py`)
- [ ] Установил CrewAI, если нужно (`pip install 'crewai[tools]>=0.11.2'`)
- [ ] Запустил приложение (`python main.py`)

---

## 🔍 Полезные команды

```bash
# Проверка Python версии
python3 --version

# Проверка установленных пакетов
pip list

# Проверка переменных окружения
python3 -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('OPENAI_API_KEY')[:10] + '...' if os.getenv('OPENAI_API_KEY') else 'Не установлен')"

# Просмотр .env файла (первые символы ключа)
head -c 20 .env
```

---

Подробные инструкции: см. `VPS_ENV_SETUP.md`

