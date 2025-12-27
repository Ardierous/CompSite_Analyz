# Разработка с Docker и Hot Reload

Это руководство поможет настроить hot reload для разработки, чтобы изменения в коде применялись автоматически без пересборки контейнера.

## Быстрый старт

### Вариант 1: Использование docker-compose.yml (рекомендуется)

```bash
docker-compose up
```

Контейнер автоматически перезагрузится при изменении файлов `.py`, `.html`, `.css`, `.js`.

### Вариант 2: Использование docker-compose.dev.yml

```bash
docker-compose -f docker-compose.dev.yml up
```

## Как это работает

1. **Volume Mounting**: Код монтируется в контейнер через volume (`.:/app`)
2. **Flask Debug Mode**: Включен режим отладки (`FLASK_DEBUG=True`)
3. **Автоматическая перезагрузка**: Flask отслеживает изменения файлов и перезагружает приложение

## Что отслеживается

Flask автоматически перезагружает приложение при изменении:

- Python файлов (`.py`)
- HTML шаблонов (`.html`)
- Статических файлов (`.css`, `.js`)

## Важные замечания

### Первая сборка

При первом запуске нужно собрать образ:

```bash
docker-compose build
# или
docker-compose -f scripts/docker-compose.yml up --build
```

### После изменения зависимостей

Если вы изменили `requirements.txt`, нужно пересобрать образ:

```bash
docker-compose -f scripts/docker-compose.yml build
docker-compose -f scripts/docker-compose.yml up
```

### Изменения в Dockerfile

Если вы изменили `Dockerfile`, обязательно пересоберите:

```bash
docker-compose -f scripts/docker-compose.yml build --no-cache
docker-compose -f scripts/docker-compose.yml up
```

## Отладка

### Проверка, что hot reload работает

1. Запустите контейнер:

   ```bash
   docker-compose -f scripts/docker-compose.yml up
   ```

2. Внесите изменение в любой `.py` файл (например, добавьте `print("test")`)

3. В логах контейнера вы должны увидеть:

   ```
   * Detected change in 'main.py', reloading
   * Restarting with stat
   ```

### Если hot reload не работает

1. **Проверьте переменные окружения:**

   ```bash
   docker-compose -f scripts/docker-compose.yml exec web env | grep FLASK
   ```

   Должно быть: `FLASK_DEBUG=True` и `FLASK_ENV=development`

2. **Проверьте монтирование volumes:**

   ```bash
   docker-compose -f scripts/docker-compose.yml exec web ls -la /app
   ```

   Должны быть видны ваши файлы

3. **Перезапустите контейнер:**

   ```bash
   docker-compose -f scripts/docker-compose.yml restart
   ```

## Остановка

```bash
docker-compose -f scripts/docker-compose.yml down
```

## Продакшен режим

Для продакшена используйте отдельную конфигурацию или установите:

```yaml
environment:
  - FLASK_ENV=production
  - FLASK_DEBUG=False
```

## Полезные команды

```bash
# Просмотр логов
docker-compose -f scripts/docker-compose.yml logs -f web

# Выполнение команд в контейнере
docker-compose -f scripts/docker-compose.yml exec web python -c "print('test')"

# Пересборка без кеша
docker-compose -f scripts/docker-compose.yml build --no-cache

# Остановка и удаление контейнеров
docker-compose -f scripts/docker-compose.yml down

# Остановка, удаление контейнеров и volumes
docker-compose -f scripts/docker-compose.yml down -v
```

