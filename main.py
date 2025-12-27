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
warnings.filterwarnings('ignore')

# Загрузка переменных окружения из .env файла
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # Если python-dotenv не установлен, используем только переменные окружения системы
    pass

# Вспомогательная функция для записи в debug.log (опционально)
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

try:
    from Agents_crew import crew
    CREW_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Could not import crew: {e}")
    CREW_AVAILABLE = False
    crew = None

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
            raise Exception("CrewAI не доступен. Проверьте установку зависимостей.")
        
        # Проверяем доступность сайта с правильными заголовками
        try:
            if task_id in analysis_status:
                analysis_status[task_id]['progress'] = 5
                analysis_status[task_id]['message'] = 'Проверка доступности сайта...'
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
        analysis_status[task_id]['progress'] = 10
        analysis_status[task_id]['message'] = 'Подготовка к анализу...'
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
                    current_progress = int(start_progress + (target_progress - start_progress) * smooth_ratio)
                else:
                    # Если прошло больше времени, медленно приближаемся к target_progress
                    extra_time = elapsed_time - estimated_duration
                    # Медленное увеличение после истечения ожидаемого времени
                    additional_progress = min(int(extra_time / 10), target_progress - start_progress)
                    current_progress = min(start_progress + additional_progress, target_progress)
                
                # Обновляем сообщение каждые ~12 секунд (10 сообщений за ~120 секунд)
                if elapsed_time > 0:
                    new_message_index = min(int(elapsed_time / (estimated_duration / len(messages))), len(messages) - 1)
                    if new_message_index != message_index:
                        message_index = new_message_index
                
                if task_id in analysis_status and analysis_status[task_id]['status'] == 'processing':
                    analysis_status[task_id]['progress'] = current_progress
                    analysis_status[task_id]['message'] = messages[message_index]
                
                time.sleep(1)  # Обновляем каждую секунду для плавности
        
        progress_thread = threading.Thread(target=update_progress_during_analysis)
        progress_thread.daemon = True
        progress_thread.start()
        
        # Запускаем анализ
        analysis_status[task_id]['progress'] = 15
        analysis_status[task_id]['message'] = 'Запуск анализа...'
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
        analysis_status[task_id]['progress'] = 90
        analysis_status[task_id]['message'] = 'Завершение анализа...'
        logger.info(f"[{task_id}] Этап 3: Завершение анализа")
        
        import time
        time.sleep(0.5)  # Небольшая пауза для плавности
        
        # Вычисляем стоимость анализа
        analysis_status[task_id]['progress'] = 93
        analysis_status[task_id]['message'] = 'Расчет стоимости...'
        cost = None
        if COST_TRACKING_AVAILABLE and initial_balance is not None:
            cost = calculate_analysis_cost(task_id, initial_balance)
            analysis_costs[task_id] = cost
            logger.info(f"[{task_id}] Стоимость анализа: {cost} руб.")
        
        time.sleep(0.3)  # Небольшая пауза для плавности
        
        # Сохраняем результат
        analysis_status[task_id]['progress'] = 96
        analysis_status[task_id]['message'] = 'Сохранение результатов...'
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
        
        # Основной контент
        content = result_data.get('result', '')
        if content:
            # Разбиваем на параграфы по строкам
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    doc.add_paragraph()
                    continue
                
                # Определяем заголовки (если строка короткая и в верхнем регистре или содержит маркеры)
                if (len(line) < 100 and 
                    (line.isupper() or line.startswith('#') or 
                     any(line.startswith(marker) for marker in ['I.', 'II.', 'III.', 'IV.', 'V.', 'VI.', 'VII.', 'VIII.', 'IX.', 'X.']))):
                    heading = doc.add_heading(line, level=1)
                else:
                    para = doc.add_paragraph(line)
        
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

if __name__ == '__main__':
    logger.info("=" * 60)
    logger.info("Запуск Flask приложения...")
    logger.info(f"Сервер будет доступен по адресу: http://{FLASK_HOST}:{FLASK_PORT}")
    logger.info("Нажмите Ctrl+C для остановки")
    logger.info("=" * 60)
    
    print("=" * 60)
    print("Запуск Flask приложения...")
    print(f"Сервер будет доступен по адресу: http://{FLASK_HOST}:{FLASK_PORT}")
    print("Нажмите Ctrl+C для остановки")
    print("=" * 60)
    
    app.run(debug=FLASK_DEBUG, host=FLASK_HOST, port=FLASK_PORT)

