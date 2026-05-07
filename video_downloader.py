# video_downloader.py

import os
import asyncio
import random
import time
import subprocess
from utils import ensure_dir, get_folder_size_mb, check_and_stop
import config

class VideoDownloader:
    def __init__(self, root_dir, max_videos_per_query=30, max_total_size_mb=None,
                 format_spec="best", delay_between_queries=(5,10), delay_between_downloads=(10,20)):
        self.root_dir = root_dir
        self.max_per_query = max_videos_per_query
        self.max_total_size_mb = max_total_size_mb
        self.format_spec = format_spec
        self.delay_between_queries = delay_between_queries
        self.delay_between_downloads = delay_between_downloads
        self.semaphore = asyncio.Semaphore(3)  # Максимум 3 параллельных загрузки видео
        ensure_dir(root_dir)

    async def _download_single_video(self, video_url, output_path, query):
        """Асинхронное скачивание одного видео через yt-dlp"""
        async with self.semaphore:
            try:
                # Задержка перед скачиванием
                await asyncio.sleep(random.uniform(*self.delay_between_downloads))
                
                # Команда yt-dlp
                cmd = [
                    'yt-dlp',
                    '-f', self.format_spec,
                    '-o', output_path,
                    '--merge-output-format', 'mp4',
                    '--no-playlist',
                    '--ignore-errors',
                    '--no-warnings',
                    '--quiet',
                    video_url
                ]
                
                # Запускаем процесс асинхронно
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                # Ждём завершения с таймаутом
                try:
                    stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=300)  # 5 минут таймаут
                    return process.returncode == 0
                except asyncio.TimeoutError:
                    process.kill()
                    await process.communicate()
                    return False
                    
            except Exception as e:
                print(f"      Ошибка загрузки: {str(e)[:80]}")
                return False

    async def _search_youtube_videos(self, query, max_results=30):
        """Асинхронный поиск видео на YouTube"""
        try:
            # Команда для получения списка видео
            cmd = [
                'yt-dlp',
                f'ytsearch{max_results}:{query}',
                '--flat-playlist',
                '--dump-json',
                '--no-warnings',
                '--quiet'
            ]
            
            # Запускаем процесс
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                return []
            
            # Парсим JSON строки
            import json
            videos = []
            for line in stdout.decode('utf-8', errors='ignore').strip().split('\n'):
                if line.strip():
                    try:
                        video = json.loads(line)
                        if 'url' in video or 'id' in video:
                            video_url = video.get('url') or f"https://youtube.com/watch?v={video.get('id')}"
                            videos.append({
                                'url': video_url,
                                'title': video.get('title', 'Unknown'),
                                'duration': video.get('duration', 0),
                                'id': video.get('id', '')
                            })
                    except:
                        continue
            
            return videos[:max_results]
            
        except Exception as e:
            print(f"      Ошибка поиска: {e}")
            return []

    async def download_videos_async(self, query, target_folder, target_videos=30):
        """Асинхронная загрузка видео для одного запроса"""
        ensure_dir(target_folder)
        
        downloaded = 0
        failed = 0
        skipped = 0
        
        print(f"\n  Поиск видео для '{query}'...")
        
        # Ищем видео
        videos = await self._search_youtube_videos(query, target_videos + 10)
        
        if not videos:
            print(f"  ✗ Не найдено видео для '{query}'")
            return 0
        
        print(f"  Найдено {len(videos)} видео, начинаем асинхронную загрузку...")
        
        # Ограничиваем количество
        videos = videos[:target_videos]
        
        # Создаём задачи для параллельной загрузки
        tasks = []
        video_infos = []
        
        for idx, video in enumerate(videos):
            if downloaded >= target_videos:
                break
            
            # Проверка лимита размера
            if self.max_total_size_mb:
                current_size = get_folder_size_mb(self.root_dir)
                if current_size >= self.max_total_size_mb:
                    print(f"\n[СТОП] Достигнут лимит {self.max_total_size_mb} MB")
                    break
            
            # Формируем безопасное имя файла
            safe_title = ''.join(c for c in video['title'][:50] if c.isalnum() or c in ' ._-')
            if not safe_title:
                safe_title = f"video_{video['id']}"
            
            output_path = os.path.join(target_folder, f"{safe_title}_{video['id']}.%(ext)s")
            
            task = self._download_single_video(video['url'], output_path, query)
            tasks.append(task)
            video_infos.append((idx + 1, video['title'][:50]))
        
        # Запускаем все задачи параллельно (до 3 одновременно благодаря семафору)
        if tasks:
            results = await asyncio.gather(*tasks)
            
            for i, success in enumerate(results):
                if success:
                    downloaded += 1
                    idx, title = video_infos[i]
                    print(f"      [{downloaded}/{target_videos}] ✓ {title}...")
                else:
                    failed += 1
        
        print(f"  ✓ Для '{query}': скачано {downloaded}, ошибок {failed}, пропущено {skipped}")
        return downloaded

    async def run_for_query_async(self, query):
        """Асинхронный метод для загрузки одного запроса"""
        target_folder = os.path.join(self.root_dir, query)
        
        current_total = get_folder_size_mb(self.root_dir)
        if check_and_stop(current_total, self.max_total_size_mb, "Видео"):
            return
        
        wait_time = random.uniform(*self.delay_between_queries)
        print(f"\n⏳ Пауза {wait_time:.1f} сек перед запросом '{query}'...")
        await asyncio.sleep(wait_time)
        
        await self.download_videos_async(query, target_folder, self.max_per_query)

    def run_for_query(self, query):
        """Синхронная обёртка для совместимости"""
        asyncio.run(self.run_for_query_async(query))