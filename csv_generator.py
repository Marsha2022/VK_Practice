# csv_generator.py

import os
import random
import pandas as pd
import time
from openai import OpenAI
from utils import ensure_dir

# ========== НАСТРОЙКИ ДЛЯ PROXYAPI ==========
# 1. Укажите ваш API-ключ от ProxyAPI
PROXYAPI_KEY = "sk-lyUvwfMTdfwBA5rbiQ8Fv3Fm6HzWceuI" 

# 2. Укажите base_url для совместимого с OpenAI API
#    Документация: https://api.proxyapi.ru/openai/v1 [reference:4]
PROXYAPI_BASE_URL = "https://api.proxyapi.ru/openai/v1"

# Инициализация клиента OpenAI с параметрами ProxyAPI
client = OpenAI(
    api_key=PROXYAPI_KEY,
    base_url=PROXYAPI_BASE_URL,
)

def generate_seed_books_via_openai(num_rows, batch_size=50):
    """
    Генерирует уникальные строки книг через OpenAI API (новая версия 1.0+)
    """
    all_rows = []
    
    for batch_start in range(0, num_rows, batch_size):
        batch_num = min(batch_size, num_rows - batch_start)
        
        prompt = f"""
        Сгенерируй {batch_num} уникальных строк в формате CSV без заголовков.
        Каждая строка должна содержать: "Книга", "Жанр", "Автор", "Тираж", "Популярность" (число от 1 до 10).
        Данные должны выглядеть реалистично: жанры (фантастика, детектив, роман, и т.д.), авторы известные и вымышленные,
        тиражи от 1000 до 2_000_000, популярность от 1 до 10.
        Разделитель — вертикальная черта '|'. Не добавляй лишнего текста, только строки.
        Пример строки:
        Три товарища|Роман|Эрих Мария Ремарк|450000|9
        """
        
        try:
            # Новый синтаксис для версии 1.0+
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "Ты генератор структурированных данных. Отвечай только строками CSV."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=batch_num * 60
            )
            
            content = response.choices[0].message.content.strip()
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            
            for line in lines:
                parts = line.split('|')
                if len(parts) == 5:
                    try:
                        all_rows.append({
                            "Книга": parts[0].strip(),
                            "Жанр": parts[1].strip(),
                            "Автор": parts[2].strip(),
                            "Тираж": int(parts[3].strip()),
                            "Популярность": int(parts[4].strip())
                        })
                    except ValueError:
                        continue
                        
            print(f"  Сгенерировано {len(all_rows)} / {num_rows} записей")
            
        except Exception as e:
            print(f"  Ошибка OpenAI: {e}")
        
        # Задержка между запросами, чтобы не превысить лимиты
        time.sleep(random.uniform(1, 3))
    
    return pd.DataFrame(all_rows)

def expand_to_millions(seed_df, target_rows):
    """
    Расширяет seed-датафрейм до target_rows строк за счёт случайных повторений
    и модификации числовых полей.
    """
    if len(seed_df) == 0:
        print("  Ошибка: нет seed-данных для расширения!")
        return pd.DataFrame()
    
    multiplier = target_rows // len(seed_df) + 1
    big_df = pd.concat([seed_df] * multiplier, ignore_index=True)
    big_df = big_df.head(target_rows)

    # Добавляем случайные вариации
    def vary_tirage(t):
        factor = random.uniform(0.8, 1.2)
        return int(t * factor)
    
    def vary_popularity(p):
        new_p = p + random.randint(-1, 1)
        return max(1, min(10, new_p))

    big_df['Тираж'] = big_df['Тираж'].apply(vary_tirage)
    big_df['Популярность'] = big_df['Популярность'].apply(vary_popularity)
    
    return big_df

def save_csv_chunks(df, output_dir, rows_per_file=500_000):
    """Сохраняет DataFrame в несколько CSV-файлов по rows_per_file строк."""
    ensure_dir(output_dir)
    
    if len(df) == 0:
        print("  Ошибка: нет данных для сохранения!")
        return
    
    num_files = (len(df) + rows_per_file - 1) // rows_per_file
    for i in range(num_files):
        start = i * rows_per_file
        end = min((i+1) * rows_per_file, len(df))
        chunk = df.iloc[start:end]
        filename = os.path.join(output_dir, f"books_part_{i+1:03d}.csv")
        chunk.to_csv(filename, index=False, encoding='utf-8')
        print(f"  Сохранён {filename} ({len(chunk)} строк)")

def generate_full_csv(total_rows, seed_rows, output_dir, use_openai=True, split_every=500_000):
    """Основная функция – создаёт CSV на 3-5 млн строк."""
    
    ensure_dir(output_dir)
    
    if use_openai and seed_rows > 0:
        print(f"Генерация {seed_rows} seed-строк через OpenAI API...")
        print("  (убедитесь, что переменная окружения OPENAI_API_KEY установлена)")
        
        seed_df = generate_seed_books_via_openai(seed_rows, batch_size=20)  # Уменьшил batch_size для стабильности
        
        if len(seed_df) > 0:
            seed_file = os.path.join(output_dir, "seed_books.csv")
            seed_df.to_csv(seed_file, index=False)
            print(f"  Seed-данные сохранены в {seed_file}")
        else:
            print("  Не удалось сгенерировать seed-данные через OpenAI")
            print("  Использую встроенные шаблоны...")
            use_openai = False
    
    if not use_openai:
        # Встроенные шаблоны
        print("Используем встроенные шаблоны (без OpenAI)")
        genres = ["Фантастика", "Детектив", "Роман", "Триллер", "История", "Поэзия", "Научная фантастика", "Приключения"]
        authors = ["Толстой", "Достоевский", "Кинг", "Роулинг", "Маркес", "Пелевин", "Лукьяненко", "Акунин"]
        books = ["Война и мир", "Преступление и наказание", "Сияние", "Гарри Поттер", 
                 "Сто лет одиночества", "Generation П", "Ночной дозор", "Азазель"]
        
        data = []
        for i in range(min(seed_rows, 1000)):  # Не более 1000 встроенных
            data.append({
                "Книга": random.choice(books) + f" {i}",
                "Жанр": random.choice(genres),
                "Автор": random.choice(authors),
                "Тираж": random.randint(1000, 2_000_000),
                "Популярность": random.randint(1, 10)
            })
        seed_df = pd.DataFrame(data)
    
    print(f"Расширение до {total_rows:,} строк с вариациями...")
    full_df = expand_to_millions(seed_df, total_rows)
    
    if len(full_df) == 0:
        print("  Ошибка: не удалось создать данные!")
        return
    
    print(f"Сохранение результатов в {output_dir}...")
    save_csv_chunks(full_df, output_dir, rows_per_file=split_every)
    print(f"Готово! Создано {total_rows:,} строк в {output_dir}")