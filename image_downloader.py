# image_downloader.py - асинхронная версия с DuckDuckGo

import os
import time
import random
import hashlib
import aiohttp
import aiofiles
import asyncio
from utils import ensure_dir, get_folder_size_mb, check_and_stop
import config
from itertools import cycle

try:
    from ddgs import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    try:
        from duckduckgo_search import DDGS
        DDGS_AVAILABLE = True
    except ImportError:
        DDGS_AVAILABLE = False
        print("⚠️ Установите: pip install ddgs")

class ImageDownloader:
    def __init__(self, root_dir, max_images_per_query=500, max_total_size_mb=None,
                 delay_between_queries=(5,10), delay_between_downloads=(0.5, 1), user_agents=None):
        self.root_dir = root_dir
        self.max_per_query = max_images_per_query
        self.max_total_size_mb = max_total_size_mb
        self.delay_between_queries = delay_between_queries
        self.delay_between_downloads = delay_between_downloads
        self.user_agents = user_agents or config.USER_AGENTS
        
        self.image_hashes = set()
        self.hash_lock = asyncio.Lock()
        self.semaphore = asyncio.Semaphore(10)  # 10 одновременных загрузок
        self.regions = cycle([
            'wt-wt', 'us-en', 'uk-en', 'de-de', 'fr-fr', 'ru-ru', 'jp-jp',
            'ar-es', 'au-en', 'at-de', 'be-fr', 'be-nl', 'br-pt', 'bg-bg',
            'ca-en', 'ca-fr', 'cl-es', 'cn-zh', 'co-es', 'hr-hr', 'cz-cs',
            'dk-da', 'ee-et', 'fi-fi', 'gr-el', 'hk-tzh', 'hu-hu', 'in-en',
            'id-id', 'ie-en', 'it-it', 'kr-kr', 'lv-lv', 'lt-lt', 'my-en',
            'mx-es', 'nl-nl', 'nz-en', 'no-no', 'pe-es', 'ph-en', 'pl-pl',
            'pt-pt', 'ro-ro', 'sg-en', 'sk-sk', 'sl-sl', 'za-en', 'es-es',
            'se-sv', 'ch-de', 'ch-fr', 'ch-it', 'tw-tzh', 'th-th', 'tr-tr',
            'ua-uk', 've-es', 'vn-vi'
        ])
        
        ensure_dir(root_dir)
        self._load_existing_hashes()

    def _load_existing_hashes(self):
        print("  Загрузка существующих изображений...")
        count = 0
        for root, dirs, files in os.walk(self.root_dir):
            for file in files:
                if file.lower().endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif')):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'rb') as f:
                            file_hash = hashlib.md5(f.read()).hexdigest()
                            self.image_hashes.add(file_hash)
                            count += 1
                    except:
                        pass
        print(f"  Найдено {count} существующих изображений")

    def _get_image_hash(self, image_data):
        return hashlib.md5(image_data).hexdigest()

    async def _is_duplicate(self, image_data):
        img_hash = self._get_image_hash(image_data)
        async with self.hash_lock:
            if img_hash in self.image_hashes:
                return True
            self.image_hashes.add(img_hash)
            return False

    async def _download_single(self, session, img_url, filename):
        """Асинхронное скачивание одного изображения"""
        async with self.semaphore:
            try:
                await asyncio.sleep(random.uniform(0.3, 0.8))
                
                headers = {
                    'User-Agent': random.choice(self.user_agents),
                    'Referer': 'https://duckduckgo.com/',
                }
                
                async with session.get(img_url, headers=headers, timeout=aiohttp.ClientTimeout(total=15)) as response:
                    if response.status == 200:
                        image_data = await response.read()
                        
                        if len(image_data) < 5000:  # Слишком маленькие файлы пропускаем
                            return None
                        
                        if await self._is_duplicate(image_data):
                            return None
                        
                        async with aiofiles.open(filename, 'wb') as f:
                            await f.write(image_data)
                        
                        return filename
                    else:
                        return None
                        
            except asyncio.TimeoutError:
                return None
            except Exception as e:
                return None

    def _get_extension(self, url):
        url_lower = url.lower()
        if '.png' in url_lower:
            return 'png'
        elif '.webp' in url_lower:
            return 'webp'
        else:
            return 'jpg'

    async def download_from_duckduckgo_async(self, query, target_folder, target_images=200):
        """Асинхронная загрузка через DuckDuckGo"""
        ensure_dir(target_folder)
        
        if not DDGS_AVAILABLE:
            print("  ❌ Библиотека ddgs не доступна!")
            return 0
        
        downloaded = 0
        duplicates = 0
        tried_regions = set()
        
        print(f"  Асинхронная загрузка {target_images} изображений для '{query}'...")
        
        async with aiohttp.ClientSession() as session:
            while downloaded < target_images and len(tried_regions) < 50:
                current_region = next(self.regions)
                if current_region in tried_regions:
                    continue
                tried_regions.add(current_region)
                
                print(f"    Поиск в регионе: {current_region}...")
                
                try:
                    # Запускаем синхронный поиск в отдельном потоке
                    loop = asyncio.get_event_loop()
                    
                    def sync_search():
                        with DDGS() as ddgs:
                            return list(ddgs.images(
                                query,
                                region=current_region,
                                safesearch='off',
                                size='Large',
                                type_image='photo',
                                max_results=min(100, target_images - downloaded)
                            ))
                    
                    results = await loop.run_in_executor(None, sync_search)
                    
                    if not results:
                        print(f"      Нет результатов в регионе {current_region}")
                        continue
                    
                    print(f"      Найдено {len(results)} URL, загружаем...")
                    
                    # Создаём задачи для параллельной загрузки
                    tasks = []
                    for idx, result in enumerate(results):
                        if downloaded >= target_images:
                            break
                        img_url = result.get('image')
                        if img_url:
                            ext = self._get_extension(img_url)
                            filename = os.path.join(target_folder, f"{query}_{downloaded+idx+1:04d}.{ext}")
                            tasks.append(self._download_single(session, img_url, filename))
                    
                    if tasks:
                        results_download = await asyncio.gather(*tasks)
                        for result in results_download:
                            if result:
                                downloaded += 1
                                print(f"      [{downloaded}/{target_images}] ✓ {os.path.basename(result)}")
                            else:
                                duplicates += 1
                    
                    # Проверка лимита
                    if self.max_total_size_mb:
                        current_size = get_folder_size_mb(self.root_dir)
                        if current_size >= self.max_total_size_mb:
                            print(f"\n[СТОП] Достигнут лимит {self.max_total_size_mb} MB")
                            return downloaded
                    
                    # Пауза между регионами
                    if downloaded < target_images:
                        wait_time = random.uniform(2, 4)
                        print(f"    ⏳ Пауза {wait_time:.1f} сек...")
                        await asyncio.sleep(wait_time)
                    
                except Exception as e:
                    print(f"      Ошибка в регионе {current_region}: {str(e)[:80]}")
                    continue
        
        print(f"  ✓ Для '{query}': скачано {downloaded}, дубликатов {duplicates}")
        return downloaded

    async def run_for_query_async(self, query):
        """Асинхронный метод для загрузки одного запроса"""
        target_folder = os.path.join(self.root_dir, query)
        
        current_total = get_folder_size_mb(self.root_dir)
        if check_and_stop(current_total, self.max_total_size_mb, "Изображения"):
            return
        
        wait_time = random.uniform(*self.delay_between_queries)
        print(f"\n⏳ Пауза {wait_time:.1f} сек перед запросом '{query}'...")
        await asyncio.sleep(wait_time)
        
        await self.download_from_duckduckgo_async(query, target_folder, self.max_per_query)

    def run_for_query(self, query):
        """Синхронная обёртка"""
        asyncio.run(self.run_for_query_async(query))