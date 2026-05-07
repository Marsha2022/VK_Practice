# config.py

# ===== НАСТРОЙКИ ЗАГРУЗКИ =====
IMAGES_ROOT = "images"
VIDEOS_ROOT = "videos"

# Список поисковых запросов
IMAGE_QUERIES = ["fire", "cat", "snake", "castle", "street", "parks", "pond", 
"road repair", "skyscrape", "car", "sidewalk", "road signs", "traffic light",
"traffic jams", "trees", "birds", "pointers", "special equipment", "road closure",
"foundation pit", "puddles", "license plates", "furniture", "payphone", "bus",
"train", "tram", "motorbike", "bike", "parking", "street store", "shopping mall"]
VIDEO_QUERIES = ["dog", "cat", "street"]

# Лимиты на размер (МБ)
MAX_IMAGES_SIZE_MB = 2048   # 2 ГБ
MAX_VIDEOS_SIZE_MB = 3072   # 3 ГБ

# Лимиты на количество файлов на запрос
MAX_IMAGES_PER_QUERY = 200
MAX_VIDEOS_PER_QUERY = 50

# ===== НАСТРОЙКИ ДЛЯ ОБХОДА ОГРАНИЧЕНИЙ =====
REQUEST_DELAY_RANGE = (1, 3)        # секунды между запросами к поисковым системам
DOWNLOAD_DELAY_RANGE = (1, 3)       # между скачиванием файлов
# MAX_RETRIES = 3                     # количество повторных попыток при ошибке
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/119.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Edg/120.0.0.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15",
]

# Настройки видео (качество и ограничения)
VIDEO_FORMAT = "bestvideo[height<=720][filesize<?10M]+bestaudio/best[filesize<?10M]"
# Пауза между скачиванием видео (секунды)
YOUTUBE_DOWNLOAD_DELAY = 10

# ===== НАСТРОЙКИ ГЕНЕРАЦИИ CSV =====
GENERATE_CSV = True                     # Включить генерацию
CSV_OUTPUT_DIR = "csv_datasets"         # Папка для CSV-файлов
CSV_TOTAL_ROWS = 5_000_000              # Целевое количество строк (3-5 млн)
CSV_FILES_SPLIT = 10                    # Разбить на 10 файлов по ~500k строк
CSV_USE_OPENAI_FOR_SEED = True          # Использовать OpenAI для создания seed-данных
CSV_SEED_ROWS = 2000                    # Сколько уникальных строк сгенерирует OpenAI
CSV_OPENAI_MODEL = "gpt-4o-mini"      # Или gpt-4, но дороже
CSV_OPENAI_BATCH_SIZE = 50              # Строк за один запрос (экономия токенов)