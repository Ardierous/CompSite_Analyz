# Деплой на сервер

## Минимальный набор для деплоя

Для деплоя **НЕ нужно** собирать контейнеры локально. Используется готовый образ из Docker Hub.

## Необходимые файлы

1. `scripts/docker-compose.prod.yml` - конфигурация для продакшена
2. `.env` - переменные окружения (создайте из `env.example`)

## Быстрый деплой

### 1. Подготовка на сервере

```bash
# Создайте директорию для проекта
mkdir -p ~/comp-site-analyz
cd ~/comp-site-analyz

# Скопируйте файлы на сервер:
# - scripts/docker-compose.prod.yml
# - env.example (переименуйте в .env и заполните)
# - scripts/stop_app.py (опционально, для управления приложением)
```

### 2. Настройка переменных окружения

```bash
# Скопируйте пример
cp env.example .env

# Отредактируйте .env и укажите свои значения
nano .env
```

Минимально необходимые переменные:

```env
OPENAI_API_KEY=your_proxyapi_key_here
OPENAI_API_BASE=https://api.proxyapi.ru/openai/v1
```

### 3. Запуск приложения

```bash
# Запустите контейнер из образа Docker Hub
docker-compose -f scripts/docker-compose.prod.yml up -d
```

Готово! Приложение доступно на порту 5000.

**Особенности запуска:**

- При запуске приложение автоматически проверяет наличие предыдущих экземпляров
- Если обнаружен запущенный процесс - он принудительно завершается
- Проверяется занятость порта (до 10 попыток освобождения)
- Создается PID файл для отслеживания запущенного экземпляра

## Обновление приложения

После публикации нового образа на Docker Hub:

```bash
# Обновите образ
docker-compose -f scripts/docker-compose.prod.yml pull

# Перезапустите контейнер
docker-compose -f scripts/docker-compose.prod.yml up -d
```

## Проверка работы

```bash
# Проверка статуса
docker-compose -f scripts/docker-compose.prod.yml ps

# Просмотр логов
docker-compose -f scripts/docker-compose.prod.yml logs -f

# Проверка в браузере
curl http://localhost:5000
```

## Остановка

```bash
docker-compose -f scripts/docker-compose.prod.yml down
```

## Альтернативный вариант (без docker-compose)

Если docker-compose недоступен:

```bash
# Запуск напрямую
docker run -d \
  --name comp-site-analyz \
  -p 5000:5000 \
  --env-file .env \
  --restart unless-stopped \
  avardous/comp_site_analyz:latest

# Обновление
docker stop comp-site-analyz
docker rm comp-site-analyz
docker pull avardous/comp_site_analyz:latest
docker run -d \
  --name comp-site-analyz \
  -p 5000:5000 \
  --env-file .env \
  --restart unless-stopped \
  avardous/comp_site_analyz:latest
```

## Минимальный набор файлов для деплоя

Для деплоя достаточно скопировать на сервер:

1. `scripts/docker-compose.prod.yml` - конфигурация
2. `.env` - переменные окружения (создать из `env.example`)

**Больше ничего не нужно!** Образ загружается автоматически из Docker Hub.

## Особенности работы приложения

### Защита от повторного запуска

Приложение имеет встроенную защиту от одновременного запуска нескольких экземпляров:

- **PID файл** - создается автоматически при запуске, удаляется при завершении
- **Проверка порта** - автоматическое завершение процессов на занятом порту (до 10 попыток)
- **Автоматическое завершение** - предыдущие экземпляры завершаются принудительно

В Docker контейнере это работает так же, как и при локальном запуске.

### Поддержка разных портов

Можно запустить приложение на любом порту через переменную `FLASK_PORT`:

```env
FLASK_PORT=5001  # или 8000, 8080 и т.д.
```

Полезно, если:

- Порт 5000 уже занят другим приложением
- Нужно запустить несколько экземпляров на одной машине (на разных портах)
- Требуется использовать стандартный порт веб-сервера

## Устранение проблем

### Порт занят, приложение не запускается

Если при запуске появляется сообщение о том, что порт занят:

1. **Завершите предыдущий контейнер:**

   ```bash
   docker-compose -f scripts/docker-compose.prod.yml down
   docker ps | grep comp-site-analyz | awk '{print $1}' | xargs docker kill
   ```

2. **Или измените порт в `.env`:**

   ```env
   FLASK_PORT=5001
   ```

   И обновите `scripts/docker-compose.prod.yml`:

   ```yaml
   ports:
     - "5001:5001"
   ```

### Контейнер не доступен извне

Если контейнер запущен, но недоступен по сети:

1. Проверьте, что порт проброшен: `docker ps` должен показывать `0.0.0.0:5000->5000/tcp`
2. Убедитесь, что `FLASK_HOST=0.0.0.0` в переменных окружения
3. Проверьте настройки файрвола на сервере

### CrewAI не доступен

Если после деплоя появляется ошибка "CrewAI не доступен":

1. **Проверьте логи контейнера:**

   ```bash
   docker logs comp-site-analyz
   ```

   Ищите сообщения об ошибках при импорте или создании агентов.

2. **Проверьте установку CrewAI в контейнере:**

   ```bash
   docker exec comp-site-analyz python -c "import crewai; print(crewai.__version__)"
   ```

3. **Проверьте переменные окружения:**

   ```bash
   docker exec comp-site-analyz env | grep OPENAI
   ```

   Убедитесь, что `OPENAI_API_KEY` установлен.

4. **Пересоберите образ** (если проблема в сборке):

   ```bash
   docker-compose -f scripts/docker-compose.prod.yml build --no-cache
   docker-compose -f scripts/docker-compose.prod.yml up -d
   ```

5. **Проверьте логи при запуске:**

   При запуске контейнера должны появиться сообщения:

   - `✓ Web Scraper Agent создан успешно`
   - `✓ Data Analyzer Agent создан успешно`
   - `✓ BI Engineer Agent создан успешно`
   - `✓ Task 1 (scrape) создана успешно`
   - `✓ Task 2 (analyze) создана успешно`
   - `✓ Task 3 (report) создана успешно`
   - `✓ Crew объект создан успешно`
   - `✓ CrewAI успешно инициализирован`

   Если какое-то сообщение отсутствует, проверьте логи для детальной информации.

### Контейнер падает при запуске

Если контейнер сразу падает после запуска:

1. **Проверьте логи:**

   ```bash
   docker logs comp-site-analyz
   ```

2. **Проверьте переменные окружения:**

   Убедитесь, что файл `.env` содержит все необходимые переменные

3. **Проверьте образ:**

   ```bash
   docker pull avardous/comp_site_analyz:latest
   ```

4. **Перезапустите контейнер:**

   ```bash
   docker-compose -f scripts/docker-compose.prod.yml down
   docker-compose -f scripts/docker-compose.prod.yml up -d
   ```

