#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Скрипт для публикации Docker образа на Docker Hub
"""
import os
import subprocess
import sys
import re
import time
import socket
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

def run_command_with_result(cmd):
    """Выполняет команду и возвращает (ok, completed_process)."""
    print(f"\n{'='*60}")
    print(f"Выполняется: {cmd}")
    print(f"{'='*60}\n")
    result = subprocess.run(
        cmd,
        shell=True,
        check=False,
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace',
        cwd=PROJECT_ROOT
    )
    if result.stdout:
        print(result.stdout, end='' if result.stdout.endswith('\n') else '\n')
    if result.stderr:
        print(result.stderr, end='' if result.stderr.endswith('\n') else '\n')
    return result.returncode == 0, result

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

def docker_login_with_prompt(docker_username):
    """Интерактивный логин в Docker Hub."""
    print("\n🔐 Вход в Docker Hub...")
    print("Введите ваш Docker Hub пароль (или токен доступа):")
    return run_command(f"docker login -u {docker_username}")

def _can_resolve_host(hostname):
    """Проверяет, резолвится ли hostname через системный DNS."""
    try:
        socket.getaddrinfo(hostname, 443)
        return True
    except socket.gaierror:
        return False
    except Exception:
        return False

def dockerhub_preflight():
    """Preflight-проверка сетевой доступности Docker Hub до push."""
    print("\n🌐 Preflight: проверка DNS Docker Hub...")
    hosts = ["registry-1.docker.io", "auth.docker.io", "index.docker.io"]
    failed = [h for h in hosts if not _can_resolve_host(h)]
    if failed:
        print("❌ DNS проблема: не удалось разрешить:")
        for h in failed:
            print(f"   - {h}")
        print("💡 Что сделать:")
        print("   1) ipconfig /flushdns")
        print("   2) Перезапустить Docker Desktop")
        print("   3) Настроить DNS в Docker Engine: 1.1.1.1, 8.8.8.8")
        print("   4) Проверить VPN/прокси/антивирусный HTTPS-фильтр")
        return False
    print("✅ DNS Docker Hub доступен")
    return True

def should_retry_push(stderr_text):
    """Определяет, стоит ли повторять push (сетевые/временные ошибки реестра)."""
    s = (stderr_text or "").lower()
    retry_markers = [
        "unexpected status from put request",
        "failed commit on ref",
        "400 bad request",
        "500 internal server error",
        "502 bad gateway",
        "503 service unavailable",
        "504 gateway timeout",
        "tls handshake timeout",
        "i/o timeout",
        "connection reset by peer",
        "eof",
        "context deadline exceeded",
        "toomanyrequests",
        "429",
    ]
    return any(m in s for m in retry_markers)

def push_with_retries(image_name, retries=4, base_delay_sec=4):
    """Публикует docker image с ретраями и backoff."""
    for attempt in range(1, retries + 1):
        print(f"\n📤 Попытка push {attempt}/{retries}: {image_name}")
        ok, result = run_command_with_result(f"docker push {image_name}")
        if ok:
            print(f"✅ Push успешен: {image_name}")
            return True

        stderr_text = (result.stderr or "") + "\n" + (result.stdout or "")
        lowered = stderr_text.lower()
        if "no such host" in lowered or "lookup registry-1.docker.io" in lowered:
            print("❌ DNS ошибка: registry-1.docker.io не резолвится.")
            print("💡 Остановлено без ретраев, т.к. сеть недоступна.")
            print("   Выполните: ipconfig /flushdns, перезапустите Docker Desktop и повторите.")
            return False
        if attempt < retries and should_retry_push(stderr_text):
            delay = base_delay_sec * (2 ** (attempt - 1))
            print(f"⚠️ Временная ошибка реестра/сети. Повтор через {delay} сек...")
            time.sleep(delay)
            continue

        print(f"❌ Push не выполнен: {image_name}")
        if "unexpected status from put request" in stderr_text.lower() or "failed commit on ref" in stderr_text.lower():
            print("💡 Похоже на сбой commit upload-сессии в Docker Hub.")
            print("   Рекомендуется: docker logout && docker login, затем повторить push.")
        return False
    return False

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
    if not docker_login_with_prompt(docker_username):
        print("❌ Ошибка при входе в Docker Hub!")
        sys.exit(1)
    
    print("✅ Успешный вход в Docker Hub!")

    # Шаг 2.5: Preflight сети/DNS перед push
    if not dockerhub_preflight():
        sys.exit(1)
    
    # Шаг 3: Публикация образа
    print("\n📤 Шаг 3: Публикация образа на Docker Hub...")
    
    # Публикуем с тегом
    if not push_with_retries(image_name, retries=4, base_delay_sec=4):
        print("❌ Ошибка при публикации образа с тегом!")
        sys.exit(1)
    
    # Публикуем latest, если тег не latest
    if docker_tag != 'latest':
        if not push_with_retries(image_name_latest, retries=3, base_delay_sec=4):
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

