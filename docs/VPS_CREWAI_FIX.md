# Исправление ошибки "CrewAI не доступен" на VPS

## Проблема

При запуске контейнера на VPS возникает ошибка:
```
Ошибка: "CrewAI не доступен. Проверьте установку зависимостей."
```

## Причина

В `requirements.txt` была указана только базовая версия `crewai>=0.11.2`, без инструментов `crewai[tools]`, которые необходимы для работы приложения.

## Решение

### 1. Обновить код на сервере

На вашем локальном компьютере:
```bash
# Закоммитьте изменения
git add requirements.txt Dockerfile Agents_crew.py
git commit -m "Исправление установки CrewAI с инструментами"
git push
```

На VPS:
```bash
cd ~/comp-site-analyz
git pull
```

### 2. Пересобрать и запушить Docker образ

**На локальном компьютере:**

```bash
# Пересобрать образ с новыми зависимостями
docker build -t avardous/comp_site_analyz:latest .

# Запушить образ в Docker Hub
docker push avardous/comp_site_analyz:latest

# Или использовать скрипт
python scripts/push_to_dockerhub.py
```

**На VPS:**

```bash
cd ~/comp-site-analyz

# Остановить текущий контейнер
docker-compose -f scripts/docker-compose.prod.yml down

# Обновить образ из Docker Hub
docker-compose -f scripts/docker-compose.prod.yml pull

# Запустить контейнер с новым образом
docker-compose -f scripts/docker-compose.prod.yml up -d
```

### 3. Проверить установку

```bash
# Проверить логи контейнера
docker-compose -f scripts/docker-compose.prod.yml logs

# Проверить, что CrewAI установлен в контейнере
docker-compose -f scripts/docker-compose.prod.yml exec web python -c "import crewai; print('CrewAI установлен:', crewai.__version__ if hasattr(crewai, '__version__') else 'unknown')"

# Проверить, что инструменты доступны
docker-compose -f scripts/docker-compose.prod.yml exec web python -c "from crewai_tools import ScrapeWebsiteTool; print('Инструменты доступны')"
```

### 4. Альтернативное решение (если нет доступа к git)

Если нет возможности обновить код через git, можно исправить вручную:

```bash
# Войти в контейнер
docker-compose -f scripts/docker-compose.prod.yml exec web bash

# Установить crewai[tools]
pip install "crewai[tools]>=0.11.2"

# Выйти из контейнера
exit

# Перезапустить контейнер
docker-compose -f scripts/docker-compose.prod.yml restart
```

**Примечание:** Это временное решение. При следующей пересборке образа изменения будут потеряны, поэтому лучше обновить код через git.

## Что было исправлено

1. **requirements.txt**: Изменено с `crewai>=0.11.2` на `crewai[tools]>=0.11.2` (включает базовый crewai и инструменты)

2. **Dockerfile**: 
   - Убрана дублирующая установка `crewai[tools]` (теперь устанавливается из requirements.txt)
   - Добавлена проверка установки CrewAI и его инструментов
   - Добавлена автоматическая установка инструментов, если они не установлены

3. **Agents_crew.py**: 
   - Улучшена диагностика ошибок импорта
   - Добавлена информация о версии Python и установленных пакетах

## Проверка работоспособности

После исправления приложение должно:
1. Успешно импортировать CrewAI при запуске
2. Создавать агентов без ошибок
3. Выполнять анализ сайтов

Проверьте логи при запуске:
```bash
docker-compose -f scripts/docker-compose.prod.yml logs -f
```

Должны появиться сообщения:
```
✓ CrewAI успешно импортирован
✓ Web Scraper Agent создан успешно
✓ Data Analyzer Agent создан успешно
✓ BI Engineer Agent создан успешно
```

