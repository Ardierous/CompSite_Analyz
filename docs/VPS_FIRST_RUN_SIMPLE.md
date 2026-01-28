# Первый запуск на VPS (Docker уже установлен)

## ⚠️ ВАЖНО: Как выполнять команды

**НЕ копируйте все команды разом!** Команда `nano .env` открывает интерактивный редактор.

**Вариант 1:** Выполняйте команды блоками (см. ниже)  
**Вариант 2:** Используйте полностью автоматический вариант (см. в конце)

---

## Полная последовательность команд (выполнять блоками)

### Блок 1: Создание структуры и .env файла

```bash
mkdir -p ~/comp-site-analyz/scripts
cd ~/comp-site-analyz
cat > .env << 'ENVEOF'
OPENAI_API_KEY=your_proxyapi_key_here
OPENAI_API_BASE=https://api.proxyapi.ru/openai/v1
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=False
ENVEOF
nano .env
```
**После выполнения:** Отредактируйте файл, укажите свой `OPENAI_API_KEY`, сохраните: `Ctrl+O`, `Enter`, `Ctrl+X`

### Блок 2: Создание docker-compose и настройка

```bash
cd ~/comp-site-analyz
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
sudo ufw allow 5000/tcp
sudo ufw allow 22/tcp
sudo ufw --force enable
```

### Блок 3: Запуск и проверка

```bash
cd ~/comp-site-analyz
docker-compose -f scripts/docker-compose.prod.yml up -d
sleep 15
docker-compose -f scripts/docker-compose.prod.yml ps
docker-compose -f scripts/docker-compose.prod.yml logs --tail=30
```

---

## ✅ Полностью автоматический вариант (скопировать всё разом)

Если вы знаете свой `OPENAI_API_KEY`, замените `YOUR_API_KEY_HERE` на ваш ключ и скопируйте всё разом:

```bash
mkdir -p ~/comp-site-analyz/scripts && cd ~/comp-site-analyz && cat > .env << 'ENVEOF'
OPENAI_API_KEY=YOUR_API_KEY_HERE
OPENAI_API_BASE=https://api.proxyapi.ru/openai/v1
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=False
ENVEOF
sed -i 's/YOUR_API_KEY_HERE/ваш_реальный_ключ_здесь/' .env && cat > scripts/docker-compose.prod.yml << 'EOF'
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
sudo ufw allow 5000/tcp && sudo ufw allow 22/tcp && sudo ufw --force enable && docker-compose -f scripts/docker-compose.prod.yml up -d && sleep 15 && docker-compose -f scripts/docker-compose.prod.yml ps && docker-compose -f scripts/docker-compose.prod.yml logs --tail=30
```

**⚠️ ВАЖНО:** Перед копированием замените `ваш_реальный_ключ_здесь` на ваш реальный API ключ!

## Минимальная версия (готово к запуску)

```bash
mkdir -p ~/comp-site-analyz/scripts && cd ~/comp-site-analyz && cat > .env << 'ENVEOF'
OPENAI_API_KEY=your_proxyapi_key_here
OPENAI_API_BASE=https://api.proxyapi.ru/openai/v1
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=False
ENVEOF
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
echo "⚠️ Отредактируйте .env: nano .env" && nano .env && sudo ufw allow 5000/tcp && sudo ufw allow 22/tcp && sudo ufw --force enable && docker-compose -f scripts/docker-compose.prod.yml up -d && sleep 15 && docker-compose -f scripts/docker-compose.prod.yml ps
```

## Пошагово с проверками (готово к запуску)

```bash
# Шаг 1: Создание структуры
mkdir -p ~/comp-site-analyz/scripts
cd ~/comp-site-analyz

# Шаг 2: Создание .env файла
cat > .env << 'ENVEOF'
OPENAI_API_KEY=your_proxyapi_key_here
OPENAI_API_BASE=https://api.proxyapi.ru/openai/v1
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=False
ENVEOF
echo "⚠️ Отредактируйте .env и укажите свой OPENAI_API_KEY"
nano .env
# Сохраните: Ctrl+O, Enter, Ctrl+X

# Шаг 3: Создание docker-compose.prod.yml
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

# Шаг 4: Настройка файрвола
echo "Настройка файрвола..."
sudo ufw allow 5000/tcp
sudo ufw allow 22/tcp
sudo ufw --force enable
echo "✅ Файрвол настроен"

# Шаг 5: Запуск контейнера
echo "Запуск контейнера..."
docker-compose -f scripts/docker-compose.prod.yml up -d

# Шаг 6: Ожидание и проверка
echo "⏳ Ожидание запуска контейнера (15 секунд)..."
sleep 15

# Проверка статуса
echo "📊 Статус контейнера:"
docker-compose -f scripts/docker-compose.prod.yml ps

# Проверка логов
echo "📋 Последние логи:"
docker-compose -f scripts/docker-compose.prod.yml logs --tail=30

# Проверка доступности
echo "🔍 Проверка доступности:"
curl http://localhost:5000 || echo "⚠️ Приложение еще запускается, подождите немного"

echo ""
echo "✅ Готово! Приложение должно быть доступно по адресу:"
echo "   http://45.133.245.186:5000"
```


## После выполнения

Откройте в браузере:
```
http://45.133.245.186:5000
```

## Полезные команды

```bash
# Просмотр логов в реальном времени
docker-compose -f scripts/docker-compose.prod.yml logs -f

# Остановка
docker-compose -f scripts/docker-compose.prod.yml down

# Перезапуск
docker-compose -f scripts/docker-compose.prod.yml restart

# Статус
docker-compose -f scripts/docker-compose.prod.yml ps
```

