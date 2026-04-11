# HTTPS на VPS (Docker + Caddy)

После настройки DNS одна команда поднимает сайт с **Let’s Encrypt**, редиректом **HTTP → HTTPS** и **www → основной домен** (`iibox.ru`).

## Предусловия на VPS

- Записи **A** (или **AAAA**) для `iibox.ru` и `www.iibox.ru` указывают на IP сервера.
- Открыты порты **80** и **443** (и не заняты другими сервисами).
- Установлены Docker и Docker Compose v2.

## Шаги

1. Склонируйте репозиторий на VPS и перейдите в корень проекта.

2. Создайте `.env` из примера и укажите реальный API-ключ:

   ```bash
   cp .env.example .env
   nano .env
   ```

3. Запуск:

   ```bash
   docker compose pull
   docker compose up -d
   ```

## Проверки

```bash
docker compose ps
```

Оба контейнера (`app`, `caddy`) должны быть в статусе **Up**.

```bash
docker compose logs caddy
```

В логах Caddy должны быть строки об успешном получении сертификата (например, `certificate obtained successfully` или использование валидного сертификата).

В браузере:

- `https://iibox.ru` — сайт открывается.
- `http://iibox.ru` — редирект на `https://iibox.ru`.
- `https://www.iibox.ru` — редирект на `https://iibox.ru` (с сохранением пути).

Сертификаты хранятся в volume `caddy_data`; перезапуск контейнеров их не сбрасывает.

## Файлы

| Файл | Назначение |
|------|------------|
| `docker-compose.yml` | Сервисы `app` и `caddy`, сеть `web`, порты 80/443 (+ UDP 443 для HTTP/3) |
| `Caddyfile` | Редирект `www` → `iibox.ru`, прокси на `app:5000`, ACME |
| `.env.example` | Шаблон переменных без секретов |

Домены зашиты в `Caddyfile`. Для другого домена отредактируйте `Caddyfile` и при необходимости имя образа в `docker-compose.yml`.
