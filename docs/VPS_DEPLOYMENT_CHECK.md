# Проверка конфигурации для деплоя на VPS

**Дата проверки:** 2025-12-27  
**VPS IP:** 45.133.245.186  
**ОС:** Ubuntu 20.04 LTS  
**Целевой URL:** http://45.133.245.186:5000/

## ✅ Проверка Dockerfile

### Переменные окружения

```dockerfile
ENV FLASK_HOST=0.0.0.0 \
    FLASK_PORT=5000 \
    FLASK_DEBUG=False
```

- ✅ `FLASK_HOST=0.0.0.0` - приложение будет слушать на всех интерфейсах (доступно извне)
- ✅ `FLASK_PORT=5000` - порт внутри контейнера
- ✅ `EXPOSE 5000` - порт объявлен для Docker

### Команда запуска

```dockerfile
CMD ["python", "main.py"]
```

- ✅ Приложение запускается через `main.py`
- ✅ Использует переменные окружения из Dockerfile

## ✅ Проверка docker-compose.prod.yml

### Конфигурация сервиса

```yaml
services:
  web:
    image: avardous/comp_site_analyz:latest
    container_name: comp-site-analyz
    ports:
      - "5000:5000"  # Хост:Контейнер
    environment:
      - FLASK_HOST=0.0.0.0
      - FLASK_PORT=5000
      - FLASK_DEBUG=False
    env_file:
      - ../.env
    restart: unless-stopped
```

- ✅ **Образ:** `avardous/comp_site_analyz:latest` (из Docker Hub)
- ✅ **Проброс порта:** `5000:5000` (хост → контейнер)
- ✅ **FLASK_HOST=0.0.0.0** - принимает подключения извне
- ✅ **FLASK_PORT=5000** - порт внутри контейнера
- ✅ **restart: unless-stopped** - автоматический перезапуск

### Путь к .env файлу

```yaml
env_file:
  - ../.env
```

- ✅ Путь правильный, если запускать из корня проекта (`~/comp-site-analyz/`)
- ✅ Структура: `~/comp-site-analyz/.env` и `~/comp-site-analyz/scripts/docker-compose.prod.yml`

## ✅ Проверка main.py

### Чтение переменных окружения

```python
FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
```

- ✅ Использует переменные из окружения (из Dockerfile или docker-compose)
- ✅ Значения по умолчанию: `0.0.0.0:5000` (правильно для Docker)

### Запуск Flask

```python
app.run(debug=FLASK_DEBUG, host=FLASK_HOST, port=FLASK_PORT, use_reloader=True)
```

- ✅ Использует `FLASK_HOST` и `FLASK_PORT` из переменных окружения
- ✅ В production режиме (`FLASK_DEBUG=False`) reloader не создает проблем

### Определение Docker окружения

```python
def is_running_in_docker():
    # Проверяет наличие /.dockerenv или cgroup
    ...
```

- ✅ В Docker контейнере пропускается проверка порта (Docker сам управляет портами)
- ✅ Это предотвращает конфликты при запуске

## ✅ Проверка сетевой конфигурации

### Внутри контейнера

1. Приложение слушает на: `0.0.0.0:5000` (все интерфейсы)
2. Порт контейнера: `5000`

### Проброс порта

1. Docker пробрасывает: `5000:5000` (хост → контейнер)
2. Приложение доступно на хосте: `localhost:5000`

### Доступ извне

1. Если файрвол открыт: `http://45.133.245.186:5000`
2. Если файрвол закрыт: нужно открыть порт 5000

## ✅ Проверка файрвола (Ubuntu 20.04)

Ubuntu 20.04 использует UFW. Для доступа извне нужно:

```bash
sudo ufw allow 5000/tcp
sudo ufw status | grep 5000
```

- ✅ Порт должен быть открыт в UFW
- ✅ Проверка: `sudo ufw status`

## ✅ Итоговая проверка

### Что должно работать:

1. ✅ **Dockerfile** устанавливает `FLASK_HOST=0.0.0.0` и `FLASK_PORT=5000`
2. ✅ **docker-compose.prod.yml** пробрасывает порт `5000:5000`
3. ✅ **main.py** использует переменные окружения для хоста и порта
4. ✅ **Приложение слушает на `0.0.0.0:5000`** внутри контейнера
5. ✅ **Docker пробрасывает порт** на хост `5000:5000`
6. ✅ **Файрвол должен быть настроен** для доступа извне

### Команды для проверки на VPS:

```bash
# 1. Проверка статуса контейнера
docker-compose -f scripts/docker-compose.prod.yml ps

# 2. Проверка логов
docker-compose -f scripts/docker-compose.prod.yml logs -f

# 3. Проверка порта на хосте
sudo netstat -tlnp | grep :5000

# 4. Проверка изнутри контейнера
docker exec comp-site-analyz netstat -tlnp | grep :5000

# 5. Проверка доступности локально
curl http://localhost:5000

# 6. Проверка доступности извне (с другого компьютера)
curl http://45.133.245.186:5000
```

## ⚠️ Потенциальные проблемы

### 1. Файрвол не настроен

**Симптом:** Приложение работает локально, но недоступно извне

**Решение:**
```bash
sudo ufw allow 5000/tcp
sudo ufw reload
```

### 2. Порт занят на хосте

**Симптом:** Docker не может пробросить порт 5000

**Решение:**
```bash
# Проверить, что занимает порт
sudo netstat -tlnp | grep :5000

# Остановить предыдущий контейнер
docker-compose -f scripts/docker-compose.prod.yml down
```

### 3. .env файл не найден

**Симптом:** Ошибка при запуске контейнера

**Решение:**
```bash
# Убедиться, что .env в корне проекта
ls -la ~/comp-site-analyz/.env

# Проверить путь в docker-compose.prod.yml
# Должно быть: env_file: - ../.env
```

### 4. Образ не найден

**Симптом:** `Error: image avardous/comp_site_analyz:latest not found`

**Решение:**
```bash
# Убедиться, что образ опубликован на Docker Hub
docker pull avardous/comp_site_analyz:latest
```

## ✅ Вывод

**Конфигурация правильная для запуска на VPS:**

- ✅ Dockerfile правильно настроен (`FLASK_HOST=0.0.0.0`, `FLASK_PORT=5000`)
- ✅ docker-compose.prod.yml правильно пробрасывает порт (`5000:5000`)
- ✅ main.py использует переменные окружения
- ✅ Приложение будет слушать на `0.0.0.0:5000` внутри контейнера
- ✅ Docker пробросит порт на хост `5000:5000`
- ✅ Приложение будет доступно по адресу `http://45.133.245.186:5000` (если файрвол настроен)

**Единственное требование:** Настроить файрвол UFW для открытия порта 5000.

