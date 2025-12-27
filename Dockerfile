# Используем официальный образ Python 3.11
FROM python:3.11-slim

# Устанавливаем метаданные образа
LABEL maintainer="Company Analyzer"
LABEL description="Flask приложение для анализа компаний с использованием CrewAI"
LABEL version="1.0"

# Устанавливаем переменные окружения
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLASK_APP=main.py \
    FLASK_ENV=production \
    FLASK_HOST=0.0.0.0 \
    FLASK_PORT=5000 \
    FLASK_DEBUG=False

# Создаем non-root пользователя для безопасности
RUN groupadd -r appuser && \
    useradd -r -g appuser -m -d /home/appuser appuser && \
    mkdir -p /home/appuser && \
    chown -R appuser:appuser /home/appuser

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir --force-reinstall "numpy<2.0" && \
    python -c "import numpy; print(f'NumPy version: {numpy.__version__}')"

# Копируем остальные файлы проекта (исключая .env через .dockerignore)
COPY . .

# Убеждаемся, что .env не попал в образ (дополнительная проверка)
RUN if [ -f .env ]; then rm -f .env; fi

# Создаем директорию для логов и даем права пользователю
RUN mkdir -p /app/logs && \
    chown -R appuser:appuser /app

# Переключаемся на non-root пользователя
USER appuser

# Открываем порт 5000
EXPOSE 5000

# Healthcheck для проверки работоспособности
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/', timeout=5)" || exit 1

# Запускаем приложение
CMD ["python", "main.py"]

