import os
import sys
import json
import platform
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
    from crewai.tools import BaseTool
    from pydantic import BaseModel, Field
    # Импортируем инструмент для скрапинга веб-сайтов
    try:
        from crewai_tools import ScrapeWebsiteTool
        SCRAPE_TOOL_AVAILABLE = True
    except ImportError:
        SCRAPE_TOOL_AVAILABLE = False
        print("⚠️  Инструмент ScrapeWebsiteTool не доступен. Установите: pip install crewai[tools]")
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
    print(f"❌ ОШИБКА: Не удалось импортировать CrewAI: {e}")
    print("📦 Убедитесь, что crewai установлен:")
    print("   pip install 'crewai[tools]>=0.11.2'")
    print("   или")
    print("   pip install crewai>=0.11.2")
    print("   pip install 'crewai[tools]>=0.11.2'")
    # Дополнительная диагностика
    import sys
    print(f"🐍 Python версия: {sys.version}")
    print(f"📂 Python путь: {sys.executable}")
    try:
        import pkg_resources
        installed = [d.project_name for d in pkg_resources.working_set]
        if 'crewai' in installed:
            crewai_pkg = [d for d in pkg_resources.working_set if d.project_name == 'crewai'][0]
            print(f"📦 CrewAI установлен: версия {crewai_pkg.version}")
        else:
            print("❌ CrewAI не найден в установленных пакетах")
    except Exception as diag_e:
        print(f"⚠️  Не удалось проверить установленные пакеты: {diag_e}")
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

# Кастомный инструмент для извлечения РЕАЛЬНЫХ ссылок с HTML-страницы
if CREWAI_IMPORTED:
    try:
        import requests
        from urllib.parse import urljoin, urlparse
        from bs4 import BeautifulSoup

        class ExtractLinksInput(BaseModel):
            """Входные данные для извлечения ссылок со страницы."""
            url: str = Field(..., description="URL страницы (например https://example.com)")

        class ExtractSiteLinksTool(BaseTool):
            name: str = "ExtractSiteLinks"
            description: str = (
                "Извлекает ВСЕ реальные ссылки со страницы по указанному URL. "
                "Возвращает список в формате [текст](url). Используй этот инструмент для раздела СТРУКТУРА САЙТА — "
                "чтобы получить ТОЛЬКО реальные URL, а не придумывать их. Вызывай для главной страницы и подстраниц."
            )
            args_schema: type[BaseModel] = ExtractLinksInput

            def _run(self, url: str) -> str:
                try:
                    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                    r = requests.get(url, headers=headers, timeout=15)
                    r.raise_for_status()
                    r.encoding = r.apparent_encoding or "utf-8"
                    soup = BeautifulSoup(r.text, "html.parser")
                    base = urlparse(url)
                    base_netloc = base.netloc
                    seen = set()
                    lines = []
                    for a in soup.find_all("a", href=True):
                        href = (a["href"] or "").strip()
                        if not href or href.startswith(("#", "javascript:", "mailto:")):
                            continue
                        abs_url = urljoin(url, href)
                        try:
                            parsed = urlparse(abs_url)
                            if parsed.netloc and parsed.netloc.lower() != base_netloc.lower():
                                continue  # только ссылки того же домена
                        except Exception:
                            continue
                        text = (a.get_text() or href).strip()[:80]
                        if not text:
                            text = abs_url
                        key = (abs_url, text)
                        if key in seen:
                            continue
                        seen.add(key)
                        lines.append(f"- [{text}]({abs_url})")
                    if not lines:
                        return f"На странице {url} не найдено внутренних ссылок."
                    return "Ссылки со страницы:\n" + "\n".join(lines)
                except Exception as e:
                    return f"Ошибка при извлечении ссылок с {url}: {e}"

        EXTRACT_LINKS_AVAILABLE = True
    except Exception as e:
        EXTRACT_LINKS_AVAILABLE = False
        ExtractSiteLinksTool = None
        print(f"⚠️  ExtractSiteLinksTool недоступен: {e}")

    # Playwright-инструменты — fallback для сайтов с защитой от ботов (Tatneft и подобные)
    # Аргументы для Chromium: обязательны на VPS/Linux/Docker (headless без display)
    _CHROMIUM_ARGS = ["--no-sandbox", "--disable-dev-shm-usage"]
    try:
        from playwright.sync_api import sync_playwright  # type: ignore[import-untyped]
        from urllib.parse import urljoin, urlparse
        from bs4 import BeautifulSoup

        class ScrapeWithPlaywrightInput(BaseModel):
            url: str = Field(..., description="URL страницы")

        class ScrapeWithPlaywrightTool(BaseTool):
            name: str = "ScrapeWithPlaywright"
            description: str = (
                "Скрапинг через браузер (Playwright). Используй, когда ScrapeWebsiteTool выдаёт ошибку или пустой результат — "
                "браузер выполняет JS и может обойти часть защит (куки, Cloudflare). Возвращает текст страницы."
            )
            args_schema: type[BaseModel] = ScrapeWithPlaywrightInput

            def _run(self, url: str) -> str:
                try:
                    with sync_playwright() as p:
                        browser = p.chromium.launch(headless=True, args=_CHROMIUM_ARGS)
                        ctx = browser.new_context(
                            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
                            viewport={"width": 1920, "height": 1080},
                        )
                        page = ctx.new_page()
                        page.goto(url, wait_until="domcontentloaded", timeout=20000)
                        page.wait_for_timeout(2000)
                        for sel in ['button:has-text("Принять")', 'button:has-text("Согласен")', '[data-testid="accept-cookies"]', '.cookie-accept', '#accept-cookies']:
                            try:
                                if page.locator(sel).count() > 0:
                                    page.locator(sel).first.click(timeout=3000)
                                    page.wait_for_timeout(1000)
                                    break
                            except Exception:
                                pass
                        text = page.inner_text("body", timeout=5000) or ""
                        browser.close()
                        return (text[:15000] + "\n...[обрезано]") if len(text) > 15000 else text
                except Exception as e:
                    return f"Ошибка Playwright для {url}: {e}"

        class ExtractLinksPlaywrightInput(BaseModel):
            url: str = Field(..., description="URL страницы")

        class ExtractLinksWithPlaywrightTool(BaseTool):
            name: str = "ExtractLinksWithPlaywright"
            description: str = (
                "Извлечение ссылок через браузер. Используй, когда ExtractSiteLinks вернул ошибку — "
                "браузер с JS обходит защиту. Возвращает [текст](url)."
            )
            args_schema: type[BaseModel] = ExtractLinksPlaywrightInput

            def _run(self, url: str) -> str:
                try:
                    with sync_playwright() as p:
                        browser = p.chromium.launch(headless=True, args=_CHROMIUM_ARGS)
                        ctx = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36")
                        page = ctx.new_page()
                        page.goto(url, wait_until="domcontentloaded", timeout=20000)
                        page.wait_for_timeout(2000)
                        for sel in ['button:has-text("Принять")', 'button:has-text("Согласен")', '.cookie-accept']:
                            try:
                                if page.locator(sel).count() > 0:
                                    page.locator(sel).first.click(timeout=2000)
                                    page.wait_for_timeout(800)
                                    break
                            except Exception:
                                pass
                        html = page.content()
                        browser.close()
                    soup = BeautifulSoup(html, "html.parser")
                    base_netloc = urlparse(url).netloc.lower()
                    seen, lines = set(), []
                    for a in soup.find_all("a", href=True):
                        href = (a["href"] or "").strip()
                        if not href or href.startswith(("#", "javascript:", "mailto:")):
                            continue
                        abs_url = urljoin(url, href)
                        try:
                            if urlparse(abs_url).netloc.lower() != base_netloc:
                                continue
                        except Exception:
                            continue
                        text = (a.get_text() or href).strip()[:80] or abs_url
                        key = (abs_url, text)
                        if key not in seen:
                            seen.add(key)
                            lines.append(f"- [{text}]({abs_url})")
                    return "Ссылки со страницы:\n" + "\n".join(lines) if lines else f"На странице {url} не найдено внутренних ссылок."
                except Exception as e:
                    return f"Ошибка ExtractLinksWithPlaywright для {url}: {e}"

        PLAYWRIGHT_AVAILABLE = True
    except Exception as e:
        PLAYWRIGHT_AVAILABLE = False
        ScrapeWithPlaywrightTool = None
        ExtractLinksWithPlaywrightTool = None
        print(f"⚠️  Playwright-инструменты недоступны: {e}. Установите: pip install playwright && playwright install chromium. На VPS/Linux: playwright install-deps")
else:
    EXTRACT_LINKS_AVAILABLE = False
    ExtractSiteLinksTool = None
    PLAYWRIGHT_AVAILABLE = False
    ScrapeWithPlaywrightTool = None
    ExtractLinksWithPlaywrightTool = None

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

# Пропускаем создание только в основном процессе Flask reloader
is_werkzeug_main = os.environ.get('WERKZEUG_RUN_MAIN') == 'true'
use_reloader = os.getenv('FLASK_DEBUG', 'True').lower() == 'true' and (
    platform.system() != 'Windows' or os.environ.get('FLASK_USE_RELOADER') == '1'
)
_skip_creation = use_reloader and not is_werkzeug_main

if not CREWAI_IMPORTED:
    print("ОШИБКА: CrewAI не установлен. Установите: pip install crewai>=0.11.2")
elif _skip_creation:
    print("ℹ Flask reloader: пропускаем создание в основном процессе")
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
        # Создаем инструмент для скрапинга (только для указанного сайта)
        # Playwright — первым для сайтов с защитой (Tatneft, и др.): браузер обходит антибот.
        scraper_tools = []
        if PLAYWRIGHT_AVAILABLE and ScrapeWithPlaywrightTool:
            try:
                scraper_tools.append(ScrapeWithPlaywrightTool())
            except Exception as e:
                print(f"⚠️  Не удалось создать ScrapeWithPlaywrightTool: {e}")
        if PLAYWRIGHT_AVAILABLE and ExtractLinksWithPlaywrightTool:
            try:
                scraper_tools.append(ExtractLinksWithPlaywrightTool())
            except Exception as e:
                print(f"⚠️  Не удалось создать ExtractLinksWithPlaywrightTool: {e}")
        if SCRAPE_TOOL_AVAILABLE:
            try:
                scraper_tools.append(ScrapeWebsiteTool())
            except Exception as e:
                print(f"⚠️  Не удалось создать ScrapeWebsiteTool: {e}")
        if EXTRACT_LINKS_AVAILABLE and ExtractSiteLinksTool:
            try:
                scraper_tools.append(ExtractSiteLinksTool())
            except Exception as e:
                print(f"⚠️  Не удалось создать ExtractSiteLinksTool: {e}")
        
        web_scraper_agent = Agent(
    role="Corporate Web Information Specialist",
    goal="Извлечение МАКСИМУМА информации с указанного сайта: все тексты, цифры, ссылки. Ничего не опускать.",
    backstory="""Вы специалист по сбору информации с веб-сайтов. Работаете ТОЛЬКО с указанным сайтом {company_url}. 
    ЗАПРЕЩЕНО использовать другие источники. Вы методично вызываете инструмент скрапинга для каждой страницы. 
    Из ответа инструмента извлекаете ВСЁ: тексты, ссылки (href), цифры, имена. Ссылки копируете ДОСЛОВНО из ответа — никогда не придумываете URL. 
    Строите дерево структуры по иерархии меню. Цель — полный отчёт, а не краткая выжимка.""",
    
    # Основные параметры
    verbose=True,
    allow_delegation=False,
    tools=scraper_tools,  # Инструмент для скрапинга только указанного сайта
    
    # Параметры LLM
    llm_config={
        "model": "gpt-4o",  # Нужна точность извлечения ссылок и структуры
        "temperature": 0.2,  # Очень низкая — точное извлечение без выдумок
        "max_tokens": 8000,  # Больше для детального сбора
    },
    
    # Параметры поведения
    max_iter=15,  # Больше итераций для обхода нескольких страниц
    max_execution_time=600,  # 10 минут на полный сбор  # 5 минут
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
    ВАЖНО: Вы можете анализировать ТОЛЬКО информацию, полученную с указанного сайта {company_url}. 
    ЗАПРЕЩЕНО использовать любые другие источники: поиск в интернете, базы данных, 
    внешние сайты, новостные источники или любые другие ресурсы. 
    Вы должны работать исключительно с данными, собранными с указанного корпоративного сайта.
    Специализируетесь на выявлении тенденций, оценке стратегических направлений,
    анализе конкурентных преимуществ и оценке финансового здоровья компаний.
    Отлично работаете с неструктурированными данными и превращаете их в 
    аналитические выводы. Знакомы с методологией финансового анализа, 
    стратегическим анализом и бизнес-интеллиджензом.""",
    
    verbose=True,
    allow_delegation=False,
    tools=[],  # Нет инструментов - работает только с предоставленными данными
    
    llm_config={
        "model": "gpt-4o",
        "temperature": 0.5,  # Средняя температура для аналитического мышления
        "max_tokens": 6000,  # Больше для детального анализа
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
    корпоративных аналитических отчетов. ВАЖНО: Вы можете использовать ТОЛЬКО информацию, 
    полученную с указанного сайта {company_url}. ЗАПРЕЩЕНО использовать любые другие источники: 
    поиск в интернете, базы данных, внешние сайты, новостные источники или любые другие ресурсы. 
    Вы должны работать исключительно с данными, собранными и проанализированными из указанного 
    корпоративного сайта. Специализируетесь на синтезе информации в единую картину. 
    Отличаетесь способностью выявлять стратегические риски, возможности и ключевые метрики компании. 
    Знакомы с международными стандартами отчетности и инвестиционного анализа.
    Создаете отчеты для руководства, инвесторов и аналитиков.""",
    
    verbose=True,
    allow_delegation=True,  # Может делегировать другим агентам
    tools=[],  # Нет инструментов - работает только с предоставленными данными
    
    llm_config={
        "model": "gpt-4o",
        "temperature": 0.4,  # Точность с элементами синтеза
        "max_tokens": 12000,  # Для полного детального отчёта
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
    description="""КРИТИЧЕСКИ ВАЖНО: Вы можете использовать ТОЛЬКО информацию с указанного сайта {company_url}. 
    ЗАПРЕЩЕНО использовать любые другие источники. Работайте исключительно с содержимым указанного сайта.
    
    ПРИНЦИП: Извлекайте МАКСИМУМ информации. Не опускайте детали. Каждый найденный факт — в отчёт.
    
    АЛГОРИТМ РАБОТЫ:
    1. Вызови ScrapeWebsiteTool для {company_url}. Если ошибка или пустой результат — вызови ScrapeWithPlaywright (браузер с JS, обходит защиту)
    2. В ответе найдите ВСЕ ссылки. Копируй URL ДОСЛОВНО. Если ExtractSiteLinks выдал ошибку — используй ExtractLinksWithPlaywright
    3. Для глубокого сбора вызывай инструмент для ключевых страниц из ответа
    4. Извлекай максимум текста: описания, цифры, имена, даты
    
    Посетите корпоративный сайт {company_url} и извлеките следующую информацию ТОЛЬКО с этого сайта:
    
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
    
    4. ФИНАНСОВАЯ ИНФОРМАЦИЯ (если доступна на сайте):
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

    7. СТРУКТУРА САЙТА (для Приложения в отчёте):
       - Вызови ExtractSiteLinks для {company_url}. Если ошибка — вызови ExtractLinksWithPlaywright
       - Выбери ДО 10 ОСНОВНЫХ разделов. Включай ТОЛЬКО те, чей URL есть в ответе
       - Копируй URL ДОСЛОВНО. НЕ придумывай пути
     
    Ссылки: [описание](url). URL только из ответа инструмента. Максимум информации с каждой страницы.
    Если какая-то информация отсутствует на сайте, укажите это явно, но НЕ пытайтесь найти её в других источниках и НЕ придумывайте.""",
    
    expected_output="""Максимально полный отчет. Все факты, цифры, описания с сайта. 
    Ссылки — [описание](url). Структура — до 10 основных разделов [Название](url), только реальные URL из ExtractSiteLinks.""",
    
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
    description="""КРИТИЧЕСКИ ВАЖНО: Вы можете анализировать ТОЛЬКО информацию, полученную с указанного сайта {company_url}. 
    ЗАПРЕЩЕНО использовать любые другие источники: поиск в интернете, базы данных, внешние сайты, 
    новостные источники или любые другие ресурсы. Работайте исключительно с данными из Задачи 1.
    
    На основе информации из Задачи 1 (которая была собрана ТОЛЬКО с сайта {company_url}), проведите детальный анализ:
    
    1. АНАЛИЗ БИЗНЕС-МОДЕЛИ:
       - Каналы доходов и основные источники прибыли (на основе информации с сайта)
       - Стратегия позиционирования на рынке (на основе информации с сайта)
       - Конкурентные преимущества (на основе информации с сайта)
    
    2. ОЦЕНКА ФИНАНСОВОГО ЗДОРОВЬЯ:
       - Тренды роста (если доступны на сайте)
       - Рентабельность и эффективность (на основе данных с сайта)
       - Финансовая устойчивость (на основе данных с сайта)
    
    3. АНАЛИЗ ПОРТФЕЛЯ ПРОДУКТОВ:
       - Разнообразие предложений (на основе информации с сайта)
       - Связь продуктов с целевыми сегментами (на основе информации с сайта)
       - Инновационность (на основе информации с сайта)
    
    4. СТРАТЕГИЧЕСКАЯ ПОЗИЦИЯ:
       - Соответствие стратегии рыночным возможностям (на основе информации с сайта)
       - Потенциальные риски (на основе информации с сайта)
       - Перспективы роста (на основе информации с сайта)
    
    5. ВЫЯВЛЕНИЕ СИЛЬНЫХ И СЛАБЫХ СТОРОН:
       - Преимущества (на основе информации с сайта)
       - Области для улучшения (на основе информации с сайта)
    
    ПРИНЦИП: Используйте ВСЮ информацию из Задачи 1. Цитируйте конкретные цифры, факты, названия. Не опускайте детали.
    Предоставьте детальный анализ с выводами и рекомендациями, основанными ТОЛЬКО на данных с указанного сайта.""",
    
    expected_output="""Детальный аналитический отчет с ПОДРОБНОЙ оценкой каждого пункта 
    (не менее 2-3 предложений на аспект), идентификацией тенденций и стратегических вопросов. 
    Ссылки на источники — формат [текст](url).""",
    
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
    description="""КРИТИЧЕСКИ ВАЖНО: Вы можете использовать ТОЛЬКО информацию, полученную с указанного сайта {company_url}. 
    ЗАПРЕЩЕНО использовать любые другие источники: поиск в интернете, базы данных, внешние сайты, 
    новостные источники или любые другие ресурсы. Работайте исключительно с данными из Задач 1 и 2.
    
    На основе информации из Задач 1 и 2 создайте комплексный отчет о компании {company_name}.
    
    ПРИНЦИП: МАКСИМУМ ИНФОРМАЦИИ. Включайте ВСЁ из Задач 1 и 2 — каждый факт, цифру, имя. Отчёт должен быть ПОЛНЫМ и ДЕТАЛЬНЫМ, а не кратким резюме. Минимум 3–5 предложений на подпункт.
    
    Формат:
    
    КОМПЛЕКСНЫЙ КОРПОРАТИВНЫЙ ОТЧЕТ: {company_name}
    
    I. КРАТКОЕ РЕЗЮМЕ
       - Краткое описание компании в 3-4 предложениях
       - Ключевые финансовые показатели
       - Основные выводы
       - В КОНЦЕ РАЗДЕЛА: Источники: [страница](url), [раздел](url) — кликабельные ссылки на источники
    
    II. ПРОФИЛЬ КОМПАНИИ
       - Основная информация (название, год основания, размер)
       - Миссия и видение
       - Краткая история развития
       - Текущее положение на рынке
       - Признание компании партнерами и награды компании
       - В КОНЦЕ РАЗДЕЛА: Источники: [страница](url) — кликабельные ссылки
    
    III. ПРОДУКТЫ И УСЛУГИ
       - Основной портфель продуктов/услуг
       - Описание каждого предложения обобщенно
       - Целевые сегменты клиентов
       - Уникальные предложения (УТП)
       - В КОНЦЕ РАЗДЕЛА: Источники: [страница](url)
    
    IV. ОРГАНИЗАЦИОННАЯ СТРУКТУРА
       - Организационная схема
       - Ключевое руководство
       - Подразделения и их функции
       - Производственные мощности
       - Географическое распределение
       - В КОНЦЕ РАЗДЕЛА: Источники: [страница](url)
    
    V. ФИНАНСОВЫЙ ОБЗОР
       - Ключевые финансовые показатели
       - Доходы и прибыль (за доступные периоды)
       - Финансовые тренды
       - Инвестиции и источники финансирования
       - В КОНЦЕ РАЗДЕЛА: Источники: [страница](url)
    
    VI. СТРАТЕГИЧЕСКОЕ НАПРАВЛЕНИЕ
       - Долгосрочные цели
       - Ключевые стратегические инициативы
       - Планы развития и расширения
       - Инновационные проекты
       - Инвестиционные проекты, их стадия выполнения
       - В КОНЦЕ РАЗДЕЛА: Источники: [страница](url)
    
    VII. КОНКУРЕНТНЫЙ АНАЛИЗ
       - Основные конкурентные преимущества
       - Позиция на рынке
       - Дифференциация
       - В КОНЦЕ РАЗДЕЛА: Источники: [страница](url)
    
    VIII. РИСКИ И ВОЗМОЖНОСТИ
       - Идентифицированные риски
       - Стратегические возможности
       - Рекомендации
       - SWOT-анализ компании
       - В КОНЦЕ РАЗДЕЛА: Источники: [страница](url)
    
    IX. ИНВЕСТИЦИОННЫЕ ПЕРСПЕКТИВЫ
       - Причины инвестировать
       - Перспективы роста
       - Финансовая стабильность
       - В КОНЦЕ РАЗДЕЛА: Источники: [страница](url)

    X. ПРИЛОЖЕНИЕ: СТРУКТУРА САЙТА
       - ПРОСТОЙ список: до 10 основных разделов сайта. Каждый пункт — одна строка [Название](url)
       - БЕЗ вложенности, БЕЗ подразделов. Только главные разделы: Главная, О компании, Продукция, Контакты и т.п.
       - Пример: 1. [Главная](url)  2. [О компании](url)  3. [Продукция](url)  4. [Контакты](url)
       - URL — ТОЛЬКО из Задачи 1. Если структуры нет — напишите «Структура не извлечена»
    
    ВСЕ ЗАГОЛОВКИ И СОДЕРЖАНИЕ ОТЧЕТА ДОЛЖНЫ БЫТЬ НА РУССКОМ ЯЗЫКЕ.
    
    КРИТИЧЕСКИ ВАЖНО:
    1. ДЕТАЛИЗАЦИЯ: Каждый пункт — минимум 3–5 предложений. Конкретные данные, цифры, имена из Задач 1 и 2. Не опускайте информацию. Бедный короткий отчёт — ошибка.
    2. ССЫЛКИ: Только проверенные! В «Источники» включай ТОЛЬКО url из Задачи 1 — копируй дословно. Несуществующие ссылки НЕ включай.
    3. СТРУКТУРА САЙТА: до 10 пунктов из ответа ExtractSiteLinks. Только реальные [Название](url).""",
    
    expected_output="""Полный детальный корпоративный отчет. Каждый раздел — 3–5+ предложений + в конце «Источники:» со ссылками. Приложение: до 10 основных разделов [Название](url). Отчёт на русском.""",
    
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