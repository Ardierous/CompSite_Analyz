# Используем официальный образ Python 3.11
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем остальные файлы проекта
COPY . .

# Открываем порт 5000
EXPOSE 5000

# Устанавливаем переменные окружения
ENV FLASK_APP=main.py
ENV FLASK_ENV=production

# Запускаем приложение
CMD ["python", "main.py"]

