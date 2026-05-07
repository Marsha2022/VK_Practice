# utils.py

import os
import time
import random
import requests
from functools import wraps

def random_delay(min_sec=1, max_sec=3):
    """Случайная задержка для имитации человека"""
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)

def get_random_user_agent(user_agents_list):
    """Возвращает случайный User-Agent из списка"""
    return random.choice(user_agents_list)

def retry_on_failure(max_retries=3, delay_range=(1, 5)):
    """Декоратор для повторных попыток при ошибках"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    wait = random.uniform(*delay_range) * (2 ** attempt)
                    print(f"Ошибка: {e}. Повтор через {wait:.1f} сек...")
                    time.sleep(wait)
            return None
        return wrapper
    return decorator

def get_folder_size_mb(folder_path):
    total = 0
    if not os.path.exists(folder_path):
        return 0
    for dirpath, _, filenames in os.walk(folder_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.isfile(fp):
                total += os.path.getsize(fp)
    return total / (1024 * 1024)

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def check_and_stop(total_size_mb, limit_mb, category_name):
    if limit_mb is None:
        return False
    if total_size_mb >= limit_mb:
        print(f"[LIMIT] {category_name} достиг лимита {limit_mb} MB. Останов.")
        return True
    return False