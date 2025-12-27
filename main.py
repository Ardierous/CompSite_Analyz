from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
import threading
from datetime import datetime
from urllib.parse import urlparse
import warnings
warnings.filterwarnings('ignore')

try:
    from Agents_crew import crew
    CREW_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import crew: {e}")
    CREW_AVAILABLE = False
    crew = None

app = Flask(__name__)
CORS(app)

# Конфигурация
FLASK_HOST = os.getenv('FLASK_HOST', '127.0.0.1')
FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'

# Хранилище результатов анализа (в продакшене использовать Redis или БД)
analysis_results = {}
analysis_status = {}

@app.route('/')
def index():
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
    
    # Устанавливаем статус "в процессе"
    analysis_status[task_id] = {
        'status': 'processing',
        'progress': 0,
        'message': 'Анализ запущен...'
    }
    
    # Запускаем анализ в отдельном потоке
    thread = threading.Thread(
        target=run_analysis,
        args=(task_id, company_url)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'task_id': task_id,
        'status': 'processing',
        'message': 'Анализ запущен'
    })

def run_analysis(task_id, company_url):
    try:
        if not CREW_AVAILABLE:
            raise Exception("CrewAI не доступен. Проверьте установку зависимостей.")
        
        # Извлекаем название компании из URL
        parsed_url = urlparse(company_url)
        domain = parsed_url.netloc
        # Убираем www. и извлекаем основное имя домена
        domain_parts = domain.replace('www.', '').split('.')
        company_name = domain_parts[0].capitalize() if domain_parts else 'Company'
        
        # Обновляем статус
        analysis_status[task_id]['progress'] = 10
        analysis_status[task_id]['message'] = 'Сбор информации с сайта...'
        
        # Подготавливаем входные данные
        inputs = {
            "company_url": company_url,
            "company_name": company_name,
        }
        
        # Запускаем анализ
        analysis_status[task_id]['progress'] = 30
        analysis_status[task_id]['message'] = 'Анализ данных...'
        
        result = crew.kickoff(inputs=inputs)
        
        analysis_status[task_id]['progress'] = 80
        analysis_status[task_id]['message'] = 'Формирование отчета...'
        
        # Сохраняем результат
        analysis_results[task_id] = {
            'result': str(result),
            'url': company_url,
            'company_name': company_name,
            'timestamp': datetime.now().isoformat()
        }
        
        # Устанавливаем статус "завершено"
        analysis_status[task_id] = {
            'status': 'completed',
            'progress': 100,
            'message': 'Анализ завершен'
        }
        
    except Exception as e:
        error_message = str(e)
        print(f"Ошибка при анализе задачи {task_id}: {error_message}")
        analysis_status[task_id] = {
            'status': 'error',
            'progress': 0,
            'message': f'Ошибка: {error_message}'
        }

@app.route('/api/status/<task_id>', methods=['GET'])
def get_status(task_id):
    if task_id not in analysis_status:
        return jsonify({'error': 'Задача не найдена'}), 404
    
    status = analysis_status[task_id].copy()
    
    # Если анализ завершен, добавляем результат
    if status['status'] == 'completed':
        if task_id in analysis_results:
            status['result'] = analysis_results[task_id]
    
    return jsonify(status)

if __name__ == '__main__':
    print("=" * 60)
    print("Запуск Flask приложения...")
    print(f"Сервер будет доступен по адресу: http://{FLASK_HOST}:{FLASK_PORT}")
    print("Нажмите Ctrl+C для остановки")
    print("=" * 60)
    app.run(debug=FLASK_DEBUG, host=FLASK_HOST, port=FLASK_PORT)

