#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Скрипт для отправки кода в GitHub репозиторий
Запрашивает у пользователя сообщение коммита
"""
import subprocess
import sys
import os

# Конфигурация репозитория
GITHUB_USERNAME = "Ardierous"
REPO_NAME = "CompSite_Analyz"
REMOTE_URL = f"https://github.com/{GITHUB_USERNAME}/{REPO_NAME}.git"

def run_command(command, description):
    """Выполняет команду и выводит результат"""
    print(f"\n{'='*60}")
    print(f"{description}...")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Ошибка: {e}")
        if e.stderr:
            print(f"Детали: {e.stderr}")
        return False

def check_git_installed():
    """Проверяет, установлен ли Git"""
    try:
        subprocess.run(["git", "--version"], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("ОШИБКА: Git не установлен!")
        print("Установите Git с https://git-scm.com/")
        return False

def check_git_repo():
    """Проверяет, инициализирован ли Git репозиторий"""
    if not os.path.exists('.git'):
        print("Git репозиторий не инициализирован. Инициализация...")
        if not run_command("git init", "Инициализация Git репозитория"):
            return False
        if not run_command("git branch -M main", "Настройка основной ветки"):
            return False
    return True

def setup_remote():
    """Настраивает remote для GitHub"""
    # Проверяем, есть ли уже remote
    result = subprocess.run(
        "git remote get-url origin",
        shell=True,
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        current_url = result.stdout.strip()
        if current_url != REMOTE_URL:
            print(f"\nТекущий remote: {current_url}")
            print(f"Обновление на: {REMOTE_URL}")
            if not run_command(f'git remote set-url origin {REMOTE_URL}', "Обновление remote URL"):
                return False
        else:
            print(f"\nRemote уже настроен: {REMOTE_URL}")
    else:
        print(f"\nДобавление remote: {REMOTE_URL}")
        if not run_command(f'git remote add origin {REMOTE_URL}', "Добавление remote"):
            return False
    
    return True

def get_commit_message():
    """Запрашивает у пользователя сообщение коммита"""
    print("\n" + "="*60)
    print("Введите сообщение коммита:")
    print("="*60)
    
    message = input("> ").strip()
    
    if not message:
        print("Сообщение коммита не может быть пустым!")
        return get_commit_message()
    
    return message

def main():
    print("="*60)
    print("Отправка кода в GitHub репозиторий")
    print(f"Репозиторий: {GITHUB_USERNAME}/{REPO_NAME}")
    print("="*60)
    
    # Проверка Git
    if not check_git_installed():
        sys.exit(1)
    
    # Проверка/инициализация репозитория
    if not check_git_repo():
        print("Не удалось инициализировать Git репозиторий")
        sys.exit(1)
    
    # Настройка remote
    if not setup_remote():
        print("Не удалось настроить remote")
        sys.exit(1)
    
    # Запрос сообщения коммита
    commit_message = get_commit_message()
    
    # Добавление файлов
    if not run_command("git add .", "Добавление файлов"):
        print("Не удалось добавить файлы")
        sys.exit(1)
    
    # Проверка, есть ли изменения для коммита
    result = subprocess.run(
        "git diff --cached --quiet",
        shell=True,
        capture_output=True
    )
    if result.returncode == 0:
        print("\nНет изменений для коммита. Все файлы уже закоммичены.")
        response = input("Выполнить push существующих коммитов? (y/n): ").strip().lower()
        if response != 'y':
            print("Операция отменена")
            sys.exit(0)
    else:
        # Создание коммита
        if not run_command(f'git commit -m "{commit_message}"', "Создание коммита"):
            print("Не удалось создать коммит")
            sys.exit(1)
    
    # Отправка в GitHub
    print("\n" + "="*60)
    print("Отправка кода в GitHub...")
    print("="*60)
    
    if not run_command("git push -u origin main", "Отправка в GitHub"):
        print("\nВозможные причины ошибки:")
        print("1. Репозиторий не создан на GitHub")
        print("2. Проблемы с аутентификацией")
        print("3. Конфликт с удаленным репозиторием")
        print("\nПопробуйте:")
        print(f"  - Создать репозиторий: https://github.com/new (название: {REPO_NAME})")
        print("  - Использовать Personal Access Token для аутентификации")
        sys.exit(1)
    
    print("\n" + "="*60)
    print("✓ Код успешно отправлен в GitHub!")
    print(f"Репозиторий: https://github.com/{GITHUB_USERNAME}/{REPO_NAME}")
    print("="*60)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nОперация отменена пользователем")
        sys.exit(1)

