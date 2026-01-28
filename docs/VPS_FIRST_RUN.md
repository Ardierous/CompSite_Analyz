# Первый запуск на VPS - пошаговая инструкция

## Полная последовательность команд для первого запуска

### Шаг 1: Подключение к серверу

```bash
ssh user@45.133.245.186
```

### Шаг 2: Установка необходимых инструментов (если не установлены)

```bash
# Обновление пакетов
sudo apt update

# Установка Git (если не установлен)
sudo apt install -y git

# Установка Docker (если не установлен)
sudo apt install -y docker.io docker-compose

# Добавление пользователя в группу docker (чтобы не использовать sudo)
sudo usermod -aG docker $USER

# Перезагрузка сессии (или выйдите и войдите снова)
newgrp docker
```

### Шаг 3: Клонирование проекта

```bash
# Переход в домашнюю директорию
cd ~

# Клонирование репозитория
git clone <ваш-git-репозиторий> comp-site-analyz

# Или если репозиторий приватный, используйте:
# git clone https://github.com/ваш-username/ваш-репозиторий.git comp-site-analyz

# Переход в директорию проекта
cd comp-site-analyz
```

**Если нет Git репозитория**, скачайте файлы вручную:

```bash
# Создайте директорию
mkdir -p ~/comp-site-analyz
cd ~/comp-site-analyz
mkdir -p scripts

# Скопируйте файлы через scp с локального компьютера:
# scp scripts/docker-compose.prod.yml user@45.133.245.186:~/comp-site-analyz/scripts/
# scp env.example user@45.133.245.186:~/comp-site-analyz/
```

### Шаг 4: Настройка переменных окружения

```bash
cd ~/comp-site-analyz

# Создание .env файла из примера
cp env.example .env

# Редактирование .env файла
nano .env
```

**В файле `.env` укажите:**

```env
# OpenAI API (ProxyAPI)
OPENAI_API_KEY=your_proxyapi_key_here
OPENAI_API_BASE=https://api.proxyapi.ru/openai/v1

# Flask настройки
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=False
```

**Сохранение в nano:** `Ctrl+O`, `Enter`, `Ctrl+X`

### Шаг 5: Настройка файрвола

```bash
cd ~/comp-site-analyz

# Сделайте скрипт исполняемым
chmod +x scripts/setup_firewall.sh

# Запустите скрипт настройки файрвола
sudo bash scripts/setup_firewall.sh
```

### Шаг 6: Запуск контейнера

```bash
cd ~/comp-site-analyz

# Запуск контейнера из образа Docker Hub
docker-compose -f scripts/docker-compose.prod.yml up -d
```

### Шаг 7: Проверка работы

```bash
# Проверка статуса контейнера
docker-compose -f scripts/docker-compose.prod.yml ps

# Просмотр логов (первые 50 строк)
docker-compose -f scripts/docker-compose.prod.yml logs --tail=50

# Проверка доступности локально
curl http://localhost:5000

# Проверка файрвола
sudo ufw status | grep 5000
```

### Шаг 8: Проверка извне

Откройте в браузере:
```
http://45.133.245.186:5000
```

## Полная последовательность команд (одним блоком)

Скопируйте и выполните все команды последовательно:

```bash
# 1. Установка Docker и Git (если не установлены)
sudo apt update
sudo apt install -y git docker.io docker-compose
sudo usermod -aG docker $USER
newgrp docker

# 2. Клонирование проекта
cd ~
git clone <ваш-git-репозиторий> comp-site-analyz
cd comp-site-analyz

# 3. Создание .env файла
cp env.example .env
echo "⚠️  ВАЖНО: Отредактируйте .env файл: nano .env"
echo "   Минимально необходимые переменные:"
echo "   OPENAI_API_KEY=your_proxyapi_key_here"
echo "   OPENAI_API_BASE=https://api.proxyapi.ru/openai/v1"
read -p "Нажмите Enter после редактирования .env файла..."

# 4. Настройка файрвола
chmod +x scripts/setup_firewall.sh
sudo bash scripts/setup_firewall.sh

# 5. Запуск контейнера
docker-compose -f scripts/docker-compose.prod.yml up -d

# 6. Ожидание запуска
echo "⏳ Ожидание запуска контейнера (15 секунд)..."
sleep 15

# 7. Проверка статуса
echo "📊 Статус контейнера:"
docker-compose -f scripts/docker-compose.prod.yml ps

echo ""
echo "📋 Логи (последние 30 строк):"
docker-compose -f scripts/docker-compose.prod.yml logs --tail=30

echo ""
echo "✅ Готово! Приложение должно быть доступно по адресу:"
echo "   http://45.133.245.186:5000"
echo ""
echo "📋 Полезные команды:"
echo "   Логи в реальном времени: docker-compose -f scripts/docker-compose.prod.yml logs -f"
echo "   Остановка: docker-compose -f scripts/docker-compose.prod.yml down"
echo "   Перезапуск: docker-compose -f scripts/docker-compose.prod.yml restart"
echo "   Статус: docker-compose -f scripts/docker-compose.prod.yml ps"
```

## Минимальная версия (если Docker и Git уже установлены)

```bash
# 1. Клонирование
cd ~
git clone <ваш-git-репозиторий> comp-site-analyz
cd comp-site-analyz

# 2. Настройка .env
cp env.example .env
nano .env  # Отредактируйте и сохраните

# 3. Настройка файрвола
chmod +x scripts/setup_firewall.sh
sudo bash scripts/setup_firewall.sh

# 4. Запуск
docker-compose -f scripts/docker-compose.prod.yml up -d

# 5. Проверка
sleep 10
docker-compose -f scripts/docker-compose.prod.yml ps
docker-compose -f scripts/docker-compose.prod.yml logs --tail=20
```

## Если нет Git репозитория

Если проект еще не в Git, используйте этот вариант:

```bash
# 1. Создание структуры
mkdir -p ~/comp-site-analyz/scripts
cd ~/comp-site-analyz

# 2. Создание .env
cat > .env << 'EOF'
OPENAI_API_KEY=your_proxyapi_key_here
OPENAI_API_BASE=https://api.proxyapi.ru/openai/v1
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=False
EOF

# 3. Создание docker-compose.prod.yml
cat > scripts/docker-compose.prod.yml << 'EOF'
version: '3.8'

services:
  web:
    image: avardous/comp_site_analyz:latest
    container_name: comp-site-analyz
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - FLASK_DEBUG=False
      - FLASK_HOST=0.0.0.0
      - FLASK_PORT=5000
      - PYTHONUNBUFFERED=1
    env_file:
      - ../.env
    restart: unless-stopped
EOF

# 4. Редактирование .env
nano .env  # Укажите свой OPENAI_API_KEY

# 5. Настройка файрвола (если скрипт доступен)
# chmod +x scripts/setup_firewall.sh
# sudo bash scripts/setup_firewall.sh

# Или вручную:
sudo ufw allow 5000/tcp
sudo ufw allow 22/tcp
sudo ufw enable

# 6. Запуск
docker-compose -f scripts/docker-compose.prod.yml up -d

# 7. Проверка
sleep 10
docker-compose -f scripts/docker-compose.prod.yml ps
docker-compose -f scripts/docker-compose.prod.yml logs --tail=20
```

## Устранение проблем

### Проблема: Docker не установлен

```bash
# Установка Docker
sudo apt update
sudo apt install -y docker.io docker-compose

# Добавление пользователя в группу docker
sudo usermod -aG docker $USER
newgrp docker

# Проверка установки
docker --version
docker-compose --version
```

### Проблема: Нет прав на Docker

```bash
# Добавление пользователя в группу docker
sudo usermod -aG docker $USER
newgrp docker

# Или используйте sudo перед командами docker
sudo docker-compose -f scripts/docker-compose.prod.yml up -d
```

### Проблема: Порт 5000 занят

```bash
# Проверка, что занимает порт
sudo netstat -tlnp | grep :5000

# Остановка процесса или контейнера
docker stop comp-site-analyz 2>/dev/null || true
docker rm comp-site-analyz 2>/dev/null || true

# Или измените порт в docker-compose.prod.yml на 5001:5000
```

### Проблема: Образ не найден

```bash
# Проверка подключения к Docker Hub
docker pull avardous/comp_site_analyz:latest

# Если образ не найден, убедитесь, что он опубликован в Docker Hub
# или используйте локальную сборку (см. документацию)
```

## Следующие шаги

После успешного запуска:

1. **Проверьте работу:** Откройте `http://45.133.245.186:5000` в браузере
2. **Настройте мониторинг:** Используйте `docker-compose logs -f` для просмотра логов
3. **Настройте автообновление:** Используйте cron для автоматического обновления образа

## Автоматическое обновление (опционально)

Для автоматического обновления образа каждый день в 3:00:

```bash
# Создание cron задачи
crontab -e

# Добавьте строку:
0 3 * * * cd ~/comp-site-analyz && docker-compose -f scripts/docker-compose.prod.yml pull && docker-compose -f scripts/docker-compose.prod.yml up -d
```

