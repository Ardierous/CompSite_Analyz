#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Скрипт для публикации Docker образа на Docker Hub
"""
import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd, check=True):
    """Выполняет команду и выводит результат"""
    print(f"\n{'='*60}")
    print(f"Выполняется: {cmd}")
    print(f"{'='*60}\n")
    
    result = subprocess.run(
        cmd,
        shell=True,
        check=check,
        capture_output=False
    )
    
    if result.returncode != 0 and check:
        print(f"\n❌ Ошибка при выполнении команды: {cmd}")
        sys.exit(1)
    
    return result.returncode == 0

def get_docker_info():
    """Получает информацию о Docker Hub из переменных окружения или запрашивает у пользователя"""
    docker_username = os.getenv('DOCKER_USERNAME')
    docker_repo = os.getenv('DOCKER_REPO', 'company-analyzer')
    docker_tag = os.getenv('DOCKER_TAG', 'latest')
    
    if not docker_username:
        docker_username = input("Введите ваш Docker Hub username: ").strip()
        if not docker_username:
            print("❌ Docker Hub username обязателен!")
            sys.exit(1)
    
    # Запрашиваем дополнительные параметры, если не заданы
    if not os.getenv('DOCKER_REPO'):
        custom_repo = input(f"Введите имя репозитория (по умолчанию: {docker_repo}): ").strip()
        if custom_repo:
            docker_repo = custom_repo
    
    if not os.getenv('DOCKER_TAG'):
        custom_tag = input(f"Введите тег (по умолчанию: {docker_tag}): ").strip()
        if custom_tag:
            docker_tag = custom_tag
    
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
    print(f"📦 Имя образа (latest): {image_name_latest}\n")
    
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
    print(f"   (обновите docker-compose.yml, указав образ: {image_name})")
    
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

