from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import os
import threading
from datetime import datetime
from urllib.parse import urlparse
import warnings
import io
import requests
import json
from pathlib import Path
import sys
import platform
import subprocess
import socket
import atexit
import signal
import unicodedata
warnings.filterwarnings('ignore')

# Путь к PID файлу
PID_FILE = Path(__file__).parent / '.app.pid'

# ANSI коды для цветного вывода в терминале
class Colors:
    """ANSI escape коды для цветного вывода"""
    GREEN = '\033[92m'  # Зеленый
    RED = '\033[91m'    # Красный
    YELLOW = '\033[93m' # Желтый
    BLUE = '\033[94m'   # Синий
    RESET = '\033[0m'   # Сброс цвета
    BOLD = '\033[1m'    # Жирный

def print_green(text):
    """Выводит текст зеленым цветом"""
    print(f"{Colors.GREEN}{text}{Colors.RESET}")

def print_red(text):
    """Выводит текст красным цветом"""
    print(f"{Colors.RED}{text}{Colors.RESET}")

def print_yellow(text):
    """Выводит текст желтым цветом"""
    print(f"{Colors.YELLOW}{text}{Colors.RESET}")

def print_blue(text):
    """Выводит текст синим цветом"""
    print(f"{Colors.BLUE}{text}{Colors.RESET}")

def is_running_in_docker():
    """Проверяет, запущено ли приложение в контейнере Docker"""
    # Проверяем наличие файла /.dockerenv (стандартный способ)
    if Path('/.dockerenv').exists():
        return True
    # Проверяем переменную окружения (если установлена)
    if os.getenv('DOCKER_CONTAINER') == 'true':
        return True
    # Проверяем cgroup (альтернативный способ)
    try:
        with open('/proc/self/cgroup', 'r') as f:
            if 'docker' in f.read():
                return True
    except:
        pass
    return False

def check_port_in_use(host, port):
    """Проверяет, занят ли порт"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = sock.connect_ex((host, port))
    sock.close()
    return result == 0

def is_process_running(pid):
    """Проверяет, запущен ли процесс с указанным PID"""
    try:
        if platform.system() == 'Windows':
            result = subprocess.run(
                ['tasklist', '/FI', f'PID eq {pid}'],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
            return str(pid) in result.stdout
        else:
            # Linux/Mac: используем kill -0 для проверки существования процесса
            result = subprocess.run(['kill', '-0', str(pid)], capture_output=True)
            return result.returncode == 0
    except:
        return False

def kill_process(pid):
    """Завершает процесс с указанным PID"""
    try:
        if platform.system() == 'Windows':
            subprocess.run(
                ['taskkill', '/F', '/PID', str(pid)],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
        else:
            subprocess.run(['kill', '-9', str(pid)], capture_output=True)
        return True
    except Exception as e:
        logger.warning(f"Не удалось завершить процесс {pid}: {e}")
        return False

def kill_process_on_port(port, exclude_pid=None):
    """Завершает все процессы, использующие указанный порт
    
    Args:
        port: Порт для проверки
        exclude_pid: PID процесса, который нужно исключить из проверки (текущий процесс)
    """
    # В контейнере Docker не проверяем порт - Docker сам управляет портами
    if is_running_in_docker():
        logger.info("Запуск в контейнере Docker - пропускаем проверку порта")
        return False
    
    if exclude_pid is None:
        exclude_pid = os.getpid()  # Исключаем текущий процесс
    
    killed_count = 0
    try:
        if platform.system() == 'Windows':
            # Windows: используем netstat и taskkill
            # Сначала получаем все PID процессов на порту
            result = subprocess.run(
                ['netstat', '-ano'],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
            pids_to_kill = set()
            for line in result.stdout.split('\n'):
                if f':{port}' in line and 'LISTENING' in line:
                    parts = line.split()
                    if len(parts) > 4:
                        pid = parts[-1]
                        if pid.isdigit():
                            pids_to_kill.add(pid)
            
            # Завершаем все найденные процессы
            for pid in pids_to_kill:
                if kill_process(pid):
                    logger.info(f"Завершен процесс с PID {pid}, занимавший порт {port}")
                    print_red(f"✓ Завершен процесс с PID {pid}, занимавший порт {port}")
                    killed_count += 1
        else:
            # Linux/Mac: используем ss или netstat (более универсально, чем lsof)
            # Сначала пробуем ss (более современная утилита)
            result = subprocess.run(
                ['ss', '-tlnp'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                # Парсим вывод ss
                import re
                for line in result.stdout.split('\n'):
                    if f':{port}' in line and 'LISTEN' in line:
                        # Извлекаем PID из строки (формат: pid=12345)
                        pid_match = re.search(r'pid=(\d+)', line)
                        if pid_match:
                            pid = pid_match.group(1)
                            # Исключаем текущий процесс и его дочерние процессы
                            if pid != str(exclude_pid) and kill_process(pid):
                                logger.info(f"Завершен процесс с PID {pid}, занимавший порт {port}")
                                print_red(f"✓ Завершен процесс с PID {pid}, занимавший порт {port}")
                                killed_count += 1
            else:
                # Если ss недоступен, пробуем netstat
                result = subprocess.run(
                    ['netstat', '-tlnp'],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if f':{port}' in line and 'LISTEN' in line:
                            parts = line.split()
                            # PID обычно в последнем столбце, формат: 12345/python
                            if len(parts) > 0:
                                last_part = parts[-1]
                                pid = last_part.split('/')[0]
                                if pid.isdigit() and pid != str(exclude_pid):
                                    # Исключаем текущий процесс и его дочерние процессы
                                    if kill_process(pid):
                                        logger.info(f"Завершен процесс с PID {pid}, занимавший порт {port}")
                                        print_red(f"✓ Завершен процесс с PID {pid}, занимавший порт {port}")
                                        killed_count += 1
    except Exception as e:
        logger.error(f"Ошибка при попытке завершить процесс на порту {port}: {e}")
        print(f"⚠ Предупреждение: не удалось автоматически завершить процесс на порту {port}")
    
    return killed_count > 0

def check_and_kill_existing_instance():
    """Проверяет наличие запущенного экземпляра приложения и завершает его"""
    if not PID_FILE.exists():
        return True  # PID файл не существует, приложение не запущено
    
    try:
        # Читаем PID из файла
        with open(PID_FILE, 'r') as f:
            old_pid_str = f.read().strip()
            if not old_pid_str:
                # Пустой файл, удаляем его
                PID_FILE.unlink()
                return True
            old_pid = int(old_pid_str)
        
        # Проверяем, запущен ли процесс
        if is_process_running(old_pid):
            logger.warning(f"Обнаружен запущенный экземпляр приложения (PID: {old_pid}). Принудительно завершаю...")
            print_yellow(f"⚠ Обнаружен запущенный экземпляр приложения (PID: {old_pid}). Принудительно завершаю...")
            
            # Принудительно завершаем процесс
            if kill_process(old_pid):
                logger.info(f"Предыдущий экземпляр приложения (PID: {old_pid}) успешно завершен")
                print_red(f"✓ Предыдущий экземпляр приложения (PID: {old_pid}) успешно завершен")
                # Ждем немного, чтобы процесс завершился
                import time
                time.sleep(2)  # Увеличено время ожидания
                
                # Проверяем еще раз, что процесс действительно завершен
                if is_process_running(old_pid):
                    logger.warning(f"Процесс {old_pid} все еще запущен после попытки завершения. Повторная попытка...")
                    print_yellow(f"⚠ Процесс {old_pid} все еще запущен. Повторная попытка завершения...")
                    kill_process(old_pid)
                    time.sleep(1)
            else:
                logger.error(f"Не удалось завершить предыдущий экземпляр (PID: {old_pid})")
                print_red(f"❌ Не удалось завершить предыдущий экземпляр (PID: {old_pid})")
                return False
        else:
            # Процесс не запущен, но PID файл остался (возможно, аварийное завершение)
            logger.info(f"PID файл найден, но процесс {old_pid} не запущен. Удаляю старый PID файл.")
            print(f"ℹ Обнаружен старый PID файл (процесс не запущен). Очищаю...")
        
        # Удаляем старый PID файл
        try:
            PID_FILE.unlink()
        except:
            pass
        
        return True
    except ValueError:
        # Неверный формат PID файла
        logger.warning("PID файл содержит неверные данные. Удаляю...")
        try:
            PID_FILE.unlink()
        except:
            pass
        return True
    except Exception as e:
        logger.error(f"Ошибка при проверке существующего экземпляра: {e}")
        # Пытаемся удалить поврежденный PID файл
        try:
            PID_FILE.unlink()
        except:
            pass
        return True  # Продолжаем запуск, даже если не удалось проверить

def create_pid_file():
    """Создает PID файл с текущим PID процесса"""
    try:
        current_pid = os.getpid()
        with open(PID_FILE, 'w') as f:
            f.write(str(current_pid))
        logger.info(f"Создан PID файл: {PID_FILE} (PID: {current_pid})")
    except Exception as e:
        logger.error(f"Не удалось создать PID файл: {e}")

def remove_pid_file():
    """Удаляет PID файл при завершении приложения"""
    try:
        if PID_FILE.exists():
            PID_FILE.unlink()
            logger.info("PID файл удален")
    except Exception as e:
        logger.error(f"Не удалось удалить PID файл: {e}")

# ВАЖНО: Отключаем телеметрию CrewAI ДО загрузки переменных окружения
# Это должно быть сделано как можно раньше, до импорта Agents_crew
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "1"
os.environ["CREWAI_TRACING_ENABLED"] = "false"

# Загрузка переменных окружения из .env файла
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # Если python-dotenv не установлен, используем только переменные окружения системы
    pass

# Убеждаемся, что телеметрия отключена (на случай, если .env переопределил значения)
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "1"
os.environ["CREWAI_TRACING_ENABLED"] = "false"

# Вспомогательная функция для записи в debug.log (опционально)
def update_progress_safely(task_id, new_progress, message=None):
    """
    Безопасно обновляет прогресс задачи, гарантируя, что он только увеличивается
    
    Args:
        task_id: ID задачи
        new_progress: Новое значение прогресса (0-100)
        message: Опциональное сообщение для обновления
    """
    if task_id not in analysis_status:
        return
    
    current_prog = analysis_status[task_id].get('progress', 0)
    final_progress = max(current_prog, min(new_progress, 100))
    analysis_status[task_id]['progress'] = final_progress
    
    if message:
        analysis_status[task_id]['message'] = message

def write_debug_log(data):
    """Безопасно записывает данные в debug.log, если файл доступен"""
    try:
        debug_log_path = os.getenv('DEBUG_LOG_PATH')
        if not debug_log_path:
            # Пытаемся использовать путь по умолчанию, если он существует
            default_path = Path(__file__).parent / '.cursor' / 'debug.log'
            if default_path.parent.exists():
                debug_log_path = str(default_path)
            else:
                return  # Не записываем, если путь недоступен
        
        with open(debug_log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(data) + '\n')
    except:
        pass  # Игнорируем ошибки записи в debug.log

try:
    from docx import Document
    from docx.shared import Pt, RGBColor, Inches
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

import re


# Символы и эмодзи, которые часто используются как маркеры списка (буллиты)
_BULLET_CHARS = (
    '•', '●', '○', '▪', '▫', '◦', '∙', '►', '⬤', '➤', '→',
    '🟢', '🔵', '🔴', '🟡', '⬜', '🟦', '🟥', '⭐', '✅', '❌', '❗', '▪️',
)


def _strip_leading_bullet_chars(text):
    """Убирает из начала текста все символы-буллиты (• ✅ и т.д.), чтобы в DOCX оставался только читаемый текст."""
    if not text or not text.strip():
        return text.strip()
    t = text.strip()
    while t:
        found = False
        for sym in sorted(_BULLET_CHARS, key=lambda s: -len(s)):
            if t.startswith(sym):
                t = t[len(sym):].lstrip()
                found = True
                break
        if not found:
            break
    return t


def _replace_md_images(text):
    """Заменяет синтаксис картинок ![alt](url) на текст (alt или [изображение]), чтобы не ломать буллиты."""
    return re.sub(r'!\[([^\]]*)\]\([^)]+\)', lambda m: ('[' + m.group(1) + ']') if m.group(1).strip() else '[изображение]', text)


def _line_starts_with_emoji_bullet(stripped):
    """Проверяет, начинается ли строка с эмодзи/символа-буллета и продолжается текстом."""
    if not stripped or len(stripped) < 2:
        return False, None
    # Сравниваем с более длинными маркерами первыми (▪️ до ▪)
    for sym in sorted(_BULLET_CHARS, key=lambda s: -len(s)):
        if stripped.startswith(sym):
            rest = stripped[len(sym):].lstrip()
            if rest or sym in ('•', '●', '○', '▪', '▫'):
                return True, rest
            return False, None
    # Один символ из категории "Symbol, other" (эмодзи, спецсимволы) + пробелы + текст
    import unicodedata
    first = stripped[0]
    if ord(first) > 0x1F and not first.isalnum() and first not in '#*-`':
        if unicodedata.category(first) == 'So' and len(stripped) > 1:
            rest = stripped[1:].lstrip()
            if rest:
                return True, rest
    return False, None


def _add_inline_formatted(paragraph, text):
    """Добавляет в параграф текст с поддержкой **жирный**, *курсив*, `код`; картинки заменяются на подпись."""
    text = _replace_md_images(text)
    # Простой разбор **bold** и *italic* по очереди (без конфликта с [])
    pattern = r'(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|[^*`]+)'
    for part in re.findall(pattern, text):
        if part.startswith('**') and part.endswith('**'):
            run = paragraph.add_run(part[2:-2] + ' ')
            run.bold = True
        elif part.startswith('*') and part.endswith('*') and len(part) > 1:
            run = paragraph.add_run(part[1:-1] + ' ')
            run.italic = True
        elif part.startswith('`') and part.endswith('`'):
            run = paragraph.add_run(part[1:-1] + ' ')
            run.font.name = 'Consolas'
        else:
            paragraph.add_run(part)


def _get_line_type(stripped):
    """Определяет тип строки: heading, list или para. Для решения, вставлять ли пустую строку."""
    if not stripped:
        return None
    if re.match(r'^#{1,6}\s+', stripped):
        return 'heading'
    if re.match(r'^[-*]\s+', stripped) or re.match(r'^\d+\.\s+', stripped):
        return 'list'
    if _line_starts_with_emoji_bullet(stripped)[0]:
        return 'list'
    return 'para'


def _md_to_docx_content(doc, md_text):
    """Заполняет документ python-docx контентом из Markdown."""
    style = doc.styles['Normal']
    style.font.name = 'Calibri'
    style.font.size = Pt(11)
    lines = md_text.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    i = 0
    in_fence = False
    fence_char = None
    code_lines = []
    last_type = None
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith('```'):
            if not in_fence:
                in_fence = True
                fence_char = '```'
                code_lines = []
            else:
                # Конец блока кода
                if code_lines:
                    p = doc.add_paragraph()
                    p.style = 'Normal'
                    run = p.add_run('\n'.join(code_lines))
                    run.font.name = 'Consolas'
                    run.font.size = Pt(10)
                in_fence = False
            i += 1
            last_type = 'code'
            continue
        if in_fence:
            code_lines.append(line)
            i += 1
            continue
        stripped = line.strip()
        if not stripped:
            # Пустые строки:
            # - не вставляем вокруг заголовков (до и после)
            # - не вставляем между пунктами списка
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            next_stripped = lines[j].strip() if j < len(lines) else ''
            next_type = _get_line_type(next_stripped) if next_stripped else None
            add_blank = len(doc.paragraphs) > 0
            # Вокруг заголовков пустую строку не добавляем вовсе
            if add_blank and (last_type == 'heading' or next_type == 'heading'):
                add_blank = False
            # Между пунктами списка (и список↔заголовок) пустые строки не нужны
            if add_blank and last_type == 'list' and next_type in ('list', 'heading'):
                add_blank = False
            if add_blank:
                doc.add_paragraph()
            i = j
            continue
        # Заголовки # ## ###
        m = re.match(r'^(#{1,6})\s+(.+)$', stripped)
        if m:
            level = min(len(m.group(1)), 4)  # 1–4 для Heading 1–4
            doc.add_heading(m.group(2).strip(), level=level)
            i += 1
            last_type = 'heading'
            continue
        # Нумерованный список
        if re.match(r'^\d+\.\s+', stripped):
            text = _strip_leading_bullet_chars(re.sub(r'^\d+\.\s+', '', stripped))
            p = doc.add_paragraph(style='List Number')
            _add_inline_formatted(p, text)
            i += 1
            last_type = 'list'
            continue
        # Маркированный список - или *
        if re.match(r'^[-*]\s+', stripped) or re.match(r'^\s{0,3}[-*]\s+', line):
            text = _strip_leading_bullet_chars(re.sub(r'^\s*[-*]\s+', '', stripped))
            p = doc.add_paragraph(style='List Bullet')
            _add_inline_formatted(p, text)
            i += 1
            last_type = 'list'
            continue
        # Буллеты-эмодзи/символы (🟢 текст, • пункт и т.п.) — тот же List Bullet, все маркеры убираем
        is_emoji_bullet, rest = _line_starts_with_emoji_bullet(stripped)
        if is_emoji_bullet and rest:
            rest = _strip_leading_bullet_chars(rest)
            p = doc.add_paragraph(style='List Bullet')
            _add_inline_formatted(p, rest)
            i += 1
            last_type = 'list'
            continue
        # Строка только с картинкой (часто под буллетом) — дописываем к предыдущему параграфу
        if re.fullmatch(r'\s*!\[[^\]]*\]\([^)]+\)\s*', stripped) and len(doc.paragraphs) > 0:
            last_p = doc.paragraphs[-1]
            last_p.add_run(' ')
            _add_inline_formatted(last_p, stripped)
            i += 1
            continue
        # Обычный параграф
        p = doc.add_paragraph()
        _add_inline_formatted(p, stripped)
        i += 1
        last_type = 'para'
    return doc

# Импорт модулей логирования и отслеживания расходов
try:
    from logger import logger
except ImportError:
    import logging
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

try:
    from cost_tracker import get_balance, calculate_analysis_cost
    COST_TRACKING_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Модуль отслеживания расходов не доступен: {e}")
    COST_TRACKING_AVAILABLE = False

# #region agent log
try:
    import json
    from pathlib import Path
    debug_log_path = Path(__file__).parent / '.cursor' / 'debug.log'
    with open(debug_log_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps({"sessionId":"debug-session","runId":"init","hypothesisId":"E","location":"main.py:64","message":"Попытка импорта Agents_crew","data":{"timestamp":__import__('datetime').datetime.now().isoformat()}})+'\n')
except: pass
# #endregion
# Проверяем, что это дочерний процесс Flask reloader (рабочий сервер)
# WERKZEUG_RUN_MAIN устанавливается Flask только в дочернем процессе
# В основном процессе не импортируем crew, чтобы избежать ошибок
is_werkzeug_main = os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'

# Импортируем crew только в дочернем процессе или если debug отключен
if is_werkzeug_main or not FLASK_DEBUG:
    try:
        from Agents_crew import crew
        # #region agent log
        try:
            with open(debug_log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"init","hypothesisId":"E","location":"main.py:72","message":"Agents_crew импортирован","data":{"crew_is_none":crew is None,"crew_type":str(type(crew)) if crew else None,"timestamp":__import__('datetime').datetime.now().isoformat()}})+'\n')
        except: pass
        # #endregion
        if crew is None:
            error_msg = "CrewAI не доступен. Проверьте установку зависимостей."
            logger.error(error_msg)
            print(f"ОШИБКА: {error_msg}")
            print("\nДиагностика:")
            # Проверяем, что именно пошло не так
            try:
                from Agents_crew import CREWAI_IMPORTED
                if not CREWAI_IMPORTED:
                    print("  ❌ CrewAI модуль не импортирован")
                    print("  Решение: pip install 'crewai[tools]>=0.11.2'")
                else:
                    print("  ⚠️  CrewAI импортирован, но объект crew не создан")
                    print("  Возможные причины:")
                    print("    - Ошибка при создании агентов")
                    print("    - Ошибка при создании задач")
                    print("    - Ошибка при создании Crew объекта")
                    print("  Запустите: python check_crewai.py для детальной диагностики")
            except:
                pass
            print("\nПроверьте логи выше для детальной информации об ошибке.")
            CREW_AVAILABLE = False
        else:
            CREW_AVAILABLE = True
            logger.info("CrewAI успешно импортирован и инициализирован")
            print("✓ CrewAI успешно инициализирован")
    except ImportError as e:
        error_msg = f"Could not import crew: {e}"
        logger.error(error_msg, exc_info=True)
        print(f"ОШИБКА: {error_msg}")
        print("Возможные причины:")
        print("  1. CrewAI не установлен: pip install crewai>=0.11.2")
        print("  2. Отсутствуют зависимости CrewAI")
        print("  3. Проблема с импортом модуля Agents_crew.py")
        CREW_AVAILABLE = False
        crew = None
    except Exception as e:
        error_msg = f"Ошибка при инициализации CrewAI: {e}"
        logger.error(error_msg, exc_info=True)
        print(f"ОШИБКА: {error_msg}")
        import traceback
        print("Детальная информация об ошибке:")
        traceback.print_exc()
        CREW_AVAILABLE = False
        crew = None
else:
    # В основном процессе Flask reloader не импортируем crew
    CREW_AVAILABLE = True  # Устанавливаем True, чтобы приложение запустилось
    crew = None  # crew будет импортирован в дочернем процессе

app = Flask(__name__)
CORS(app)

# Конфигурация
FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'

# Хранилище результатов анализа (в продакшене использовать Redis или БД)
analysis_results = {}
analysis_status = {}
analysis_costs = {}  # Хранилище расходов по задачам

@app.route('/')
def index():
    logger.info("Главная страница открыта")
    return render_template('index.html')

@app.route('/api/analyze', methods=['POST'])
def analyze():
    if not request.json:
        return jsonify({'error': 'Требуется JSON в теле запроса'}), 400
    
    data = request.json
    company_url = data.get('url', '').strip()
    
    if not company_url:
        return jsonify({'error': 'URL не может быть пустым'}), 400
    
    # Валидация и нормализация URL
    if not company_url.startswith(('http://', 'https://')):
        company_url = 'https://' + company_url
    
    # Проверка корректности URL
    try:
        parsed = urlparse(company_url)
        if not parsed.netloc:
            return jsonify({'error': 'Некорректный URL'}), 400
    except Exception:
        return jsonify({'error': 'Некорректный URL'}), 400
    
    # Генерируем уникальный ID для задачи
    task_id = datetime.now().strftime('%Y%m%d%H%M%S%f')
    
    logger.info(f"Запуск анализа для URL: {company_url} (Task ID: {task_id})")
    
    # Получаем начальный баланс для отслеживания расходов
    initial_balance = None
    if COST_TRACKING_AVAILABLE:
        try:
            initial_balance = get_balance()
            if initial_balance is not None:
                logger.info(f"Начальный баланс: {initial_balance} руб.")
            else:
                logger.warning("Не удалось получить начальный баланс. Отслеживание стоимости будет недоступно.")
        except Exception as e:
            logger.error(f"Ошибка при получении начального баланса: {e}")
            initial_balance = None
    
    # Устанавливаем статус "в процессе"
    analysis_status[task_id] = {
        'status': 'processing',
        'progress': 0,
        'message': 'Анализ запущен...',
        'cost': None,
        'initial_balance': initial_balance
    }
    
    # #region agent log
    write_debug_log({
        "sessionId": "debug-session",
        "runId": "task-created",
        "hypothesisId": "A",
        "location": "main.py:103",
        "message": "Задача создана",
        "data": {
            "task_id": task_id,
            "status": analysis_status[task_id],
            "timestamp": datetime.now().isoformat()
        }
    })
    # #endregion
    
    logger.info(f"Задача {task_id} создана в analysis_status. Всего задач: {len(analysis_status)}")
    
    # Запускаем анализ в отдельном потоке
    thread = threading.Thread(
        target=run_analysis,
        args=(task_id, company_url, initial_balance)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'task_id': task_id,
        'status': 'processing',
        'message': 'Анализ запущен'
    })

def run_analysis(task_id, company_url, initial_balance=None):
    """Выполняет анализ сайта компании"""
    try:
        logger.info(f"[{task_id}] Начало анализа для {company_url}")
        
        # Проверяем, что задача существует
        if task_id not in analysis_status:
            logger.error(f"[{task_id}] Задача не найдена в analysis_status при запуске run_analysis")
            # Создаем задачу, если её нет
            analysis_status[task_id] = {
                'status': 'processing',
                'progress': 0,
                'message': 'Инициализация анализа...',
                'cost': None,
                'initial_balance': initial_balance
            }
            logger.warning(f"[{task_id}] Задача создана в run_analysis (не должна была отсутствовать)")
        
        if not CREW_AVAILABLE:
            error_msg = "CrewAI не доступен. Проверьте установку зависимостей."
            logger.error(f"[{task_id}] {error_msg}")
            # Попробуем импортировать еще раз для диагностики
            try:
                import crewai
                logger.info(f"CrewAI модуль найден, версия: {crewai.__version__ if hasattr(crewai, '__version__') else 'неизвестна'}")
            except ImportError as e:
                logger.error(f"CrewAI модуль не установлен: {e}")
            except Exception as e:
                logger.error(f"Ошибка при проверке CrewAI: {e}")
            raise Exception(error_msg)
        
        # Проверяем доступность сайта с правильными заголовками
        try:
            if task_id in analysis_status:
                update_progress_safely(task_id, 5, 'Проверка доступности сайта...')
            else:
                logger.error(f"[{task_id}] Задача исчезла из analysis_status перед проверкой сайта")
            
            # Заголовки для имитации обычного браузера
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            response = requests.get(company_url, timeout=10, allow_redirects=True, headers=headers)
            
            # Обрабатываем разные коды ответа
            if response.status_code == 403:
                # 403 (Forbidden) - сайт может блокировать автоматические запросы, но CrewAI может справиться
                logger.warning(f"[{task_id}] Сайт вернул 403 (Forbidden). Это может быть защита от ботов. Продолжаем анализ - CrewAI может обойти защиту.")
                # Не блокируем анализ, только предупреждаем
            elif response.status_code == 404:
                raise Exception("Сайт не найден (404). Проверьте правильность URL.")
            elif response.status_code >= 500:
                raise Exception(f"Ошибка сервера (код ответа: {response.status_code}). Сайт временно недоступен.")
            elif response.status_code >= 400:
                # Другие 4xx ошибки - предупреждаем, но продолжаем
                logger.warning(f"[{task_id}] Сайт вернул код {response.status_code}. Продолжаем анализ.")
            
            logger.info(f"[{task_id}] Проверка доступности завершена, код ответа: {response.status_code}")
            
        except requests.exceptions.Timeout:
            raise Exception("Сайт не отвечает (таймаут). Проверьте правильность URL и доступность сайта.")
        except requests.exceptions.ConnectionError as e:
            error_msg = str(e)
            if "resolve" in error_msg.lower() or "Name or service not known" in error_msg:
                raise Exception("Не удалось найти сайт. Проверьте правильность URL.")
            else:
                raise Exception("Не удалось подключиться к сайту. Проверьте правильность URL и доступность сайта.")
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if "404" in error_msg or "not found" in error_msg.lower():
                raise Exception("Сайт не найден. Проверьте правильность URL.")
            else:
                # Для других ошибок предупреждаем, но не блокируем
                logger.warning(f"[{task_id}] Ошибка при проверке доступности: {error_msg}. Продолжаем анализ.")
        
        # Извлекаем название компании из URL
        parsed_url = urlparse(company_url)
        domain = parsed_url.netloc
        # Убираем www. и извлекаем основное имя домена
        domain_parts = domain.replace('www.', '').split('.')
        company_name = domain_parts[0].capitalize() if domain_parts else 'Company'
        
        logger.info(f"[{task_id}] Название компании: {company_name}")
        
        # Обновляем статус
        update_progress_safely(task_id, 10, 'Подготовка к анализу...')
        logger.info(f"[{task_id}] Этап 1: Подготовка к анализу")
        
        # Подготавливаем входные данные
        inputs = {
            "company_url": company_url,
            "company_name": company_name,
        }
        
        # Запускаем поток для плавного обновления прогресса во время выполнения CrewAI
        import time
        progress_thread_running = threading.Event()
        progress_thread_running.set()
        start_time = time.time()
        start_progress = 15
        target_progress = 88  # Увеличено до 88% для более плавного финала
        estimated_duration = 120  # Ожидаемая длительность анализа в секундах (2 минуты)
        
        def update_progress_during_analysis():
            """Плавно обновляет прогресс во время выполнения CrewAI анализа"""
            messages = [
                'Инициализация анализа...',
                'Сбор информации с сайта...',
                'Обработка данных...',
                'Анализ структуры компании...',
                'Анализ продуктов и услуг...',
                'Анализ финансовых показателей...',
                'Анализ стратегических направлений...',
                'Формирование аналитического отчета...',
                'Структурирование данных...',
                'Финальная обработка...',
            ]
            message_index = 0
            
            last_progress = start_progress  # Отслеживаем последнее значение прогресса
            
            while progress_thread_running.is_set():
                if task_id not in analysis_status or analysis_status[task_id]['status'] != 'processing':
                    break
                
                elapsed_time = time.time() - start_time
                
                # Более равномерное линейное увеличение прогресса
                if elapsed_time < estimated_duration:
                    # Линейное увеличение для равномерности
                    progress_ratio = min(elapsed_time / estimated_duration, 1.0)
                    # Используем слегка ускоренную функцию для более естественного движения
                    # Комбинация линейной и квадратичной для плавности без замедления в начале
                    smooth_ratio = progress_ratio * (0.3 + 0.7 * progress_ratio)  # 30% линейная + 70% квадратичная
                    calculated_progress = int(start_progress + (target_progress - start_progress) * smooth_ratio)
                else:
                    # Если прошло больше времени, медленно приближаемся к target_progress
                    extra_time = elapsed_time - estimated_duration
                    # Медленное увеличение после истечения ожидаемого времени
                    additional_progress = min(int(extra_time / 10), target_progress - start_progress)
                    calculated_progress = min(start_progress + additional_progress, target_progress)
                
                # ВАЖНО: Прогресс может только увеличиваться, никогда не уменьшаться
                # Используем max, чтобы гарантировать монотонное увеличение
                current_progress = max(last_progress, calculated_progress)
                last_progress = current_progress  # Сохраняем для следующей итерации
                
                # Обновляем сообщение каждые ~12 секунд (10 сообщений за ~120 секунд)
                if elapsed_time > 0:
                    new_message_index = min(int(elapsed_time / (estimated_duration / len(messages))), len(messages) - 1)
                    if new_message_index != message_index:
                        message_index = new_message_index
                
                if task_id in analysis_status and analysis_status[task_id]['status'] == 'processing':
                    update_progress_safely(task_id, current_progress, messages[message_index])
                
                time.sleep(1)  # Обновляем каждую секунду для плавности
        
        progress_thread = threading.Thread(target=update_progress_during_analysis)
        progress_thread.daemon = True
        progress_thread.start()
        
        # Запускаем анализ
        update_progress_safely(task_id, 15, 'Запуск анализа...')
        logger.info(f"[{task_id}] Этап 2: Запуск CrewAI анализа")
        
        # #region agent log
        write_debug_log({
            "sessionId": "debug-session",
            "runId": "pre-kickoff",
            "hypothesisId": "B",
            "location": "main.py:142",
            "message": "Перед вызовом crew.kickoff()",
            "data": {
                "task_id": task_id,
                "timestamp": datetime.now().isoformat()
            }
        })
        # #endregion
        
        result = crew.kickoff(inputs=inputs)
        
        # Останавливаем поток обновления прогресса
        progress_thread_running.clear()
        
        # #region agent log
        write_debug_log({
            "sessionId": "debug-session",
            "runId": "post-kickoff",
            "hypothesisId": "B",
            "location": "main.py:145",
            "message": "После вызова crew.kickoff()",
            "data": {
                "task_id": task_id,
                "timestamp": datetime.now().isoformat()
            }
        })
        # #endregion
        
        logger.info(f"[{task_id}] CrewAI анализ завершен")
        
        # Плавное завершение с небольшими шагами
        update_progress_safely(task_id, 90, 'Завершение анализа...')
        logger.info(f"[{task_id}] Этап 3: Завершение анализа")
        
        import time
        time.sleep(0.5)  # Небольшая пауза для плавности
        
        # Вычисляем стоимость анализа
        update_progress_safely(task_id, 93, 'Расчет стоимости...')
        cost = None
        if COST_TRACKING_AVAILABLE and initial_balance is not None:
            cost = calculate_analysis_cost(task_id, initial_balance)
            analysis_costs[task_id] = cost
            logger.info(f"[{task_id}] Стоимость анализа: {cost} руб.")
        
        time.sleep(0.3)  # Небольшая пауза для плавности
        
        # Сохраняем результат
        update_progress_safely(task_id, 96, 'Сохранение результатов...')
        analysis_results[task_id] = {
            'result': str(result),
            'url': company_url,
            'company_name': company_name,
            'timestamp': datetime.now().isoformat(),
            'cost': cost,
            'task_id': task_id  # Добавляем task_id для экспорта
        }
        
        # Устанавливаем статус "завершено"
        analysis_status[task_id] = {
            'status': 'completed',
            'progress': 100,
            'message': 'Анализ завершен',
            'cost': cost,
            'initial_balance': initial_balance
        }
        
        logger.info(f"[{task_id}] Анализ успешно завершен. Готов к новой итерации.")
        
    except Exception as e:
        error_message = str(e)
        logger.error(f"[{task_id}] Ошибка при анализе: {error_message}", exc_info=True)
        analysis_status[task_id] = {
            'status': 'error',
            'progress': 0,
            'message': f'Ошибка: {error_message}',
            'cost': None
        }

@app.route('/api/status/<task_id>', methods=['GET'])
def get_status(task_id):
    # #region agent log
    write_debug_log({
        "sessionId": "debug-session",
        "runId": "status-check",
        "hypothesisId": "A",
        "location": "main.py:279",
        "message": "Запрос статуса задачи",
        "data": {
            "task_id": task_id,
            "exists": task_id in analysis_status,
            "all_tasks": list(analysis_status.keys())[-5:],
            "timestamp": datetime.now().isoformat()
        }
    })
    # #endregion
    
    if task_id not in analysis_status:
        logger.warning(f"Запрос статуса для несуществующей задачи: {task_id}. Доступные задачи: {list(analysis_status.keys())[-5:]}")
        return jsonify({'error': 'Задача не найдена'}), 404
    
    status = analysis_status[task_id].copy()
    
    # Если анализ завершен, добавляем результат
    if status['status'] == 'completed':
        if task_id in analysis_results:
            result_data = analysis_results[task_id].copy()
            status['result'] = result_data
            # Добавляем информацию о стоимости в статус и результат
            if 'cost' in result_data:
                cost_value = result_data['cost']
                status['cost'] = cost_value
                # Убеждаемся, что стоимость есть в результате
                if 'cost' not in result_data or result_data['cost'] is None:
                    result_data['cost'] = cost_value
            else:
                # Если стоимости нет в результате, но есть в статусе
                if 'cost' in status and status['cost'] is not None:
                    result_data['cost'] = status['cost']
            
            logger.info(f"[{task_id}] Возврат статуса: cost={status.get('cost')}, result.cost={result_data.get('cost')}")
    
    return jsonify(status)

@app.route('/api/export/<task_id>', methods=['GET'])
def export_to_docx(task_id):
    """Экспорт результатов анализа в DOCX формат"""
    if task_id not in analysis_results:
        return jsonify({'error': 'Результаты анализа не найдены'}), 404
    
    if not DOCX_AVAILABLE:
        return jsonify({'error': 'Модуль python-docx не установлен'}), 500
    
    try:
        result_data = analysis_results[task_id]
        
        # Создаем документ
        doc = Document()
        
        # Настройка стилей
        style = doc.styles['Normal']
        font = style.font
        font.name = 'Calibri'
        font.size = Pt(11)
        
        # Заголовок
        title = doc.add_heading('КОМПЛЕКСНЫЙ КОРПОРАТИВНЫЙ ОТЧЕТ', 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Информация о компании
        company_name = result_data.get('company_name', 'Неизвестная компания')
        company_url = result_data.get('url', 'N/A')
        timestamp = result_data.get('timestamp', datetime.now().isoformat())
        cost = result_data.get('cost')
        
        doc.add_paragraph(f'Компания: {company_name}')
        doc.add_paragraph(f'URL: {company_url}')
        doc.add_paragraph(f'Дата анализа: {timestamp}')
        if cost is not None:
            doc.add_paragraph(f'Стоимость анализа: {cost:.4f} руб.')
        
        doc.add_paragraph()  # Пустая строка
        
        # Основной контент — схлопываем пустые строки, распознаём списки и эмодзи-буллиты
        content = result_data.get('result', '')
        if content:
            lines = content.replace('\r\n', '\n').replace('\r', '\n').split('\n')
            i = 0
            while i < len(lines):
                line = lines[i]
                stripped = line.strip()
                if not stripped:
                    j = i + 1
                    while j < len(lines) and not lines[j].strip():
                        j += 1
                    if len(doc.paragraphs) > 6:
                        doc.add_paragraph()
                    i = j
                    continue
                if (len(stripped) < 100 and
                    (stripped.isupper() or stripped.startswith('#') or
                     any(stripped.startswith(m) for m in ['I.', 'II.', 'III.', 'IV.', 'V.', 'VI.', 'VII.', 'VIII.', 'IX.', 'X.']))):
                    doc.add_heading(stripped, level=1)
                elif re.match(r'^[-*]\s+', stripped):
                    text = _strip_leading_bullet_chars(re.sub(r'^[-*]\s+', '', stripped))
                    p = doc.add_paragraph(style='List Bullet')
                    p.add_run(text)
                else:
                    is_emoji_bullet, rest = _line_starts_with_emoji_bullet(stripped)
                    if is_emoji_bullet and rest:
                        p = doc.add_paragraph(style='List Bullet')
                        p.add_run(_strip_leading_bullet_chars(rest))
                        i += 1
                        continue
                    doc.add_paragraph(stripped)
                i += 1
        
        # Сохраняем в память
        file_stream = io.BytesIO()
        doc.save(file_stream)
        file_stream.seek(0)
        
        # Формируем имя файла
        filename = f'analysis_{company_name}_{datetime.now().strftime("%Y%m%d")}.docx'
        safe_filename = "".join(c for c in filename if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
        
        logger.info(f"Экспорт результатов {task_id} в DOCX: {safe_filename}")
        
        return send_file(
            file_stream,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            as_attachment=True,
            download_name=safe_filename
        )
        
    except Exception as e:
        logger.error(f"Ошибка при экспорте в DOCX для задачи {task_id}: {e}", exc_info=True)
        return jsonify({'error': f'Ошибка при создании документа: {str(e)}'}), 500


@app.route('/api/convert/md-to-docx', methods=['POST'])
def convert_md_to_docx():
    """Принимает MD-файл, конвертирует в DOCX и возвращает файл для скачивания."""
    if not DOCX_AVAILABLE:
        return jsonify({'error': 'Модуль python-docx не установлен'}), 500
    uploaded = request.files.get('file')
    if not uploaded or uploaded.filename == '':
        return jsonify({'error': 'Файл не выбран'}), 400
    if not (uploaded.filename.lower().endswith('.md') or (getattr(uploaded, 'content_type', '') or '').startswith('text/')):
        return jsonify({'error': 'Требуется файл Markdown (.md)'}), 400
    try:
        md_bytes = uploaded.read()
        try:
            md_text = md_bytes.decode('utf-8')
        except UnicodeDecodeError:
            md_text = md_bytes.decode('utf-8-sig')
        doc = Document()
        _md_to_docx_content(doc, md_text)
        file_stream = io.BytesIO()
        doc.save(file_stream)
        file_stream.seek(0)
        base_name = Path(uploaded.filename).stem
        safe_name = "".join(c for c in base_name if c.isalnum() or c in (' ', '-', '_')).rstrip() or 'document'
        download_name = f"{safe_name}_{datetime.now().strftime('%Y%m%d')}.docx"
        return send_file(
            file_stream,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            as_attachment=True,
            download_name=download_name,
        )
    except Exception as e:
        logger.error(f"Ошибка конвертации MD → DOCX: {e}", exc_info=True)
        return jsonify({'error': f'Ошибка конвертации: {str(e)}'}), 500


if __name__ == '__main__':
    # Проверяем, что это дочерний процесс Flask reloader (рабочий сервер)
    # WERKZEUG_RUN_MAIN устанавливается Flask только в дочернем процессе
    # Используем уже определенную переменную is_werkzeug_main из начала файла
    
    # Проверки PID файла и порта выполняем только в основном процессе
    # (до запуска reloader) или если debug отключен
    if not is_werkzeug_main or not FLASK_DEBUG:
        # Регистрируем обработчик для удаления PID файла при завершении
        atexit.register(remove_pid_file)
        
        # Обработка сигналов для корректного завершения
        def signal_handler(signum, frame):
            print_red("\n" + "=" * 60)
            print_red("Завершение работы приложения...")
            print_red("=" * 60)
            remove_pid_file()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # ШАГ 1: Проверяем наличие запущенного экземпляра приложения через PID файл
        # Это основная проверка - если приложение запущено, оно создало PID файл
        logger.info("Проверка запущенных экземпляров приложения...")
        print("Проверка запущенных экземпляров приложения...")
        if not check_and_kill_existing_instance():
            logger.error("Не удалось завершить предыдущий экземпляр приложения")
            print_red("❌ Ошибка: не удалось завершить предыдущий экземпляр приложения")
            sys.exit(1)
        
        # ========================================================================
        # ШАГ 2: Дополнительная проверка - занят ли порт
        # ========================================================================
        # В контейнере Docker пропускаем проверку порта - Docker сам управляет портами
        # В debug режиме Flask reloader создаст дочерний процесс, который займет порт - это нормально
        # Поэтому в debug режиме проверяем порт только один раз, перед запуском Flask
        if not is_running_in_docker() and not FLASK_DEBUG:
            # Проверяем порт только если debug отключен (нет Flask reloader)
            # Проверяем порт на случай, если PID файл был удален, но процесс еще работает
            # или если другой процесс использует порт 5000
            check_host = FLASK_HOST if FLASK_HOST != '0.0.0.0' else '127.0.0.1'
            import time
            
            # Проверяем порт несколько раз с попытками завершения
            # Увеличено количество попыток для более надежного освобождения порта
            max_attempts = 10
            for attempt in range(max_attempts):
                if check_port_in_use(check_host, FLASK_PORT):
                    if attempt == 0:
                        logger.warning(f"Порт {FLASK_PORT} уже занят. Принудительно завершаю предыдущий процесс...")
                        print_yellow(f"⚠ Порт {FLASK_PORT} уже занят. Принудительно завершаю предыдущий процесс...")
                    else:
                        logger.warning(f"Порт {FLASK_PORT} все еще занят (попытка {attempt + 1}/{max_attempts}). Повторная попытка завершения...")
                        print_yellow(f"⚠ Порт {FLASK_PORT} все еще занят. Повторная попытка завершения (попытка {attempt + 1}/{max_attempts})...")
                    
                    # Исключаем текущий процесс из проверки
                    kill_process_on_port(FLASK_PORT, exclude_pid=os.getpid())
                    
                    # Ждем, чтобы порт освободился (увеличено время ожидания для надежности)
                    time.sleep(3)  # Увеличено с 2 до 3 секунд
                    
                    # Проверяем снова
                    if not check_port_in_use(check_host, FLASK_PORT):
                        logger.info(f"Порт {FLASK_PORT} успешно освобожден после {attempt + 1} попыток")
                        print_green(f"✓ Порт {FLASK_PORT} успешно освобожден после {attempt + 1} попыток")
                        break
                else:
                    # Порт свободен, можно запускать
                    break
            else:
                # Все попытки исчерпаны, порт все еще занят
                logger.error(f"Порт {FLASK_PORT} все еще занят после {max_attempts} попыток завершения процесса")
                print_red(f"❌ Ошибка: порт {FLASK_PORT} все еще занят после {max_attempts} попыток.")
                print_red(f"   Закройте приложение вручную или измените порт в переменных окружения.")
                print_red(f"   Используйте скрипт scripts/stop_app.py для принудительного завершения.")
                sys.exit(1)
        elif not is_running_in_docker() and FLASK_DEBUG:
            # В debug режиме проверяем порт только один раз, перед запуском Flask
            # Flask reloader создаст дочерний процесс, который займет порт - это нормально
            # Проверяем только, не занят ли порт другим процессом (не нашим)
            check_host = FLASK_HOST if FLASK_HOST != '0.0.0.0' else '127.0.0.1'
            if check_port_in_use(check_host, FLASK_PORT):
                # Проверяем, не занят ли порт другим процессом (не нашим)
                # Исключаем текущий процесс из проверки
                killed = kill_process_on_port(FLASK_PORT, exclude_pid=os.getpid())
                if killed:
                    import time
                    time.sleep(1)  # Небольшая пауза для освобождения порта
                    logger.info("Освобожден порт от предыдущего процесса")
                    print_green("✓ Освобожден порт от предыдущего процесса")
                else:
                    # Порт занят, но это может быть наш дочерний процесс от предыдущего запуска
                    # Или другой процесс - проверяем через PID файл (уже сделано в ШАГ 1)
                    logger.info("Порт занят, но это может быть нормально в debug режиме (Flask reloader)")
                    print("ℹ Порт занят - в debug режиме Flask reloader создаст дочерний процесс")
        else:
            logger.info("Запуск в контейнере Docker - пропускаем проверку порта (Docker управляет портами)")
            print("ℹ Запуск в контейнере Docker - проверка порта не требуется")
        
        # ШАГ 3: Создаем PID файл для текущего экземпляра ПЕРЕД запуском
        # Это важно - флаг должен быть установлен до того, как приложение начнет слушать порт
        create_pid_file()
        logger.info(f"PID файл создан: {PID_FILE} (PID: {os.getpid()})")
    
    # В дочернем процессе также регистрируем обработчик для удаления PID файла
    if is_werkzeug_main:
        atexit.register(remove_pid_file)
    
    logger.info("=" * 60)
    logger.info("Запуск Flask приложения...")
    logger.info(f"Сервер будет доступен по адресу: http://{FLASK_HOST}:{FLASK_PORT}")
    logger.info("Нажмите Ctrl+C для остановки")
    logger.info("=" * 60)
    
    print_green("=" * 60)
    print_green("Запуск Flask приложения...")
    print_green(f"Сервер будет доступен по адресу: http://{FLASK_HOST}:{FLASK_PORT}")
    print_green("Нажмите Ctrl+C для остановки")
    print_green("=" * 60)
    
    # Flask reloader в debug режиме запускает приложение дважды:
    # 1. Основной процесс (parent) - только для мониторинга изменений
    # 2. Дочерний процесс (child) - рабочий сервер
    # Используем use_reloader=False, чтобы избежать двойного запуска
    # или проверяем WERKZEUG_RUN_MAIN для создания агентов только в дочернем процессе
    app.run(debug=FLASK_DEBUG, host=FLASK_HOST, port=FLASK_PORT, use_reloader=True)

