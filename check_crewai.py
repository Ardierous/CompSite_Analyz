#!/usr/bin/env python3
"""
Скрипт для диагностики установки CrewAI на VPS
Используйте: python check_crewai.py
"""

import sys
import os

print("=" * 60)
print("ДИАГНОСТИКА УСТАНОВКИ CREWAI")
print("=" * 60)

# 1. Проверка версии Python
print("\n1. Проверка версии Python:")
print(f"   Версия: {sys.version}")
print(f"   Исполняемый файл: {sys.executable}")

python_version = sys.version_info
if python_version.major == 3 and 9 <= python_version.minor <= 11:
    print(f"   ✓ Python версия подходит (3.{python_version.minor})")
else:
    print(f"   ⚠️  Python версия может быть несовместима (требуется 3.9-3.11)")

# 2. Проверка установки CrewAI
print("\n2. Проверка установки CrewAI:")
try:
    import crewai
    version = crewai.__version__ if hasattr(crewai, '__version__') else 'неизвестна'
    print(f"   ✓ CrewAI установлен, версия: {version}")
    
    # Проверяем совместимость версии
    try:
        from packaging import version as pkg_version
        installed_ver = pkg_version.parse(version)
        min_ver = pkg_version.parse("0.11.2")
        if installed_ver >= min_ver:
            print(f"   ✓ Версия совместима (>= 0.11.2)")
        else:
            print(f"   ⚠️  Версия может быть устаревшей (рекомендуется >= 0.11.2)")
    except:
        # Если packaging не установлен, просто пропускаем проверку
        pass
except ImportError as e:
    print(f"   ❌ CrewAI не установлен: {e}")
    print("\n   Решение:")
    print("   pip install 'crewai[tools]>=0.11.2'")
    sys.exit(1)
except Exception as e:
    print(f"   ❌ Ошибка при импорте CrewAI: {e}")
    sys.exit(1)

# 3. Проверка основных модулей CrewAI
print("\n3. Проверка основных модулей CrewAI:")
try:
    from crewai import Agent, Task, Crew, Process
    print("   ✓ Agent импортирован")
    print("   ✓ Task импортирован")
    print("   ✓ Crew импортирован")
    print("   ✓ Process импортирован")
except ImportError as e:
    print(f"   ❌ Ошибка импорта модулей: {e}")
    sys.exit(1)
except Exception as e:
    print(f"   ❌ Ошибка: {e}")
    sys.exit(1)

# 4. Проверка CrewAI Tools
print("\n4. Проверка CrewAI Tools:")
try:
    from crewai_tools import ScrapeWebsiteTool
    print("   ✓ ScrapeWebsiteTool доступен")
except ImportError:
    print("   ⚠️  ScrapeWebsiteTool не установлен")
    print("   Решение: pip install 'crewai[tools]>=0.11.2'")
except Exception as e:
    print(f"   ⚠️  Ошибка при импорте ScrapeWebsiteTool: {e}")

# 5. Проверка переменных окружения
print("\n5. Проверка переменных окружения:")
telemetry = os.getenv("CREWAI_TELEMETRY_OPT_OUT", "не установлена")
tracing = os.getenv("CREWAI_TRACING_ENABLED", "не установлена")
print(f"   CREWAI_TELEMETRY_OPT_OUT: {telemetry}")
print(f"   CREWAI_TRACING_ENABLED: {tracing}")

openai_key = os.getenv("OPENAI_API_KEY")
openai_base = os.getenv("OPENAI_API_BASE")
if openai_key:
    print(f"   ✓ OPENAI_API_KEY установлен (длина: {len(openai_key)})")
else:
    print("   ⚠️  OPENAI_API_KEY не установлен")
if openai_base:
    print(f"   ✓ OPENAI_API_BASE установлен: {openai_base}")
else:
    print("   ℹ️  OPENAI_API_BASE не установлен (будет использован по умолчанию)")

# 6. Проверка импорта Agents_crew
print("\n6. Проверка импорта Agents_crew:")
try:
    from Agents_crew import crew, CREWAI_IMPORTED
    print(f"   ✓ Agents_crew импортирован")
    print(f"   CREWAI_IMPORTED: {CREWAI_IMPORTED}")
    if crew is None:
        print("   ❌ crew = None (объект не создан)")
        print("\n   Возможные причины:")
        print("   - Ошибка при создании агентов")
        print("   - Ошибка при создании задач")
        print("   - Ошибка при создании Crew объекта")
        print("   - Проверьте логи выше для деталей")
    else:
        print(f"   ✓ crew создан: {type(crew)}")
except ImportError as e:
    print(f"   ❌ Ошибка импорта Agents_crew: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
except Exception as e:
    print(f"   ❌ Ошибка: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# 7. Проверка других зависимостей
print("\n7. Проверка других зависимостей:")
dependencies = {
    'flask': 'Flask',
    'flask_cors': 'Flask-CORS',
    'dotenv': 'python-dotenv',
    'requests': 'requests',
    'docx': 'python-docx',
    'numpy': 'NumPy'
}

for module, name in dependencies.items():
    try:
        __import__(module)
        print(f"   ✓ {name} установлен")
    except ImportError:
        print(f"   ❌ {name} не установлен")

# 8. Итоговый результат
print("\n" + "=" * 60)
if crew is not None and CREWAI_IMPORTED:
    print("✓ ВСЕ ПРОВЕРКИ ПРОЙДЕНЫ")
    print("CrewAI готов к использованию!")
else:
    print("❌ ОБНАРУЖЕНЫ ПРОБЛЕМЫ")
    print("Проверьте вывод выше для деталей")
print("=" * 60)

