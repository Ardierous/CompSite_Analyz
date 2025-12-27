# Деплой на сервер

## Минимальный набор для деплоя

Для деплоя **НЕ нужно** собирать контейнеры локально. Используется готовый образ из Docker Hub.

## Необходимые файлы

1. `docker-compose.prod.yml` - конфигурация для продакшена
2. `.env` - переменные окружения (создайте из `env.example`)

## Быстрый деплой

### 1. Подготовка на сервере

```bash
# Создайте директорию для проекта
mkdir -p ~/comp-site-analyz
cd ~/comp-site-analyz

# Скопируйте файлы на сервер:
# - docker-compose.prod.yml
# - env.example (переименуйте в .env и заполните)
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
docker-compose -f docker-compose.prod.yml up -d
```

Готово! Приложение доступно на порту 5000.

## Обновление приложения

После публикации нового образа на Docker Hub:

```bash
# Обновите образ
docker-compose -f docker-compose.prod.yml pull

# Перезапустите контейнер
docker-compose -f docker-compose.prod.yml up -d
```

## Проверка работы

```bash
# Проверка статуса
docker-compose -f docker-compose.prod.yml ps

# Просмотр логов
docker-compose -f docker-compose.prod.yml logs -f

# Проверка в браузере
curl http://localhost:5000
```

## Остановка

```bash
docker-compose -f docker-compose.prod.yml down
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

1. `docker-compose.prod.yml` - конфигурация
2. `.env` - переменные окружения (создать из `env.example`)

**Больше ничего не нужно!** Образ загружается автоматически из Docker Hub.

