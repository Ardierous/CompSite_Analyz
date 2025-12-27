# Работа с Docker контейнерами

## Проблема: Вижу образы, но не вижу контейнеров

Если в Docker Desktop вы видите образы, но не видите контейнеры, это означает, что контейнеры еще не были запущены. Образы - это "шаблоны" для контейнеров, а контейнеры - это запущенные экземпляры образов.

## Быстрый запуск

### Вариант 1: Ручной запуск через docker-compose

#### Режим разработки (с hot reload):

```bash
docker-compose up -d
```

#### Режим продакшена (образ из Docker Hub):

```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Вариант 2: Запуск напрямую через Docker

```bash
docker run -d \
  --name comp-site-analyz \
  -p 5000:5000 \
  --env-file .env \
  --restart unless-stopped \
  avardous/comp_site_analyz:latest
```

## Проверка статуса контейнеров

### В Docker Desktop:

1. Откройте Docker Desktop
2. Перейдите на вкладку "Containers"
3. Вы должны увидеть запущенные контейнеры

### Через командную строку:

```bash
# Показать запущенные контейнеры
docker ps

# Показать все контейнеры (включая остановленные)
docker ps -a

# Проверить контейнеры через docker-compose
docker-compose -f scripts/docker-compose.yml ps
```

## Просмотр логов

```bash
# Логи для режима разработки
docker-compose logs -f

# Логи для режима продакшена
docker-compose -f docker-compose.prod.yml logs -f

# Логи конкретного контейнера
docker logs -f comp-site-analyz
```

## Остановка контейнеров

```bash
# Остановить контейнеры разработки
docker-compose -f scripts/docker-compose.yml down

# Остановить контейнеры продакшена
docker-compose -f scripts/docker-compose.prod.yml down

# Остановить конкретный контейнер
docker stop comp-site-analyz

# Удалить контейнер
docker rm comp-site-analyz
```

## Устранение проблем

### Контейнер не запускается

1. **Проверьте логи:**

   ```bash
   docker-compose logs
   ```

2. **Проверьте, что порт 5000 свободен:**

   ```bash
   # Windows
   netstat -ano | findstr :5000
   
   # Linux/Mac
   lsof -i :5000
   ```

3. **Проверьте файл .env:**

   Убедитесь, что файл `.env` существует и содержит необходимые переменные.

### Контейнер запускается, но сразу останавливается

1. **Проверьте логи:**

   ```bash
   docker-compose -f scripts/docker-compose.yml logs --tail=50
   ```

2. **Проверьте переменные окружения:**

   ```bash
   docker-compose -f scripts/docker-compose.yml exec web env
   ```

3. **Запустите контейнер в интерактивном режиме:**

   ```bash
   docker-compose -f scripts/docker-compose.yml run --rm web python main.py
   ```

### Ошибка NumPy (несовместимость архитектуры)

Если в логах видна ошибка:

```
RuntimeError: NumPy was built with baseline optimizations: (X86_V2) but your machine doesn't support: (X86_V2)
```

**Причина**: NumPy 2.x использует оптимизации, которые могут быть несовместимы с некоторыми процессорами.

**Решение**:

1. Образ уже содержит исправленную версию NumPy (<2.0)
2. Если проблема сохраняется, пересоберите образ:

   ```bash
   docker-compose -f scripts/docker-compose.yml build --no-cache
   docker-compose -f scripts/docker-compose.yml up -d
   ```

### Ошибка прав доступа

Если возникает ошибка:

```
PermissionError: [Errno 13] Permission denied: '/home/appuser'
```

**Решение**: Dockerfile настроен для автоматического создания домашней директории. Пересоберите образ:

```bash
docker-compose -f scripts/docker-compose.yml build --no-cache
docker-compose -f scripts/docker-compose.yml up -d
```

### Контейнер не виден в Docker Desktop

1. **Обновите список контейнеров** в Docker Desktop (кнопка обновления)
2. **Проверьте фильтры** - возможно, включен фильтр "Running only"
3. **Проверьте через командную строку:**

   ```bash
   docker ps -a
   ```

## Полезные команды

```bash
# Перезапустить контейнер
docker-compose -f scripts/docker-compose.yml restart

# Пересобрать и запустить
docker-compose -f scripts/docker-compose.yml up -d --build

# Показать использование ресурсов
docker stats

# Войти в контейнер
docker-compose -f scripts/docker-compose.yml exec web bash
# или
docker exec -it comp-site-analyz bash

# Показать информацию о контейнере
docker inspect comp-site-analyz
```

## Проверка работы приложения

После запуска контейнера откройте в браузере:

```
http://localhost:5000
```

Если приложение работает, вы увидите главную страницу.

## Технические детали образа

Образ настроен для стабильной работы:

- **NumPy**: версия <2.0 (совместимость с различными архитектурами)
- **Пользователь**: non-root (`appuser`) для безопасности
- **Хост**: `0.0.0.0` по умолчанию (доступ извне контейнера)
- **Порт**: 5000 (пробрасывается наружу)
- **Автоперезапуск**: `unless-stopped` (автоматический перезапуск при сбоях)

