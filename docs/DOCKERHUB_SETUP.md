# Инструкция по публикации на Docker Hub

Это руководство поможет вам опубликовать Docker образ вашего приложения на Docker Hub.

## Предварительные требования

1. **Установленный Docker**
   - Убедитесь, что Docker установлен и запущен
   - Проверьте: `docker --version`

2. **Аккаунт на Docker Hub**
   - Зарегистрируйтесь на [hub.docker.com](https://hub.docker.com)
   - Создайте репозиторий для вашего образа (или используйте существующий)

3. **Python 3.x** (для скрипта публикации)

## Быстрый старт

### Вариант 1: Использование скрипта (рекомендуется)

#### Windows:

```bash
scripts/push_dockerhub.bat
```

#### Linux/Mac:

```bash
python3 scripts/push_to_dockerhub.py
```

Скрипт автоматически:

1. Соберет Docker образ
2. Попросит ввести данные для входа в Docker Hub
3. Опубликует образ на Docker Hub

### Вариант 2: Ручная публикация

#### 1. Сборка образа

```bash
docker build -t ваш-username/company-analyzer:latest .
```

Замените `ваш-username` на ваш Docker Hub username.

#### 2. Вход в Docker Hub

```bash
docker login
```

Введите ваш Docker Hub username и пароль (или токен доступа).

#### 3. Публикация образа

```bash
docker push ваш-username/company-analyzer:latest
```

## Использование переменных окружения

Вы можете задать параметры через переменные окружения:

```bash
# Windows (PowerShell)
$env:DOCKER_USERNAME="ваш-username"
$env:DOCKER_REPO="company-analyzer"
$env:DOCKER_TAG="v1.0.0"

# Linux/Mac
export DOCKER_USERNAME="ваш-username"
export DOCKER_REPO="company-analyzer"
export DOCKER_TAG="v1.0.0"
```

Затем запустите скрипт:

```bash
python scripts/push_to_dockerhub.py
```

## Использование опубликованного образа

После успешной публикации образа на Docker Hub, вы можете использовать его несколькими способами:

### Вариант 1: Использование docker-compose.prod.yml (рекомендуется)

Для продакшена используйте готовый файл `scripts/docker-compose.prod.yml`:

```bash
docker-compose -f scripts/docker-compose.prod.yml up -d
```

Этот файл использует опубликованный образ `avardous/comp_site_analyz:latest` из Docker Hub.

### Вариант 2: Запуск образа напрямую

```bash
docker run -d \
  --name comp-site-analyz \
  -p 5000:5000 \
  --env-file .env \
  --restart unless-stopped \
  avardous/comp_site_analyz:latest
```

Или с конкретной версией:

```bash
docker run -d \
  --name comp-site-analyz \
  -p 5000:5000 \
  --env-file .env \
  --restart unless-stopped \
  avardous/comp_site_analyz:20251227-163644
```

### Вариант 3: Обновление docker-compose.yml

Если хотите использовать образ из Docker Hub в основном `scripts/docker-compose.yml`, закомментируйте `build` и раскомментируйте `image`:

```yaml
services:
  web:
    # build: .
    image: avardous/comp_site_analyz:latest
    # ... остальные настройки
```

### Обновление образа

Для получения последней версии образа:

```bash
# Остановите контейнер
docker-compose -f scripts/docker-compose.prod.yml down

# Обновите образ
docker pull avardous/comp_site_analyz:latest

# Запустите снова
docker-compose -f scripts/docker-compose.prod.yml up -d
```

### Разница между режимами

- **scripts/docker-compose.yml** - для разработки (hot reload, локальная сборка)
- **scripts/docker-compose.prod.yml** - для продакшена (образ из Docker Hub, без hot reload)

### Запуск на удаленном сервере

1. Войдите в Docker Hub на сервере:

   ```bash
   docker login
   ```

2. Запустите образ:

   ```bash
   docker run -d \
     --name company-analyzer \
     -p 5000:5000 \
     --env-file .env \
     --restart unless-stopped \
     ваш-username/company-analyzer:latest
   ```

## Переменные окружения для контейнера

Убедитесь, что файл `.env` содержит необходимые переменные:

```env
# OpenAI API (ProxyAPI)
OPENAI_API_KEY=your_api_key_here
OPENAI_API_BASE=https://api.proxyapi.ru/openai/v1

# Flask настройки
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=False
```

## Версионирование образов

Рекомендуется использовать теги для версионирования:

```bash
# Сборка с версией
docker build -t ваш-username/company-analyzer:v1.0.0 .

# Публикация версии
docker push ваш-username/company-analyzer:v1.0.0

# Также публикуйте latest
docker tag ваш-username/company-analyzer:v1.0.0 ваш-username/company-analyzer:latest
docker push ваш-username/company-analyzer:latest
```

## Проверка опубликованного образа

После публикации проверьте образ на Docker Hub:

- Откройте: `https://hub.docker.com/r/ваш-username/company-analyzer`
- Убедитесь, что образ виден и доступен для скачивания

## Устранение проблем

### Ошибка: "denied: requested access to the resource is denied"

- Убедитесь, что вы вошли в Docker Hub: `docker login`
- Проверьте, что имя репозитория соответствует вашему username

### Ошибка: "unauthorized: authentication required"

- Проверьте правильность username и пароля
- Для безопасности используйте токен доступа вместо пароля

### Ошибка при сборке образа

- Проверьте, что Dockerfile находится в корне проекта
- Убедитесь, что все необходимые файлы присутствуют
- Проверьте логи сборки: `docker build --no-cache -t test .`

## Безопасность

⚠️ **Важно:**

- Никогда не публикуйте файлы с секретами (`.env`, ключи API)
- Используйте `.dockerignore` для исключения чувствительных файлов
- Используйте Docker secrets или переменные окружения для секретов
- Регулярно обновляйте базовые образы для получения исправлений безопасности

## Дополнительные ресурсы

- [Docker Hub Documentation](https://docs.docker.com/docker-hub/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [Dockerfile Reference](https://docs.docker.com/reference/dockerfile/)

