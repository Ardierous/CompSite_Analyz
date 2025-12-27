#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Скрипт для отправки кода в GitHub репозиторий
Запрашивает у пользователя сообщение коммита
"""
import subprocess
import sys
import os
import shlex
from pathlib import Path

# Установка кодировки UTF-8 для Windows консоли
if sys.platform == 'win32':
    # Устанавливаем кодировку консоли через chcp 65001 (скрываем вывод)
    try:
        subprocess.run('chcp 65001 >nul 2>&1', shell=True, check=False)
    except:
        pass
    # Устанавливаем кодировку через Windows API
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleOutputCP(65001)  # UTF-8
        kernel32.SetConsoleCP(65001)  # UTF-8
    except:
        pass
    # Настраиваем stdout и stderr для UTF-8 с обработкой ошибок
    try:
        import io
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = io.TextIOWrapper(
                sys.stdout.buffer, 
                encoding='utf-8', 
                errors='replace', 
                line_buffering=True
            )
        if hasattr(sys.stderr, 'buffer'):
            sys.stderr = io.TextIOWrapper(
                sys.stderr.buffer, 
                encoding='utf-8', 
                errors='replace', 
                line_buffering=True
            )
    except:
        pass

# Изменяем рабочую директорию на корень проекта (на уровень выше scripts/)
PROJECT_ROOT = Path(__file__).parent.parent
os.chdir(PROJECT_ROOT)

# Конфигурация репозитория
GITHUB_USERNAME = "Ardierous"
REPO_NAME = "CompSite_Analyz"
REMOTE_URL = f"https://github.com/{GITHUB_USERNAME}/{REPO_NAME}.git"
BRANCH_NAME = "main"

# Константы для форматирования
SEPARATOR = "=" * 60

def run_command(command, description, silent=False):
    """Выполняет команду и выводит результат"""
    if not silent:
        print(f"\n{SEPARATOR}")
        print(f"{description}...")
        print(f"{SEPARATOR}")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',  # Заменяем неверные символы вместо ошибки
            cwd=PROJECT_ROOT
        )
        if result.stdout and not silent:
            print(result.stdout.strip())
        return True
    except subprocess.CalledProcessError as e:
        if not silent:
            print(f"Ошибка: {e}")
            if e.stderr:
                print(f"Детали: {e.stderr.strip()}")
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
    if not (PROJECT_ROOT / '.git').exists():
        print("Git репозиторий не инициализирован. Инициализация...")
        if not run_command("git init", "Инициализация Git репозитория"):
            return False
        if not run_command(f"git branch -M {BRANCH_NAME}", "Настройка основной ветки"):
            return False
    return True

def setup_remote():
    """Настраивает remote для GitHub"""
    # Проверяем, есть ли уже remote
    result = subprocess.run(
        "git remote get-url origin",
        shell=True,
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT
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
    print(f"\n{SEPARATOR}")
    print("Введите сообщение коммита:")
    print(f"{SEPARATOR}")
    
    try:
        message = input("> ").strip()
    except (UnicodeDecodeError, UnicodeEncodeError):
        # Если возникла проблема с кодировкой, используем альтернативный способ
        if sys.platform == 'win32':
            import msvcrt
            print("> ", end='', flush=True)
            chars = []
            while True:
                char = msvcrt.getch()
                if char == b'\r':  # Enter
                    break
                elif char == b'\x08':  # Backspace
                    if chars:
                        chars.pop()
                        print('\b \b', end='', flush=True)
                else:
                    try:
                        char_str = char.decode('utf-8')
                        chars.append(char_str)
                        print(char_str, end='', flush=True)
                    except:
                        pass
            print()  # Новая строка после ввода
            message = ''.join(chars).strip()
        else:
            message = input("> ").strip()
    
    if not message:
        print("⚠ Сообщение коммита не может быть пустым!")
        return get_commit_message()
    
    # Возвращаем сообщение как есть, экранирование будет в функции создания коммита
    return message

def check_changes():
    """Проверяет, есть ли изменения для коммита"""
    result = subprocess.run(
        "git status --porcelain",
        shell=True,
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT
    )
    return bool(result.stdout.strip())

def main():
    print(SEPARATOR)
    print("Отправка кода в GitHub репозиторий")
    print(f"Репозиторий: {GITHUB_USERNAME}/{REPO_NAME}")
    print(SEPARATOR)
    
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
    
    # Проверка наличия изменений
    if not check_changes():
        print("\n⚠ Нет изменений для коммита.")
        response = input("Выполнить push существующих коммитов? (y/n): ").strip().lower()
        if response != 'y':
            print("Операция отменена")
            sys.exit(0)
    else:
        # Запрос сообщения коммита
        commit_message = get_commit_message()
        
        # Добавление файлов
        if not run_command("git add .", "Добавление файлов"):
            print("❌ Не удалось добавить файлы")
            sys.exit(1)
        
        # Создание коммита
        # Используем правильное экранирование для Windows с кириллицей
        # Передаем сообщение через stdin для надежности
        try:
            commit_process = subprocess.Popen(
                ['git', 'commit', '-m', commit_message],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                cwd=PROJECT_ROOT
            )
            stdout, stderr = commit_process.communicate()
            
            if commit_process.returncode != 0:
                print(f"❌ Не удалось создать коммит")
                if stderr:
                    print(f"Ошибка: {stderr.strip()}")
                sys.exit(1)
            else:
                print(f"✓ Коммит создан: {commit_message}")
                if stdout:
                    print(stdout.strip())
        except Exception as e:
            print(f"❌ Ошибка при создании коммита: {e}")
            sys.exit(1)
    
    # Отправка в GitHub
    print(f"\n{SEPARATOR}")
    print("Отправка кода в GitHub...")
    print(f"{SEPARATOR}")
    
    if not run_command(f"git push -u origin {BRANCH_NAME}", "Отправка в GitHub"):
        print(f"\n{SEPARATOR}")
        print("❌ Ошибка при отправке кода")
        print(f"{SEPARATOR}")
        print("\nВозможные причины:")
        print("  1. Репозиторий не создан на GitHub")
        print("  2. Проблемы с аутентификацией")
        print("  3. Конфликт с удаленным репозиторием")
        print("\nРешения:")
        print(f"  • Создать репозиторий: https://github.com/new (название: {REPO_NAME})")
        print("  • Использовать Personal Access Token для аутентификации")
        print("  • Проверить права доступа к репозиторию")
        sys.exit(1)
    
    print(f"\n{SEPARATOR}")
    print("✓ Код успешно отправлен в GitHub!")
    print(f"Репозиторий: https://github.com/{GITHUB_USERNAME}/{REPO_NAME}")
    print(f"{SEPARATOR}")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nОперация отменена пользователем")
        sys.exit(1)

