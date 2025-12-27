import os
import json
from datetime import datetime
from pathlib import Path

# ВАЖНО: Отключаем телеметрию CrewAI ДО импорта модуля
# Это должно быть сделано до загрузки dotenv, чтобы переменные были установлены как можно раньше
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "1"
os.environ["CREWAI_TRACING_ENABLED"] = "false"

# Загружаем переменные окружения до импорта CrewAI
from dotenv import load_dotenv
load_dotenv()

# Убеждаемся, что телеметрия отключена (на случай, если .env переопределил значения)
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "1"
os.environ["CREWAI_TRACING_ENABLED"] = "false"

# Импортируем CrewAI с обработкой ошибок
# #region agent log
try:
    import json
    import os
    from pathlib import Path
    debug_log_path = Path(__file__).parent / '.cursor' / 'debug.log'
    with open(debug_log_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps({"sessionId":"debug-session","runId":"init","hypothesisId":"A","location":"Agents_crew.py:12","message":"Попытка импорта CrewAI","data":{"timestamp":__import__('datetime').datetime.now().isoformat()}})+'\n')
except: pass
# #endregion
try:
    from crewai import Agent, Task, Crew, Process
    CREWAI_IMPORTED = True
    # #region agent log
    try:
        with open(debug_log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"init","hypothesisId":"A","location":"Agents_crew.py:15","message":"CrewAI успешно импортирован","data":{"CREWAI_IMPORTED":True,"timestamp":__import__('datetime').datetime.now().isoformat()}})+'\n')
    except: pass
    # #endregion
except ImportError as e:
    CREWAI_IMPORTED = False
    # #region agent log
    try:
        with open(debug_log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"init","hypothesisId":"A","location":"Agents_crew.py:18","message":"Ошибка импорта CrewAI","data":{"error":str(e),"CREWAI_IMPORTED":False,"timestamp":__import__('datetime').datetime.now().isoformat()}})+'\n')
    except: pass
    # #endregion
    print(f"ОШИБКА: Не удалось импортировать CrewAI: {e}")
    print("Убедитесь, что crewai установлен: pip install crewai>=0.11.2")
    # Создаем заглушки для избежания ошибок при импорте модуля
    Agent = None
    Task = None
    Crew = None
    Process = None

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

# #region agent log
write_debug_log({
    "sessionId": "debug-session",
    "runId": "init",
    "hypothesisId": "A",
    "location": "Agents_crew.py:7",
    "message": "Импорт CrewAI модулей",
    "data": {"timestamp": datetime.now().isoformat()}
})
# #endregion

# Настройка переменных окружения для OpenAI
api_key = os.getenv("OPENAI_API_KEY")
api_base = os.getenv("OPENAI_API_BASE")

# #region agent log
write_debug_log({
    "sessionId": "debug-session",
    "runId": "init",
    "hypothesisId": "C",
    "location": "Agents_crew.py:15",
    "message": "Проверка переменных окружения телеметрии",
    "data": {
        "CREWAI_TELEMETRY_OPT_OUT": os.getenv("CREWAI_TELEMETRY_OPT_OUT"),
        "CREWAI_TRACING_ENABLED": os.getenv("CREWAI_TRACING_ENABLED"),
        "timestamp": datetime.now().isoformat()
    }
})
# #endregion

# Телеметрия уже отключена в начале файла, но убеждаемся еще раз
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "1"
os.environ["CREWAI_TRACING_ENABLED"] = "false"

# #region agent log
write_debug_log({
    "sessionId": "debug-session",
    "runId": "init",
    "hypothesisId": "C",
    "location": "Agents_crew.py:22",
    "message": "Проверка переменных для отключения телеметрии",
    "data": {
        "CREWAI_TELEMETRY_OPT_OUT": os.environ.get("CREWAI_TELEMETRY_OPT_OUT"),
        "CREWAI_TRACING_ENABLED": os.environ.get("CREWAI_TRACING_ENABLED"),
        "timestamp": datetime.now().isoformat()
    }
})
# #endregion

if api_key:
    os.environ["OPENAI_API_KEY"] = api_key
if api_base:
    os.environ["OPENAI_API_BASE"] = api_base

# Инициализируем переменные по умолчанию
# ВАЖНО: При повторном импорте модуля (Flask reloader) все переменные сбрасываются
# Поэтому crew будет пересоздан при каждом импорте, что нормально
web_scraper_agent = None
data_analyzer_agent = None
bi_engineer_agent = None
task_1_scrape = None
task_2_analyze = None
task_3_report = None
crew = None

# Проверяем, что это дочерний процесс Flask reloader (рабочий сервер)
# WERKZEUG_RUN_MAIN устанавливается Flask только в дочернем процессе
# Это предотвращает создание агентов дважды (в основном и дочернем процессе)
is_werkzeug_main = os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'

# Проверяем, что CrewAI импортирован
if not CREWAI_IMPORTED:
    print("ОШИБКА: CrewAI не установлен. Установите: pip install crewai>=0.11.2")
    # Не выбрасываем исключение, чтобы main.py мог обработать ошибку
elif not is_werkzeug_main and FLASK_DEBUG:
    # Если это основной процесс Flask reloader (не дочерний), не создаем агентов
    # Они будут созданы в дочернем процессе
    print("ℹ Flask reloader: пропускаем создание агентов в основном процессе")
else:
    # ============================================================================
    # АГЕНТ 1: Web Scraper (Считыватель информации с корпоративного сайта)
    # ============================================================================
    
    try:
        # #region agent log
        try:
            with open(debug_log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"init","hypothesisId":"B","location":"Agents_crew.py:108","message":"Создание Web Scraper Agent","data":{"CREWAI_IMPORTED":CREWAI_IMPORTED,"Agent_class":str(Agent) if Agent else None,"timestamp":__import__('datetime').datetime.now().isoformat()}})+'\n')
        except: pass
        # #endregion
        web_scraper_agent = Agent(
    role="Corporate Web Information Specialist",
    goal="Извлечение полной и точной информации с корпоративного сайта компании",
    backstory="""Вы специалист по сбору информации с веб-сайтов компаний. 
    Имеете опыт в работе с различными структурами сайтов, умеете находить 
    и извлекать ключевую информацию: описание компании, услуги, структуру, 
    контакты, финансовые показатели и стратегические документы. 
    Работаете методично и внимательно к деталям.""",
    
    # Основные параметры
    verbose=True,
    allow_delegation=False,
    tools=[],  # Добавьте инструменты для работы с веб
    
    # Параметры LLM
    llm_config={
        "model": "gpt-4",
        "temperature": 0.3,  # Низкая температура для точного извлечения данных
        "max_tokens": 4000,
    },
    
    # Параметры поведения
    max_iter=5,
    max_execution_time=300,  # 5 минут
    memory=True,
    )
        # #region agent log
        try:
            with open(debug_log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"init","hypothesisId":"B","location":"Agents_crew.py:136","message":"Web Scraper Agent создан","data":{"success":True,"agent_type":str(type(web_scraper_agent)),"timestamp":__import__('datetime').datetime.now().isoformat()}})+'\n')
        except: pass
        # #endregion
        print("✓ Web Scraper Agent создан успешно")
    except Exception as e:
        # #region agent log
        try:
            with open(debug_log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"init","hypothesisId":"B","location":"Agents_crew.py:140","message":"Ошибка создания Web Scraper Agent","data":{"error":str(e),"error_type":type(e).__name__,"timestamp":__import__('datetime').datetime.now().isoformat()}})+'\n')
        except: pass
        # #endregion
        print(f"ОШИБКА при создании Web Scraper Agent: {e}")
        import traceback
        traceback.print_exc()
        web_scraper_agent = None
    
    # ============================================================================
    # АГЕНТ 2: Data Analyzer (Анализатор информации)
    # ============================================================================
    
    try:
        # #region agent log
        try:
            with open(debug_log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"init","hypothesisId":"B","location":"Agents_crew.py:145","message":"Создание Data Analyzer Agent","data":{"web_scraper_created":web_scraper_agent is not None,"timestamp":__import__('datetime').datetime.now().isoformat()}})+'\n')
        except: pass
        # #endregion
        data_analyzer_agent = Agent(
    role="Corporate Data Analyst",
    goal="Анализ и структурирование информации о компании для выявления ключевых паттернов и взаимосвязей",
    backstory="""Вы опытный аналитик с 10+ летним опытом в анализе корпоративной информации.
    Специализируетесь на выявлении тенденций, оценке стратегических направлений,
    анализе конкурентных преимуществ и оценке финансового здоровья компаний.
    Отлично работаете с неструктурированными данными и превращаете их в 
    аналитические выводы. Знакомы с методологией финансового анализа, 
    стратегическим анализом и бизнес-интеллиджензом.""",
    
    verbose=True,
    allow_delegation=False,
    tools=[],
    
    llm_config={
        "model": "gpt-4",
        "temperature": 0.5,  # Средняя температура для аналитического мышления
        "max_tokens": 3000,
    },
    
    max_iter=5,
    max_execution_time=300,
    memory=True,
    )
        # #region agent log
        try:
            with open(debug_log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"init","hypothesisId":"B","location":"Agents_crew.py:164","message":"Data Analyzer Agent создан","data":{"success":True,"timestamp":__import__('datetime').datetime.now().isoformat()}})+'\n')
        except: pass
        # #endregion
        print("✓ Data Analyzer Agent создан успешно")
    except Exception as e:
        # #region agent log
        try:
            with open(debug_log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"init","hypothesisId":"B","location":"Agents_crew.py:168","message":"Ошибка создания Data Analyzer Agent","data":{"error":str(e),"error_type":type(e).__name__,"timestamp":__import__('datetime').datetime.now().isoformat()}})+'\n')
        except: pass
        # #endregion
        print(f"ОШИБКА при создании Data Analyzer Agent: {e}")
        import traceback
        traceback.print_exc()
        data_analyzer_agent = None
    
    # ============================================================================
    # АГЕНТ 3: Business Intelligence Engineer (Инженер BI)
    # ============================================================================
    
    try:
        # #region agent log
        try:
            with open(debug_log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"init","hypothesisId":"B","location":"Agents_crew.py:173","message":"Создание BI Engineer Agent","data":{"agents_created":web_scraper_agent is not None and data_analyzer_agent is not None,"timestamp":__import__('datetime').datetime.now().isoformat()}})+'\n')
        except: pass
        # #endregion
        bi_engineer_agent = Agent(
    role="Business Intelligence Engineer",
    goal="Формирование сводной информации о компании в структурированном формате с аналитическими выводами",
    backstory="""Вы ведущий инженер бизнес-интеллиджеза с опытом в создании 
    корпоративных аналитических отчетов. Специализируетесь на синтезе различных 
    источников информации в единую картину. Отличаетесь способностью выявлять 
    стратегические риски, возможности и ключевые метрики компании. 
    Знакомы с международными стандартами отчетности и инвестиционного анализа.
    Создаете отчеты для руководства, инвесторов и аналитиков.""",
    
    verbose=True,
    allow_delegation=True,  # Может делегировать другим агентам
    tools=[],
    
    llm_config={
        "model": "gpt-4",
        "temperature": 0.4,  # Точность с элементами синтеза
        "max_tokens": 5000,
    },
    
    max_iter=10,
    max_execution_time=600,  # 10 минут на формирование финального отчета
    memory=True,
    )
        # #region agent log
        try:
            with open(debug_log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"init","hypothesisId":"B","location":"Agents_crew.py:189","message":"BI Engineer Agent создан","data":{"success":True,"all_agents_created":all([web_scraper_agent, data_analyzer_agent, bi_engineer_agent]),"timestamp":__import__('datetime').datetime.now().isoformat()}})+'\n')
        except: pass
        # #endregion
        print("✓ BI Engineer Agent создан успешно")
    except Exception as e:
        # #region agent log
        try:
            with open(debug_log_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps({"sessionId":"debug-session","runId":"init","hypothesisId":"B","location":"Agents_crew.py:193","message":"Ошибка создания BI Engineer Agent","data":{"error":str(e),"error_type":type(e).__name__,"timestamp":__import__('datetime').datetime.now().isoformat()}})+'\n')
        except: pass
        # #endregion
        print(f"ОШИБКА при создании BI Engineer Agent: {e}")
        import traceback
        traceback.print_exc()
        bi_engineer_agent = None
    
    # Проверяем, что все агенты созданы
    # #region agent log
    try:
        with open(debug_log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps({"sessionId":"debug-session","runId":"init","hypothesisId":"B","location":"Agents_crew.py:200","message":"Проверка создания агентов","data":{"web_scraper":web_scraper_agent is not None,"data_analyzer":data_analyzer_agent is not None,"bi_engineer":bi_engineer_agent is not None,"all_created":all([web_scraper_agent, data_analyzer_agent, bi_engineer_agent]),"timestamp":__import__('datetime').datetime.now().isoformat()}})+'\n')
    except: pass
    # #endregion
    if not all([web_scraper_agent, data_analyzer_agent, bi_engineer_agent]):
        print("ОШИБКА: Не все агенты созданы. Проверьте логи выше.")
        crew = None
    else:
        # ============================================================================
        # ОПРЕДЕЛЕНИЕ ЗАДАЧ (TASKS)
        # ============================================================================
        
        try:
            # #region agent log
            try:
                with open(debug_log_path, 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"init","hypothesisId":"C","location":"Agents_crew.py:225","message":"Создание Task 1 (scrape)","data":{"Task_class":str(Task) if Task else None,"timestamp":__import__('datetime').datetime.now().isoformat()}})+'\n')
            except: pass
            # #endregion
            # ЗАДАЧА 1: Сбор информации с сайта
            task_1_scrape = Task(
    description="""Посетите корпоративный сайт {company_url} и извлеките следующую информацию:
    
    1. ОСНОВНАЯ ИНФОРМАЦИЯ:
       - Полное название компании и аббревиатура
       - Краткое описание компании (из раздела "О нас")
       - Год основания и размер компании (количество сотрудников)
    
    2. ПРОДУКТЫ И УСЛУГИ:
       - Полный список основных продуктов/услуг
       - Описание каждого продукта/услуги
       - Целевые рынки и сегменты клиентов
    
    3. СТРУКТУРА КОМПАНИИ:
       - Организационная структура (подразделения, филиалы)
       - Руководство и ключевые должностные лица (если доступно)
       - Количество офисов и географический охват
    
    4. ФИНАНСОВАЯ ИНФОРМАЦИЯ (если доступна):
       - Годовой доход/оборот
       - Финансовые показатели за последние годы
       - Инвестиции и источники финансирования
       - Ссылки на финансовые отчеты
    
    5. СТРАТЕГИЯ И ПЛАНЫ:
       - Миссия и видение компании
       - Ключевые стратегические направления
       - Планы развития и экспансии
       - Инновационные инициативы
    
    6. ИСТОРИЯ КОМПАНИИ:
       - Основные вехи и достижения
       - Ключевые события развития
    
    Извлекайте точные данные со ссылками на источники. Сохраняйте оригинальный текст для критических данных.""",
    
    expected_output="""Структурированный отчет со всей извлеченной информацией, 
    включая исходный текст, ссылки на источники и примечания о качестве данных.""",
    
    agent=web_scraper_agent,
    output_file="tasks/task_1_scraped_data.md",
            )
            # #region agent log
            try:
                with open(debug_log_path, 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"init","hypothesisId":"C","location":"Agents_crew.py:236","message":"Task 1 создана","data":{"success":True,"task_type":str(type(task_1_scrape)),"timestamp":__import__('datetime').datetime.now().isoformat()}})+'\n')
            except: pass
            # #endregion
            print("✓ Task 1 (scrape) создана успешно")
            
            # ЗАДАЧА 2: Анализ информации
            # #region agent log
            try:
                with open(debug_log_path, 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"init","hypothesisId":"C","location":"Agents_crew.py:242","message":"Создание Task 2 (analyze)","data":{"task1_created":task_1_scrape is not None,"timestamp":__import__('datetime').datetime.now().isoformat()}})+'\n')
            except: pass
            # #endregion
            task_2_analyze = Task(
    description="""На основе информации из Задачи 1, проведите детальный анализ:
    
    1. АНАЛИЗ БИЗНЕС-МОДЕЛИ:
       - Каналы доходов и основные источники прибыли
       - Стратегия позиционирования на рынке
       - Конкурентные преимущества
    
    2. ОЦЕНКА ФИНАНСОВОГО ЗДОРОВЬЯ:
       - Тренды роста (если доступны)
       - Рентабельность и эффективность
       - Финансовая устойчивость
    
    3. АНАЛИЗ ПОРТФЕЛЯ ПРОДУКТОВ:
       - Разнообразие предложений
       - Связь продуктов с целевыми сегментами
       - Инновационность
    
    4. СТРАТЕГИЧЕСКАЯ ПОЗИЦИЯ:
       - Соответствие стратегии рыночным возможностям
       - Потенциальные риски
       - Перспективы роста
    
    5. ВЫЯВЛЕНИЕ СИЛЬНЫХ И СЛАБЫХ СТОРОН:
       - Преимущества
       - Областиsfor improvement
    
    Предоставьте структурированный анализ с выводами и рекомендациями.""",
    
    expected_output="""Детальный аналитический отчет с оценкой ключевых аспектов 
    бизнеса, идентификацией тенденций и выявлением стратегических вопросов.""",
    
    agent=data_analyzer_agent,
    output_file="tasks/task_2_analysis.md",
            )
            # #region agent log
            try:
                with open(debug_log_path, 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"init","hypothesisId":"C","location":"Agents_crew.py:272","message":"Task 2 создана","data":{"success":True,"timestamp":__import__('datetime').datetime.now().isoformat()}})+'\n')
            except: pass
            # #endregion
            print("✓ Task 2 (analyze) создана успешно")
            
            # ЗАДАЧА 3: Формирование итоговой сводки
            # #region agent log
            try:
                with open(debug_log_path, 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"init","hypothesisId":"C","location":"Agents_crew.py:278","message":"Создание Task 3 (report)","data":{"tasks_created":task_1_scrape is not None and task_2_analyze is not None,"timestamp":__import__('datetime').datetime.now().isoformat()}})+'\n')
            except: pass
            # #endregion
            task_3_report = Task(
    description="""На основе информации из Задач 1 и 2, создайте комплексный отчет 
    о компании {company_name} в следующем формате:
    
    КОМПЛЕКСНЫЙ КОРПОРАТИВНЫЙ ОТЧЕТ: {company_name}
    
    I. КРАТКОЕ РЕЗЮМЕ
       - Краткое описание компании в 2-3 предложениях
       - Ключевые финансовые показатели
       - Основные выводы
    
    II. ПРОФИЛЬ КОМПАНИИ
       - Основная информация (название, год основания, размер)
       - Миссия и видение
       - Краткая история развития
       - Текущее положение на рынке
    
    III. ПРОДУКТЫ И УСЛУГИ
       - Основной портфель продуктов/услуг
       - Описание каждого предложения
       - Целевые сегменты клиентов
       - Уникальные предложения (УТП)
    
    IV. ОРГАНИЗАЦИОННАЯ СТРУКТУРА
       - Организационная схема
       - Ключевое руководство
       - Подразделения и их функции
       - Географическое распределение
    
    V. ФИНАНСОВЫЙ ОБЗОР
       - Ключевые финансовые показатели
       - Доходы и прибыль (за доступные периоды)
       - Финансовые тренды
       - Инвестиции и источники финансирования
    
    VI. СТРАТЕГИЧЕСКОЕ НАПРАВЛЕНИЕ
       - Долгосрочные цели
       - Ключевые стратегические инициативы
       - Планы развития и расширения
       - Инновационные проекты
    
    VII. КОНКУРЕНТНЫЙ АНАЛИЗ
       - Основные конкурентные преимущества
       - Позиция на рынке
       - Дифференциация
    
    VIII. РИСКИ И ВОЗМОЖНОСТИ
       - Идентифицированные риски
       - Стратегические возможности
       - Рекомендации
    
    IX. ИНВЕСТИЦИОННЫЕ ПЕРСПЕКТИВЫ
       - Причины инвестировать
       - Перспективы роста
       - Финансовая стабильность
    
    ВСЕ ЗАГОЛОВКИ И СОДЕРЖАНИЕ ОТЧЕТА ДОЛЖНЫ БЫТЬ НА РУССКОМ ЯЗЫКЕ.
    Форматируйте как профессиональный отчет с четкой структурой и аналитическими выводами.""",
    
    expected_output="""Комплексный корпоративный отчет в формате структурированного документа 
    с подробной информацией о компании, финансовом анализе и стратегических выводах. 
    Весь отчет должен быть на русском языке. Отчет должен быть готов для представления инвесторам или руководству.""",
    
    agent=bi_engineer_agent,
    output_file="tasks/task_3_final_report.md",
            )
            # #region agent log
            try:
                with open(debug_log_path, 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"init","hypothesisId":"C","location":"Agents_crew.py:370","message":"Task 3 создана","data":{"success":True,"all_tasks_created":all([task_1_scrape, task_2_analyze, task_3_report]),"timestamp":__import__('datetime').datetime.now().isoformat()}})+'\n')
            except: pass
            # #endregion
            print("✓ Task 3 (report) создана успешно")
            
            # Проверяем, что все задачи созданы
            # #region agent log
            try:
                with open(debug_log_path, 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"init","hypothesisId":"C","location":"Agents_crew.py:375","message":"Проверка создания задач","data":{"task1":task_1_scrape is not None,"task2":task_2_analyze is not None,"task3":task_3_report is not None,"all_created":all([task_1_scrape, task_2_analyze, task_3_report]),"timestamp":__import__('datetime').datetime.now().isoformat()}})+'\n')
            except: pass
            # #endregion
            if not all([task_1_scrape, task_2_analyze, task_3_report]):
                print("ОШИБКА: Не все задачи созданы. Проверьте логи выше.")
                crew = None
            else:
                # #region agent log
                try:
                    with open(debug_log_path, 'a', encoding='utf-8') as f:
                        f.write(json.dumps({"sessionId":"debug-session","runId":"init","hypothesisId":"D","location":"Agents_crew.py:384","message":"Создание объекта Crew","data":{"Crew_class":str(Crew) if Crew else None,"agents_count":sum([1 for a in [web_scraper_agent, data_analyzer_agent, bi_engineer_agent] if a is not None]),"tasks_count":sum([1 for t in [task_1_scrape, task_2_analyze, task_3_report] if t is not None]),"timestamp":__import__('datetime').datetime.now().isoformat()}})+'\n')
                except: pass
                # #endregion
                
                try:
                    crew = Crew(
                        agents=[web_scraper_agent, data_analyzer_agent, bi_engineer_agent],
                        tasks=[task_1_scrape, task_2_analyze, task_3_report],
                        verbose=True,
                        process="sequential",  # Выполнение задач последовательно
                        output_file="crew_output.md",
                    )
                    # #region agent log
                    try:
                        with open(debug_log_path, 'a', encoding='utf-8') as f:
                            f.write(json.dumps({"sessionId":"debug-session","runId":"init","hypothesisId":"D","location":"Agents_crew.py:401","message":"Crew объект создан","data":{"success":True,"crew_type":str(type(crew)),"timestamp":__import__('datetime').datetime.now().isoformat()}})+'\n')
                    except: pass
                    # #endregion
                    print("✓ Crew объект создан успешно")
                except Exception as e:
                    # #region agent log
                    try:
                        with open(debug_log_path, 'a', encoding='utf-8') as f:
                            f.write(json.dumps({"sessionId":"debug-session","runId":"init","hypothesisId":"D","location":"Agents_crew.py:405","message":"Ошибка создания Crew объекта","data":{"error":str(e),"error_type":type(e).__name__,"timestamp":__import__('datetime').datetime.now().isoformat()}})+'\n')
                    except: pass
                    # #endregion
                    print(f"ОШИБКА при создании Crew объекта: {e}")
                    import traceback
                    traceback.print_exc()
                    crew = None
        except Exception as e:
            # #region agent log
            try:
                with open(debug_log_path, 'a', encoding='utf-8') as f:
                    f.write(json.dumps({"sessionId":"debug-session","runId":"init","hypothesisId":"C","location":"Agents_crew.py:410","message":"Ошибка при создании задач","data":{"error":str(e),"error_type":type(e).__name__,"timestamp":__import__('datetime').datetime.now().isoformat()}})+'\n')
            except: pass
            # #endregion
            print(f"ОШИБКА при создании задач: {e}")
            import traceback
            traceback.print_exc()
            task_1_scrape = None
            task_2_analyze = None
            task_3_report = None
            crew = None

# Проверяем финальное состояние crew перед экспортом
# #region agent log
try:
    with open(debug_log_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps({"sessionId":"debug-session","runId":"init","hypothesisId":"E","location":"Agents_crew.py:559","message":"Финальная проверка crew перед экспортом","data":{"crew_is_none":crew is None,"crew_type":str(type(crew)) if crew else None,"CREWAI_IMPORTED":CREWAI_IMPORTED,"timestamp":__import__('datetime').datetime.now().isoformat()}})+'\n')
except: pass
# #endregion

# #region agent log
write_debug_log({
    "sessionId": "debug-session",
    "runId": "init",
    "hypothesisId": "A",
    "location": "Agents_crew.py:264",
    "message": "Объект Crew создан",
    "data": {"timestamp": datetime.now().isoformat(), "crew_is_none": crew is None}
})
# #endregion

# ============================================================================
# ЗАПУСК CREW
# ============================================================================

if __name__ == "__main__":
    # Пример использования
    inputs = {
        "company_url": "https://example-company.com",  # Замените на реальный URL
        "company_name": "Example Company",  # Замените на название компании
    }
    
    result = crew.kickoff(inputs=inputs)
    print(result)