#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Модуль логирования для проекта
"""
import logging
import os
from datetime import datetime
from pathlib import Path

# Создаем директорию для логов, если её нет
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

# Имя файла лога с датой
LOG_FILE = LOG_DIR / f"app_{datetime.now().strftime('%Y%m%d')}.log"

# Настройка логирования
def setup_logger(name="CompanyAnalyzer", log_level=logging.INFO):
    """Настраивает и возвращает logger"""
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Удаляем существующие обработчики, чтобы избежать дублирования
    if logger.handlers:
        logger.handlers.clear()
    
    # Формат логов
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Обработчик для файла
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Обработчик для консоли (только важные сообщения)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)  # Только WARNING и выше в консоль
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

# Создаем глобальный logger
logger = setup_logger()

