#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Модуль для отслеживания расходов через ProxyAPI
"""
import os
import requests
from typing import Optional, Dict
from logger import logger

# URL ProxyAPI
PROXYAPI_BASE_URL = "https://api.proxyapi.ru"

def get_proxyapi_key() -> Optional[str]:
    """Получает ключ ProxyAPI из переменных окружения"""
    return os.getenv("PROXYAPI_KEY") or os.getenv("OPENAI_API_KEY")

def get_balance() -> Optional[float]:
    """
    Получает текущий баланс аккаунта ProxyAPI в рублях
    
    Примечание: Эндпоинт может отличаться в зависимости от версии API ProxyAPI.
    Проверьте документацию: https://proxyapi.ru/docs
    
    Returns:
        float: Баланс в рублях или None в случае ошибки
    """
    api_key = get_proxyapi_key()
    if not api_key:
        logger.warning("ProxyAPI ключ не найден в переменных окружения")
        return None
    
    try:
        # Согласно документации ProxyAPI, правильный эндпоинт для баланса: /proxyapi/balance
        # Также нужно убедиться, что у API ключа есть разрешение на запрос баланса
        # (настройки в личном кабинете ProxyAPI -> Ключи API -> Редактировать -> "Запрос баланса")
        endpoints = [
            f"{PROXYAPI_BASE_URL}/proxyapi/balance",  # Правильный эндпоинт согласно документации
            f"{PROXYAPI_BASE_URL}/balance",  # Резервный вариант
            f"{PROXYAPI_BASE_URL}/api/balance",
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(
                    endpoint,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    timeout=10
                )
                
                logger.debug(f"Запрос баланса к {endpoint}: статус {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    logger.debug(f"Ответ от {endpoint}: {data}")
                    # Пробуем разные возможные ключи для баланса
                    balance = data.get("balance") or data.get("amount") or data.get("value") or data.get("rub") or 0
                    if balance:
                        logger.info(f"Текущий баланс ProxyAPI: {balance} руб. (эндпоинт: {endpoint})")
                        return float(balance)
                elif response.status_code == 404:
                    # Эндпоинт не найден, пробуем следующий
                    logger.debug(f"Эндпоинт {endpoint} не найден (404)")
                    continue
                elif response.status_code == 400:
                    # 400 может означать, что у ключа нет разрешения на запрос баланса
                    error_text = response.text[:200]
                    logger.warning(f"Ошибка 400 при получении баланса от {endpoint}: {error_text}")
                    if "not supported" in error_text.lower() or "endpoint" in error_text.lower():
                        logger.warning("Возможно, у API ключа нет разрешения на запрос баланса. "
                                     "Проверьте настройки ключа в личном кабинете ProxyAPI: "
                                     "Ключи API -> Редактировать -> включите 'Запрос баланса'")
                    continue
                else:
                    logger.warning(f"Ошибка при получении баланса: {response.status_code} - {response.text[:200]}")
            except requests.exceptions.RequestException as e:
                logger.debug(f"Ошибка запроса к {endpoint}: {e}")
                continue
        
        logger.warning("Не удалось получить баланс ни по одному из эндпоинтов. "
                      "Убедитесь, что: 1) У API ключа есть разрешение 'Запрос баланса' в настройках ProxyAPI, "
                      "2) Используется правильный эндпоинт /proxyapi/balance")
        return None
            
    except Exception as e:
        logger.error(f"Ошибка при запросе баланса ProxyAPI: {e}")
        return None

def get_request_cost() -> Optional[Dict]:
    """
    Получает стоимость запросов через ProxyAPI
    
    Returns:
        dict: Словарь с информацией о стоимости или None
    """
    api_key = get_proxyapi_key()
    if not api_key:
        return None
    
    try:
        response = requests.get(
            f"{PROXYAPI_BASE_URL}/cost",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.warning(f"Не удалось получить стоимость запросов: {response.status_code}")
            return None
            
    except Exception as e:
        logger.warning(f"Ошибка при запросе стоимости: {e}")
        return None

def calculate_analysis_cost(task_id: str, initial_balance: Optional[float]) -> Optional[float]:
    """
    Вычисляет стоимость анализа, сравнивая баланс до и после
    
    Args:
        task_id: ID задачи анализа
        initial_balance: Баланс до начала анализа
    
    Returns:
        float: Стоимость анализа в рублях или None
    """
    if initial_balance is None:
        return None
    
    import time
    # Небольшая задержка для обновления баланса в API
    time.sleep(2)
    
    final_balance = get_balance()
    if final_balance is None:
        logger.warning(f"Не удалось получить финальный баланс для задачи {task_id}")
        return None
    
    cost = initial_balance - final_balance
    if cost < 0:
        # Если баланс увеличился (пополнение), считаем стоимость 0
        logger.info(f"Баланс увеличился (возможно пополнение), стоимость = 0")
        cost = 0
    
    logger.info(f"Стоимость анализа {task_id}: {cost:.4f} руб. (баланс: {initial_balance:.4f} -> {final_balance:.4f})")
    return round(cost, 4)

