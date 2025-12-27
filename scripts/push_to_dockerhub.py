#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Скрипт для публикации Docker образа на Docker Hub
"""
import os
import subprocess
import sys
import re
from pathlib import Path
from datetime import datetime

# Изменяем рабочую директорию на корень проекта (на уровень выше scripts/)
PROJECT_ROOT = Path(__file__).parent.parent
os.chdir(PROJECT_ROOT)

def run_command(cmd, check=True):
    """Выполняет команду и выводит результат"""
    print(f"\n{'='*60}")
    print(f"Выполняется: {cmd}")
    print(f"{'='*60}\n")
    
    result = subprocess.run(
        cmd,
        shell=True,
        check=check,
        capture_output=False,
        cwd=PROJECT_ROOT
    )
    
    if result.returncode != 0 and check:
        print(f"\n❌ Ошибка при выполнении команды: {cmd}")
        sys.exit(1)
    
    return result.returncode == 0

def normalize_docker_name(name):
    """
    Нормализует имя для Docker (только строчные буквы, дефисы, подчеркивания, точки)
    Docker требует, чтобы имена репозиториев были в нижнем регистре
    """
    if not name:
        return name
    
    # Преобразуем в нижний регистр
    normalized = name.lower()
    
    # Заменяем недопустимые символы на дефисы
    # Оставляем только буквы, цифры, дефисы, подчеркивания и точки
    normalized = re.sub(r'[^a-z0-9._-]', '-', normalized)
    # Убираем множественные дефисы
    normalized = re.sub(r'-+', '-', normalized)
    # Убираем дефисы в начале и конце
    normalized = normalized.strip('-')
    
    return normalized

def get_git_tag():
    """Пытается получить последний git тег"""
    try:
        result = subprocess.run(
            ['git', 'describe', '--tags', '--abbrev=0'],
            capture_output=True,
            text=True,
            check=False,
            cwd=PROJECT_ROOT
        )
        if result.returncode == 0:
            tag = result.stdout.strip()
            # Убираем префикс 'v' если есть
            if tag.startswith('v'):
                tag = tag[1:]
            return tag
    except:
        pass
    return None

def get_version_from_file():
    """Пытается получить версию из файла VERSION или __version__"""
    # Проверяем файл VERSION
    version_file = PROJECT_ROOT / 'VERSION'
    if version_file.exists():
        try:
            version = version_file.read_text(encoding='utf-8').strip()
            if version:
                return version
        except:
            pass
    
    # Проверяем __version__ в main.py
    try:
        main_file = PROJECT_ROOT / 'main.py'
        if main_file.exists():
            content = main_file.read_text(encoding='utf-8')
            match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', content)
            if match:
                return match.group(1)
    except:
        pass
    
    return None

def generate_auto_tag():
    """
    Автоматически генерирует тег для Docker образа
    Приоритет:
    1. Git тег (если есть)
    2. Версия из файла + дата (если есть версия)
    3. Дата/время в формате YYYYMMDD-HHMMSS
    """
    # Пытаемся получить git тег
    git_tag = get_git_tag()
    if git_tag:
        print(f"📌 Найден git тег: {git_tag}")
        return git_tag
    
    # Пытаемся получить версию из файла
    version = get_version_from_file()
    if version:
        # Используем версию + дату
        date_str = datetime.now().strftime('%Y%m%d')
        auto_tag = f"{version}-{date_str}"
        print(f"📌 Используется версия из файла: {version}")
        return auto_tag
    
    # Генерируем тег на основе даты/времени
    auto_tag = datetime.now().strftime('%Y%m%d-%H%M%S')
    print(f"📌 Автоматически сгенерирован тег на основе даты/времени: {auto_tag}")
    return auto_tag

def get_docker_info():
    """Получает информацию о Docker Hub из переменных окружения или использует значения по умолчанию"""
    # Используем имя пользователя по умолчанию или из переменной окружения
    docker_username = os.getenv('DOCKER_USERNAME', 'avardous')
    docker_repo = os.getenv('DOCKER_REPO', 'comp_site_analyz')
    
    # Автоматически генерируем тег, если не задан в переменных окружения
    docker_tag = os.getenv('DOCKER_TAG')
    if not docker_tag:
        print("\n🏷️  Генерация тега...")
        docker_tag = generate_auto_tag()
    else:
        print(f"🏷️  Используется тег из переменной окружения: {docker_tag}")
    
    # Показываем используемое имя пользователя
    if os.getenv('DOCKER_USERNAME'):
        print(f"👤 Используется имя пользователя из переменной окружения: {docker_username}")
    else:
        print(f"👤 Используется имя пользователя по умолчанию: {docker_username}")
    
    # Нормализуем username
    original_username = docker_username
    docker_username = normalize_docker_name(docker_username)
    if docker_username != original_username:
        print(f"⚠️  Имя пользователя нормализовано: {original_username} → {docker_username}")
    
    # Нормализуем имя репозитория
    original_repo = docker_repo
    docker_repo = normalize_docker_name(docker_repo)
    if docker_repo != original_repo:
        print(f"⚠️  Имя репозитория нормализовано: {original_repo} → {docker_repo}")
    
    return docker_username, docker_repo, docker_tag

def main():
    """Основная функция"""
    print("="*60)
    print("🚀 Публикация Docker образа на Docker Hub")
    print("="*60)
    
    # Проверяем, что Docker установлен
    if not run_command("docker --version", check=False):
        print("❌ Docker не установлен или не доступен!")
        print("Установите Docker: https://www.docker.com/get-started")
        sys.exit(1)
    
    # Получаем информацию о Docker Hub
    docker_username, docker_repo, docker_tag = get_docker_info()
    
    image_name = f"{docker_username}/{docker_repo}:{docker_tag}"
    image_name_latest = f"{docker_username}/{docker_repo}:latest"
    
    print(f"\n📦 Имя образа: {image_name}")
    print(f"📦 Имя образа (latest): {image_name_latest}")
    print(f"🏷️  Тег: {docker_tag}\n")
    
    confirm = input("Продолжить? (y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ Отменено пользователем")
        sys.exit(0)
    
    # Шаг 1: Сборка образа
    print("\n🔨 Шаг 1: Сборка Docker образа...")
    build_cmd = f"docker build -t {image_name} -t {image_name_latest} ."
    if not run_command(build_cmd):
        print("❌ Ошибка при сборке образа!")
        sys.exit(1)
    
    print("✅ Образ успешно собран!")
    
    # Шаг 2: Вход в Docker Hub
    print("\n🔐 Шаг 2: Вход в Docker Hub...")
    print("Введите ваш Docker Hub пароль (или токен доступа):")
    login_cmd = f"docker login -u {docker_username}"
    if not run_command(login_cmd):
        print("❌ Ошибка при входе в Docker Hub!")
        sys.exit(1)
    
    print("✅ Успешный вход в Docker Hub!")
    
    # Шаг 3: Публикация образа
    print("\n📤 Шаг 3: Публикация образа на Docker Hub...")
    
    # Публикуем с тегом
    if not run_command(f"docker push {image_name}"):
        print("❌ Ошибка при публикации образа с тегом!")
        sys.exit(1)
    
    # Публикуем latest, если тег не latest
    if docker_tag != 'latest':
        if not run_command(f"docker push {image_name_latest}"):
            print("⚠️  Предупреждение: не удалось опубликовать latest тег")
    
    print("✅ Образ успешно опубликован на Docker Hub!")
    
    # Шаг 4: Информация о публикации
    print("\n" + "="*60)
    print("✅ Публикация завершена успешно!")
    print("="*60)
    print(f"\n📦 Опубликованный образ:")
    print(f"   {image_name}")
    if docker_tag != 'latest':
        print(f"   {image_name_latest}")
    
    print(f"\n🔗 Ссылка на образ:")
    print(f"   https://hub.docker.com/r/{docker_username}/{docker_repo}")
    
    print(f"\n📝 Команда для запуска образа:")
    print(f"   docker run -p 5000:5000 --env-file .env {image_name}")
    
    print(f"\n📝 Команда для запуска с docker-compose:")
    print(f"   (обновите scripts/docker-compose.yml, указав образ: {image_name})")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Прервано пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")
        sys.exit(1)

