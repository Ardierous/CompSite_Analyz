# CrewAI установлен на VPS - дальнейшие шаги

## ✅ Статус: CrewAI версия 1.7.2 установлена

Отлично! CrewAI установлен на VPS. Теперь нужно проверить, что все работает корректно.

---

## 🔍 Шаг 1: Полная диагностика

Запустите скрипт диагностики на VPS:

```bash
ssh Service
cd ~/Company  # или ваш путь к проекту
python check_crewai.py
```

Скрипт проверит:
- ✅ Версию Python
- ✅ Установку CrewAI (уже подтверждено: 1.7.2)
- ✅ Доступность модулей (Agent, Task, Crew, Process)
- ✅ Доступность Tools (ScrapeWebsiteTool)
- ✅ Переменные окружения (.env файл)
- ✅ Импорт Agents_crew и создание объекта crew

---

## 🔑 Шаг 2: Проверка .env файла

Убедитесь, что файл `.env` создан и содержит API ключ:

```bash
# На VPS
cat .env
```

Должно быть:
```env
OPENAI_API_KEY=sk-ваш-реальный-ключ
OPENAI_API_BASE=https://api.proxyapi.ru/openai/v1
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=False
```

**Если файла нет, создайте его:**
```bash
nano .env
# Добавьте строки выше
chmod 600 .env
```

---

## 🧪 Шаг 3: Тест импорта Agents_crew

Проверьте, что модуль Agents_crew импортируется без ошибок:

```bash
python3 << 'EOF'
try:
    from Agents_crew import crew, CREWAI_IMPORTED
    print(f"✓ Agents_crew импортирован")
    print(f"CREWAI_IMPORTED: {CREWAI_IMPORTED}")
    if crew is None:
        print("❌ crew = None (объект не создан)")
        print("\nВозможные причины:")
        print("1. Ошибка при создании агентов")
        print("2. Отсутствует OPENAI_API_KEY")
        print("3. Ошибка при создании задач")
        print("4. Ошибка при создании Crew объекта")
    else:
        print(f"✓ crew создан: {type(crew)}")
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
except Exception as e:
    print(f"❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()
EOF
```

---

## 🚀 Шаг 4: Запуск приложения

Если все проверки пройдены, запустите приложение:

```bash
# Активируйте виртуальное окружение (если используется)
source venv/bin/activate

# Запустите приложение
python main.py
```

**Ожидаемый вывод:**
```
✓ CrewAI успешно инициализирован
Запуск Flask приложения...
Сервер будет доступен по адресу: http://0.0.0.0:5000
```

---

## ❌ Если ошибка "CrewAI не доступен" все еще возникает

### Проблема 1: crew = None

**Симптомы:**
- CrewAI установлен (версия 1.7.2)
- Но `crew = None` при импорте

**Решение:**

1. **Проверьте переменные окружения:**
   ```bash
   python3 -c "import os; from dotenv import load_dotenv; load_dotenv(); print('OPENAI_API_KEY:', 'установлен' if os.getenv('OPENAI_API_KEY') else 'НЕ установлен')"
   ```

2. **Проверьте логи при импорте:**
   ```bash
   python3 -c "from Agents_crew import crew" 2>&1 | head -50
   ```

3. **Проверьте создание агентов:**
   - Откройте `Agents_crew.py`
   - Найдите сообщения об ошибках при создании агентов
   - Проверьте, что все агенты созданы успешно

### Проблема 2: Ошибка при создании агентов

**Симптомы:**
```
ОШИБКА при создании Web Scraper Agent: ...
```

**Возможные причины:**
- Неверный формат OPENAI_API_KEY
- Недоступен OPENAI_API_BASE
- Проблемы с сетью

**Решение:**
```bash
# Проверьте формат ключа
python3 -c "import os; from dotenv import load_dotenv; load_dotenv(); key = os.getenv('OPENAI_API_KEY'); print('Ключ начинается с:', key[:7] if key else 'НЕ УСТАНОВЛЕН')"
```

### Проблема 3: Ошибка импорта модулей

**Симптомы:**
```
ImportError: cannot import name 'Agent' from 'crewai'
```

**Решение:**
Версия 1.7.2 может иметь изменения в API. Проверьте:

```bash
python3 -c "from crewai import Agent, Task, Crew, Process; print('✓ Все модули доступны')"
```

Если ошибка, возможно нужно обновить код под новую версию.

---

## 🌐 Playwright на VPS (скрапинг сайтов с защитой)

Для работы на VPS (headless Linux) добавлены аргументы Chromium: `--no-sandbox`, `--disable-dev-shm-usage`.

**Без Docker (прямой запуск на VPS):**
```bash
pip install playwright
playwright install chromium
playwright install-deps   # системные зависимости для Linux
```

**С Docker:** образ уже включает Chromium. В `docker-compose.prod.yml` указано `ipc: host` для стабильности.

---

## 📋 Чек-лист диагностики

- [ ] CrewAI установлен (версия 1.7.2) ✓
- [ ] Файл `.env` создан и содержит `OPENAI_API_KEY`
- [ ] Python версия 3.9-3.11
- [ ] Все модули CrewAI импортируются (`Agent`, `Task`, `Crew`, `Process`)
- [ ] `Agents_crew` импортируется без ошибок
- [ ] Объект `crew` создан (не `None`)
- [ ] Приложение запускается без ошибок

---

## 🔧 Быстрая диагностика (одна команда)

```bash
python3 << 'EOF'
import sys
print("Python:", sys.version.split()[0])

try:
    import crewai
    print(f"CrewAI: {crewai.__version__}")
except:
    print("CrewAI: НЕ УСТАНОВЛЕН")
    sys.exit(1)

try:
    from crewai import Agent, Task, Crew
    print("Модули: ✓")
except Exception as e:
    print(f"Модули: ❌ {e}")
    sys.exit(1)

import os
from dotenv import load_dotenv
load_dotenv()
if os.getenv('OPENAI_API_KEY'):
    print("OPENAI_API_KEY: ✓")
else:
    print("OPENAI_API_KEY: ❌ НЕ УСТАНОВЛЕН")

try:
    from Agents_crew import crew
    if crew is None:
        print("crew объект: ❌ None")
    else:
        print("crew объект: ✓")
except Exception as e:
    print(f"Agents_crew: ❌ {e}")
EOF
```

---

## 📞 Если проблема не решена

1. Запустите полную диагностику: `python check_crewai.py`
2. Сохраните вывод команды выше
3. Проверьте логи при запуске: `python main.py 2>&1 | tee startup.log`
4. Проверьте файл `.cursor/debug.log` (если существует)

---

## ✅ Версия 1.7.2 - что нового

Версия 1.7.2 новее, чем указано в requirements.txt (>=0.11.2), что хорошо:
- ✅ Совместима с текущим кодом
- ✅ Может содержать исправления ошибок
- ✅ Может иметь улучшения производительности

Если возникнут проблемы совместимости, сообщите - обновим код под новую версию.

