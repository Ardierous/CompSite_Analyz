# Быстрые команды для VPS

## Полная последовательность команд (скопируйте и выполните)

```bash
# 1. Переход в директорию проекта
cd ~/comp-site-analyz || (mkdir -p ~/comp-site-analyz && cd ~/comp-site-analyz && mkdir -p scripts)

# 2. Обновление кода (если проект уже клонирован)
git pull || echo "⚠️  Git не настроен, пропускаем"

# 3. Создание .env файла (если не существует)
if [ ! -f .env ]; then
    cp env.example .env
    echo "⚠️  ВАЖНО: Отредактируйте .env файл: nano .env"
    echo "   Минимально необходимые переменные:"
    echo "   OPENAI_API_KEY=your_proxyapi_key_here"
    echo "   OPENAI_API_BASE=https://api.proxyapi.ru/openai/v1"
    read -p "Нажмите Enter после редактирования .env..."
fi

# 4. Настройка файрвола
chmod +x scripts/setup_firewall.sh 2>/dev/null || true
sudo bash scripts/setup_firewall.sh

# 5. Остановка предыдущего контейнера
docker-compose -f scripts/docker-compose.prod.yml down 2>/dev/null || true

# 6. Обновление и запуск контейнера
docker-compose -f scripts/docker-compose.prod.yml pull
docker-compose -f scripts/docker-compose.prod.yml up -d

# 7. Ожидание запуска
echo "⏳ Ожидание запуска (10 секунд)..."
sleep 10

# 8. Проверка статуса
echo "📊 Статус:"
docker-compose -f scripts/docker-compose.prod.yml ps

echo ""
echo "✅ Готово! Проверьте: http://45.133.245.186:5000"
echo "📋 Логи: docker-compose -f scripts/docker-compose.prod.yml logs -f"
```

## Минимальная последовательность (если все уже настроено)

```bash
cd ~/comp-site-analyz
git pull
docker-compose -f scripts/docker-compose.prod.yml pull
docker-compose -f scripts/docker-compose.prod.yml down
docker-compose -f scripts/docker-compose.prod.yml up -d
docker-compose -f scripts/docker-compose.prod.yml logs --tail=20
```

## Проверка работы

```bash
# Статус контейнера
docker-compose -f scripts/docker-compose.prod.yml ps

# Логи
docker-compose -f scripts/docker-compose.prod.yml logs -f

# Проверка доступности
curl http://localhost:5000

# Проверка файрвола
sudo ufw status | grep 5000
```

## Остановка

```bash
docker-compose -f scripts/docker-compose.prod.yml down
```

## Перезапуск

```bash
docker-compose -f scripts/docker-compose.prod.yml restart
```

