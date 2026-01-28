# Пошаговая инструкция деплоя на VPS

## Полная последовательность команд для VPS

### Шаг 1: Подключение к серверу

```bash
ssh user@45.133.245.186
```

### Шаг 2: Подготовка директории проекта

```bash
# Создайте директорию проекта (если еще не создана)
mkdir -p ~/comp-site-analyz
cd ~/comp-site-analyz

# Создайте структуру папок
mkdir -p scripts
```

### Шаг 3: Клонирование/обновление кода

**Если проект уже клонирован:**

```bash
cd ~/comp-site-analyz
git pull
```

**Если проект еще не клонирован:**

```bash
cd ~
git clone <ваш-git-репозиторий> comp-site-analyz
cd comp-site-analyz
```

### Шаг 4: Настройка переменных окружения

```bash
cd ~/comp-site-analyz

# Создайте .env файл из примера
cp env.example .env

# Отредактируйте .env файл
nano .env
```

**Минимально необходимые переменные в `.env`:**

```env
# OpenAI API (ProxyAPI)
OPENAI_API_KEY=your_proxyapi_key_here
OPENAI_API_BASE=https://api.proxyapi.ru/openai/v1

# Flask настройки
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=False
```

Сохраните файл: `Ctrl+O`, `Enter`, `Ctrl+X`

### Шаг 5: Настройка файрвола (автоматически)

```bash
cd ~/comp-site-analyz

# Сделайте скрипт исполняемым
chmod +x scripts/setup_firewall.sh

# Запустите скрипт настройки файрвола
sudo bash scripts/setup_firewall.sh
```

Скрипт автоматически:
- Проверит наличие UFW
- Откроет порт 5000 для входящих подключений
- Откроет SSH порт (22) для безопасности
- Активирует файрвол (если не активен)

### Шаг 6: Остановка предыдущего контейнера (если запущен)

```bash
cd ~/comp-site-analyz

# Остановите и удалите предыдущий контейнер (если есть)
docker-compose -f scripts/docker-compose.prod.yml down 2>/dev/null || true

# Или напрямую через Docker
docker stop comp-site-analyz 2>/dev/null || true
docker rm comp-site-analyz 2>/dev/null || true
```

### Шаг 7: Запуск приложения

**Вариант 1: Автоматический запуск (рекомендуется)**

```bash
cd ~/comp-site-analyz

# Сделайте скрипт исполняемым
chmod +x scripts/start_app.sh

# Запустите скрипт автоматического запуска
sudo bash scripts/start_app.sh
```

**Вариант 2: Ручной запуск**

```bash
cd ~/comp-site-analyz

# Запустите контейнер из образа Docker Hub
docker-compose -f scripts/docker-compose.prod.yml up -d
```

### Шаг 8: Проверка работы

```bash
# Проверьте статус контейнера
docker-compose -f scripts/docker-compose.prod.yml ps

# Проверьте логи (первые 50 строк)
docker-compose -f scripts/docker-compose.prod.yml logs --tail=50

# Проверьте доступность локально
curl http://localhost:5000

# Проверьте, что порт открыт в файрволе
sudo ufw status | grep 5000
```

### Шаг 9: Проверка извне

Откройте в браузере:
```
http://45.133.245.186:5000
```

## Полная последовательность команд (одним блоком)

Если хотите выполнить все команды последовательно:

```bash
# 1. Переход в директорию проекта
cd ~/comp-site-analyz || (mkdir -p ~/comp-site-analyz && cd ~/comp-site-analyz)

# 2. Обновление кода
git pull || echo "⚠️  Git репозиторий не настроен, пропускаем обновление"

# 3. Создание .env (если не существует)
if [ ! -f .env ]; then
    cp env.example .env
    echo "⚠️  Создан файл .env из примера. Отредактируйте его: nano .env"
    echo "⚠️  Минимально необходимые переменные:"
    echo "   OPENAI_API_KEY=your_proxyapi_key_here"
    echo "   OPENAI_API_BASE=https://api.proxyapi.ru/openai/v1"
    read -p "Нажмите Enter после редактирования .env файла..."
fi

# 4. Настройка файрвола
chmod +x scripts/setup_firewall.sh
sudo bash scripts/setup_firewall.sh

# 5. Остановка предыдущего контейнера
docker-compose -f scripts/docker-compose.prod.yml down 2>/dev/null || true

# 6. Запуск приложения
docker-compose -f scripts/docker-compose.prod.yml pull
docker-compose -f scripts/docker-compose.prod.yml up -d

# 7. Ожидание запуска
echo "⏳ Ожидание запуска контейнера (10 секунд)..."
sleep 10

# 8. Проверка статуса
echo "📊 Статус контейнера:"
docker-compose -f scripts/docker-compose.prod.yml ps

echo ""
echo "✅ Готово! Приложение должно быть доступно по адресу:"
echo "   http://45.133.245.186:5000"
echo ""
echo "📋 Полезные команды:"
echo "   Логи:    docker-compose -f scripts/docker-compose.prod.yml logs -f"
echo "   Остановка: docker-compose -f scripts/docker-compose.prod.yml down"
echo "   Статус:    docker-compose -f scripts/docker-compose.prod.yml ps"
```

## Обновление приложения (после изменений в коде)

Если были изменены `Dockerfile` или `requirements.txt`:

```bash
cd ~/comp-site-analyz

# Обновите код
git pull

# Обновите образ из Docker Hub (после того, как образ был пересобран и запушен)
docker-compose -f scripts/docker-compose.prod.yml pull

# Перезапустите контейнер
docker-compose -f scripts/docker-compose.prod.yml up -d
```

## Устранение проблем

### Проблема: Контейнер не запускается

```bash
# Проверьте логи
docker-compose -f scripts/docker-compose.prod.yml logs

# Проверьте, что порт 5000 свободен
sudo netstat -tlnp | grep :5000

# Остановите все контейнеры
docker-compose -f scripts/docker-compose.prod.yml down

# Попробуйте запустить снова
docker-compose -f scripts/docker-compose.prod.yml up -d
```

### Проблема: Приложение недоступно извне

```bash
# Проверьте файрвол
sudo ufw status | grep 5000

# Если порт не открыт, откройте его
sudo ufw allow 5000/tcp

# Проверьте статус контейнера
docker-compose -f scripts/docker-compose.prod.yml ps

# Проверьте логи
docker-compose -f scripts/docker-compose.prod.yml logs --tail=50
```

### Проблема: Ошибка "CrewAI не доступен"

```bash
# Проверьте логи контейнера
docker-compose -f scripts/docker-compose.prod.yml logs | grep -i crewai

# Убедитесь, что образ обновлен
docker-compose -f scripts/docker-compose.prod.yml pull

# Пересоздайте контейнер
docker-compose -f scripts/docker-compose.prod.yml up -d --force-recreate
```

## Полезные команды для управления

```bash
# Просмотр логов в реальном времени
docker-compose -f scripts/docker-compose.prod.yml logs -f

# Остановка приложения
docker-compose -f scripts/docker-compose.prod.yml down

# Перезапуск приложения
docker-compose -f scripts/docker-compose.prod.yml restart

# Проверка статуса
docker-compose -f scripts/docker-compose.prod.yml ps

# Вход в контейнер (для отладки)
docker-compose -f scripts/docker-compose.prod.yml exec web bash

# Проверка использования ресурсов
docker stats comp-site-analyz
```

