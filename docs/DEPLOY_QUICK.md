# Быстрый деплой на VPS (ihor)

## Подготовка на сервере

1. **Подключитесь к серверу:**
   ```bash
   ssh user@45.133.245.186
   ```

2. **Создайте директорию проекта:**
   ```bash
   mkdir -p ~/comp-site-analyz
   cd ~/comp-site-analyz
   ```

3. **Создайте структуру папок:**
   ```bash
   mkdir -p scripts
   ```

4. **Скопируйте файлы на сервер:**
   - `scripts/docker-compose.prod.yml` → `~/comp-site-analyz/scripts/docker-compose.prod.yml`
   - `env.example` → `~/comp-site-analyz/.env` (и заполните его)

## Настройка .env файла

Создайте файл `.env` в корне проекта (`~/comp-site-analyz/.env`):

```env
# OpenAI API (ProxyAPI)
OPENAI_API_KEY=your_proxyapi_key_here
OPENAI_API_BASE=https://api.proxyapi.ru/openai/v1

# Flask настройки
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=False
```

## Запуск приложения

**ВАЖНО:** Запускайте команду из корня проекта (`~/comp-site-analyz/`):

### Вариант 1: Автоматический запуск (рекомендуется)

```bash
cd ~/comp-site-analyz

# Сделайте скрипт исполняемым
chmod +x scripts/start_app.sh

# Запустите скрипт (потребуются права root для настройки файрвола)
sudo bash scripts/start_app.sh
```

Скрипт автоматически:
- Настраивает файрвол (открывает порт 5000)
- Проверяет наличие `.env` файла
- Останавливает предыдущий контейнер (если запущен)
- Запускает новый контейнер
- Проверяет доступность приложения

### Вариант 2: Ручной запуск

```bash
cd ~/comp-site-analyz

# Настройте файрвол (если еще не настроен)
sudo bash scripts/setup_firewall.sh

# Перед запуском убедитесь, что порт 5000 свободен на хосте
# (если запускаете впервые, этот шаг можно пропустить)
sudo netstat -tlnp | grep :5000

# Если порт занят предыдущим контейнером, остановите его:
docker-compose -f scripts/docker-compose.prod.yml down

# Запустите контейнер
docker-compose -f scripts/docker-compose.prod.yml up -d
```

**Примечание:** В контейнере приложение автоматически определяет, что оно запущено в Docker, и **не проверяет** занятость порта (это делает сам Docker). Если порт 5000 на хосте занят, Docker выдаст ошибку при запуске, и нужно будет остановить предыдущий контейнер или изменить порт.

## Проверка работы

```bash
# Проверка статуса контейнера
docker-compose -f scripts/docker-compose.prod.yml ps

# Просмотр логов
docker-compose -f scripts/docker-compose.prod.yml logs -f

# Проверка доступности
curl http://localhost:5000
```

## Доступ к приложению

После успешного запуска приложение будет доступно:

- **Локально на сервере:** `http://localhost:5000`
- **Извне (если порт открыт):** `http://45.133.245.186:5000`

## Настройка файрвола (Ubuntu 20.04)

Ubuntu 20.04 использует UFW (Uncomplicated Firewall) по умолчанию.

### Автоматическая настройка (рекомендуется)

```bash
# Запустите скрипт настройки файрвола
sudo bash scripts/setup_firewall.sh
```

Скрипт автоматически:
- Проверяет наличие UFW
- Открывает порт 5000 для входящих подключений
- Открывает SSH порт (22) для безопасности
- Активирует файрвол (если не активен)

### Ручная настройка

Если скрипт недоступен:

```bash
# Проверьте статус файрвола
sudo ufw status

# Откройте порт 5000
sudo ufw allow 5000/tcp

# Если файрвол не активен, активируйте его
sudo ufw enable

# Проверьте, что порт открыт
sudo ufw status | grep 5000
```

**Важно:** Если файрвол был только что включен, убедитесь, что SSH порт (обычно 22) открыт, иначе потеряете доступ к серверу:

```bash
# Откройте SSH порт перед включением файрвола
sudo ufw allow 22/tcp
sudo ufw enable
```

## Обновление приложения

### После изменений в коде (требуется пересборка образа)

Если были изменены `Dockerfile` или `requirements.txt`:

**На локальном компьютере:**

```bash
# Пересоберите образ
docker build -t avardous/comp_site_analyz:latest .

# Запушите в Docker Hub
docker push avardous/comp_site_analyz:latest

# Или используйте скрипт
python scripts/push_to_dockerhub.py
```

**На VPS:**

```bash
cd ~/comp-site-analyz

# Обновите образ из Docker Hub
docker-compose -f scripts/docker-compose.prod.yml pull

# Перезапустите контейнер
docker-compose -f scripts/docker-compose.prod.yml up -d
```

### Обновление без изменений в образе

Если образ уже обновлен в Docker Hub:

```bash
cd ~/comp-site-analyz
docker-compose -f scripts/docker-compose.prod.yml pull
docker-compose -f scripts/docker-compose.prod.yml up -d
```

## Остановка

```bash
cd ~/comp-site-analyz
docker-compose -f scripts/docker-compose.prod.yml down
```

## Структура на сервере

```
~/comp-site-analyz/
├── .env                    # Переменные окружения (создать из env.example)
└── scripts/
    └── docker-compose.prod.yml  # Конфигурация Docker Compose
```

## Откуда запускается приложение

Приложение запускается **из контейнера Docker**:

1. **Образ:** `avardous/comp_site_analyz:latest` (из Docker Hub)
2. **Команда запуска:** `python main.py` (указана в Dockerfile)
3. **Хост внутри контейнера:** `0.0.0.0` (принимает подключения извне)
4. **Порт внутри контейнера:** `5000`
5. **Проброс порта:** `5000:5000` (из контейнера на хост)

Таким образом:
- Приложение слушает на `0.0.0.0:5000` **внутри контейнера**
- Docker пробрасывает порт `5000` контейнера на порт `5000` хоста
- Приложение доступно по адресу `http://45.133.245.186:5000` (если порт открыт в файрволе)

