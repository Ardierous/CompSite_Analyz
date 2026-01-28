# Передача API ключа на VPS и проверка CrewAI

## 1. Как передать API ключ (OPENAI_API_KEY) на VPS

### Способ 1: Создание .env файла напрямую на VPS (рекомендуется)

1. **Подключитесь к VPS:**
   ```bash
   ssh Service
   # или
   ssh root@95.81.123.146
   ```

2. **Перейдите в директорию проекта:**
   ```bash
   cd /path/to/your/project
   # или
   cd ~/Company
   ```

3. **Создайте файл .env:**
   ```bash
   nano .env
   # или
   vi .env
   ```

4. **Добавьте в файл следующие строки:**
   ```env
   OPENAI_API_KEY=sk-ваш-реальный-ключ-здесь
   OPENAI_API_BASE=https://api.proxyapi.ru/openai/v1
   FLASK_HOST=0.0.0.0
   FLASK_PORT=5000
   FLASK_DEBUG=False
   ```

5. **Сохраните файл:**
   - В `nano`: `Ctrl+O` (сохранить), затем `Ctrl+X` (выйти)
   - В `vi`: `Esc`, затем `:wq` (сохранить и выйти)

6. **Установите права доступа (безопасность):**
   ```bash
   chmod 600 .env  # Только владелец может читать/писать
   ```

### Способ 2: Копирование .env файла с локального компьютера

1. **На вашем локальном компьютере (Windows):**
   ```powershell
   # Используйте SCP для копирования файла
   scp .env Service:/path/to/your/project/
   # или
   scp .env root@95.81.123.146:/path/to/your/project/
   ```

2. **Если файл .env находится в текущей директории:**
   ```powershell
   scp .env Service:~/Company/
   ```

### Способ 3: Создание .env через команду (быстрый способ)

```bash
# На VPS выполните:
cat > .env << 'EOF'
OPENAI_API_KEY=sk-ваш-реальный-ключ-здесь
OPENAI_API_BASE=https://api.proxyapi.ru/openai/v1
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=False
EOF

# Установите права доступа
chmod 600 .env
```

### Проверка, что .env файл создан правильно:

```bash
# Проверьте содержимое файла
cat .env

# Проверьте, что файл существует
ls -la .env

# Должно показать:
# -rw------- 1 root root ... .env
```

---

## 2. Как проверить установлен ли CrewAI на VPS

### Способ 1: Использование скрипта диагностики (рекомендуется)

1. **Скопируйте скрипт `check_crewai.py` на VPS:**
   ```powershell
   # На вашем локальном компьютере
   scp check_crewai.py Service:/path/to/your/project/
   ```

2. **На VPS запустите скрипт:**
   ```bash
   # Подключитесь к VPS
   ssh Service
   
   # Перейдите в директорию проекта
   cd /path/to/your/project
   
   # Активируйте виртуальное окружение (если используется)
   source venv/bin/activate
   
   # Запустите скрипт диагностики
   python check_crewai.py
   ```

3. **Скрипт покажет:**
   - Версию Python
   - Установлен ли CrewAI
   - Версию CrewAI
   - Доступность модулей
   - Переменные окружения
   - Статус импорта Agents_crew

### Способ 2: Ручная проверка через Python

```bash
# На VPS выполните:
python3 -c "import crewai; print(f'CrewAI версия: {crewai.__version__}')"

# Если установлен, увидите:
# CrewAI версия: 0.11.2 (или другая версия)

# Если не установлен, увидите:
# ModuleNotFoundError: No module named 'crewai'
```

### Способ 3: Проверка через pip

```bash
# Проверьте установленные пакеты
pip list | grep crewai

# Или
pip show crewai

# Если установлен, увидите информацию о пакете
# Если не установлен, увидите:
# WARNING: Package(s) not found: crewai
```

### Способ 4: Проверка импорта модулей

```bash
python3 << 'EOF'
try:
    from crewai import Agent, Task, Crew, Process
    print("✓ CrewAI основные модули импортированы успешно")
    
    try:
        from crewai_tools import ScrapeWebsiteTool
        print("✓ CrewAI Tools доступны")
    except ImportError:
        print("⚠️  CrewAI Tools не установлены")
        print("   Установите: pip install 'crewai[tools]>=0.11.2'")
        
except ImportError as e:
    print(f"❌ CrewAI не установлен: {e}")
    print("   Установите: pip install 'crewai[tools]>=0.11.2'")
except Exception as e:
    print(f"❌ Ошибка: {e}")
EOF
```

### Способ 5: Проверка через импорт Agents_crew

```bash
python3 << 'EOF'
try:
    from Agents_crew import crew, CREWAI_IMPORTED
    print(f"CREWAI_IMPORTED: {CREWAI_IMPORTED}")
    if crew is None:
        print("❌ crew = None (объект не создан)")
    else:
        print(f"✓ crew создан: {type(crew)}")
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
except Exception as e:
    print(f"❌ Ошибка: {e}")
EOF
```

---

## Быстрая проверка всего сразу

Создайте на VPS файл `quick_check.sh`:

```bash
cat > quick_check.sh << 'EOF'
#!/bin/bash
echo "=== Проверка Python ==="
python3 --version

echo -e "\n=== Проверка CrewAI ==="
python3 -c "import crewai; print(f'✓ CrewAI версия: {crewai.__version__}')" 2>&1

echo -e "\n=== Проверка модулей ==="
python3 -c "from crewai import Agent, Task, Crew; print('✓ Основные модули доступны')" 2>&1

echo -e "\n=== Проверка Tools ==="
python3 -c "from crewai_tools import ScrapeWebsiteTool; print('✓ Tools доступны')" 2>&1

echo -e "\n=== Проверка .env ==="
if [ -f .env ]; then
    echo "✓ Файл .env существует"
    if grep -q "OPENAI_API_KEY" .env; then
        echo "✓ OPENAI_API_KEY найден в .env"
    else
        echo "❌ OPENAI_API_KEY не найден в .env"
    fi
else
    echo "❌ Файл .env не найден"
fi

echo -e "\n=== Проверка Agents_crew ==="
python3 -c "from Agents_crew import crew; print(f'crew = {crew is not None}')" 2>&1
EOF

chmod +x quick_check.sh
./quick_check.sh
```

---

## Установка CrewAI, если он не установлен

Если проверка показала, что CrewAI не установлен:

```bash
# 1. Активируйте виртуальное окружение (если используется)
source venv/bin/activate

# 2. Обновите pip
pip install --upgrade pip

# 3. Установите CrewAI с инструментами
pip install 'crewai[tools]>=0.11.2'

# 4. Проверьте установку
python check_crewai.py
```

---

## Проверка переменных окружения

После создания .env файла проверьте, что переменные загружаются:

```bash
python3 << 'EOF'
import os
from dotenv import load_dotenv

# Загружаем .env
load_dotenv()

# Проверяем переменные
api_key = os.getenv("OPENAI_API_KEY")
api_base = os.getenv("OPENAI_API_BASE")

if api_key:
    print(f"✓ OPENAI_API_KEY установлен (длина: {len(api_key)})")
else:
    print("❌ OPENAI_API_KEY не установлен")

if api_base:
    print(f"✓ OPENAI_API_BASE: {api_base}")
else:
    print("ℹ️  OPENAI_API_BASE не установлен (будет использован по умолчанию)")
EOF
```

---

## Итоговая последовательность действий

1. **Подключитесь к VPS:**
   ```bash
   ssh Service
   ```

2. **Перейдите в директорию проекта:**
   ```bash
   cd /path/to/your/project
   ```

3. **Создайте .env файл с API ключом:**
   ```bash
   nano .env
   # Добавьте OPENAI_API_KEY=sk-...
   ```

4. **Скопируйте check_crewai.py на VPS (если еще не скопирован):**
   ```powershell
   # На локальном компьютере
   scp check_crewai.py Service:/path/to/your/project/
   ```

5. **Запустите диагностику:**
   ```bash
   python check_crewai.py
   ```

6. **Если CrewAI не установлен, установите:**
   ```bash
   pip install 'crewai[tools]>=0.11.2'
   ```

7. **Проверьте еще раз:**
   ```bash
   python check_crewai.py
   ```

8. **Запустите приложение:**
   ```bash
   python main.py
   ```

