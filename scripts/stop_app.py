#!/usr/bin/env python3
"""
Скрипт для принудительного завершения приложения Company Analyzer
"""

import os
import sys
import platform
import subprocess
import socket
from pathlib import Path

# Путь к PID файлу (в корне проекта, на уровень выше scripts/)
PID_FILE = Path(__file__).parent.parent / '.app.pid'

# ANSI коды для цветного вывода
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RESET = '\033[0m'

def print_red(text):
    print(f"{Colors.RED}{text}{Colors.RESET}")

def print_green(text):
    print(f"{Colors.GREEN}{text}{Colors.RESET}")

def print_yellow(text):
    print(f"{Colors.YELLOW}{text}{Colors.RESET}")

def is_process_running(pid):
    """Проверяет, запущен ли процесс с указанным PID"""
    try:
        if platform.system() == 'Windows':
            result = subprocess.run(
                ['tasklist', '/FI', f'PID eq {pid}'],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
            return str(pid) in result.stdout
        else:
            result = subprocess.run(['kill', '-0', str(pid)], capture_output=True)
            return result.returncode == 0
    except:
        return False

def kill_process(pid):
    """Завершает процесс с указанным PID"""
    try:
        if platform.system() == 'Windows':
            subprocess.run(
                ['taskkill', '/F', '/PID', str(pid)],
                capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
        else:
            subprocess.run(['kill', '-9', str(pid)], capture_output=True)
        return True
    except Exception as e:
        print_yellow(f"⚠ Не удалось завершить процесс {pid}: {e}")
        return False

def kill_process_on_port(port):
    """Завершает все процессы, использующие указанный порт"""
    killed_count = 0
    try:
        if platform.system() == 'Windows':
            result = subprocess.run(
                ['netstat', '-ano'],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
            )
            pids_to_kill = set()
            for line in result.stdout.split('\n'):
                if f':{port}' in line and 'LISTENING' in line:
                    parts = line.split()
                    if len(parts) > 4:
                        pid = parts[-1]
                        if pid.isdigit():
                            pids_to_kill.add(pid)
            
            for pid in pids_to_kill:
                if kill_process(pid):
                    print_red(f"✓ Завершен процесс с PID {pid}, занимавший порт {port}")
                    killed_count += 1
        else:
            result = subprocess.run(
                ['lsof', '-ti', f':{port}'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')
                for pid in pids:
                    if pid and pid.isdigit():
                        if kill_process(pid):
                            print_red(f"✓ Завершен процесс с PID {pid}, занимавший порт {port}")
                            killed_count += 1
    except Exception as e:
        print_yellow(f"⚠ Ошибка при попытке завершить процесс на порту {port}: {e}")
    
    return killed_count > 0

def check_port_in_use(host, port):
    """Проверяет, занят ли порт"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)
    result = sock.connect_ex((host, port))
    sock.close()
    return result == 0

def main():
    """Основная функция для принудительного завершения приложения"""
    print("=" * 60)
    print("Принудительное завершение приложения Company Analyzer")
    print("=" * 60)
    
    killed_any = False
    
    # ШАГ 1: Проверяем PID файл и завершаем процесс
    if PID_FILE.exists():
        try:
            with open(PID_FILE, 'r') as f:
                pid_str = f.read().strip()
                if pid_str:
                    pid = int(pid_str)
                    if is_process_running(pid):
                        print_yellow(f"⚠ Обнаружен запущенный экземпляр приложения (PID: {pid})")
                        if kill_process(pid):
                            print_red(f"✓ Приложение (PID: {pid}) успешно завершено")
                            killed_any = True
                        else:
                            print_red(f"❌ Не удалось завершить приложение (PID: {pid})")
                    else:
                        print(f"ℹ PID файл найден, но процесс {pid} не запущен")
                else:
                    print("ℹ PID файл пуст")
            
            # Удаляем PID файл
            try:
                PID_FILE.unlink()
                print_green("✓ PID файл удален")
            except:
                pass
        except ValueError:
            print_yellow("⚠ PID файл содержит неверные данные")
            try:
                PID_FILE.unlink()
            except:
                pass
        except Exception as e:
            print_yellow(f"⚠ Ошибка при чтении PID файла: {e}")
    else:
        print("ℹ PID файл не найден")
    
    # ШАГ 2: Проверяем порт из переменной окружения или по умолчанию 5000
    import os
    from dotenv import load_dotenv
    try:
        # Загружаем .env из корня проекта
        env_path = Path(__file__).parent.parent / '.env'
        if env_path.exists():
            load_dotenv(env_path)
        else:
            load_dotenv()
    except:
        pass
    
    port = int(os.getenv('FLASK_PORT', 5000))
    
    if check_port_in_use('127.0.0.1', port):
        print_yellow(f"⚠ Порт {port} занят. Завершаю процессы на порту...")
        if kill_process_on_port(port):
            killed_any = True
            import time
            time.sleep(1)  # Ждем освобождения порта
    else:
        print_green(f"✓ Порт {port} свободен")
    
    # Итог
    print("=" * 60)
    if killed_any:
        print_green("✓ Приложение успешно завершено")
    else:
        print("ℹ Приложение не было запущено")
    print("=" * 60)

if __name__ == '__main__':
    main()

