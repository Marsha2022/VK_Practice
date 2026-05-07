import asyncio
import config
from image_downloader import ImageDownloader
from video_downloader import VideoDownloader
from utils import ensure_dir

def print_banner():
    print("=" * 60)
    print("   DATA CRAWLER - АСИНХРОННЫЙ сбор данных")
    print("=" * 60)

def print_menu():
    print("\n" + "=" * 60)
    print("ГЛАВНОЕ МЕНЮ")
    print("=" * 60)
    print("  1. Скачать изображения (Bing, асинхронно)")
    print("  2. Скачать видео (YouTube, асинхронно)")
    print("  3. Сгенерировать CSV таблицы")
    print("  4. Запустить ВСЁ (асинхронно)")
    print("  5. Тестовый запуск (10 картинок, 2 видео)")
    print("  0. Выход")
    print("-" * 60)

async def run_image_download_async():
    """Асинхронная загрузка изображений"""
    print("\n" + "=" * 60)
    print("ЗАГРУЗКА ИЗОБРАЖЕНИЙ (Bing)")
    print("=" * 60)
    
    img_dl = ImageDownloader(
        root_dir=config.IMAGES_ROOT,
        max_images_per_query=config.MAX_IMAGES_PER_QUERY,
        max_total_size_mb=config.MAX_IMAGES_SIZE_MB,
        delay_between_queries=config.REQUEST_DELAY_RANGE,
        user_agents=config.USER_AGENTS
    )
    
    tasks = [img_dl.run_for_query_async(query) for query in config.IMAGE_QUERIES]
    await asyncio.gather(*tasks)
    print("\nЗагрузка изображений завершена!")

async def run_video_download_async():
    """Асинхронная загрузка видео"""
    print("\n" + "=" * 60)
    print("ЗАГРУЗКА ВИДЕО (YouTube)")
    print("=" * 60)
    
    vid_dl = VideoDownloader(
        root_dir=config.VIDEOS_ROOT,
        max_videos_per_query=config.MAX_VIDEOS_PER_QUERY,
        max_total_size_mb=config.MAX_VIDEOS_SIZE_MB,
        format_spec=config.VIDEO_FORMAT,
        delay_between_queries=config.REQUEST_DELAY_RANGE,
        delay_between_downloads=(5, 10)
    )
    
    tasks = [vid_dl.run_for_query_async(query) for query in config.VIDEO_QUERIES]
    await asyncio.gather(*tasks)
    print("\nЗагрузка видео завершена!")

def run_image_download():
    asyncio.run(run_image_download_async())

def run_video_download():
    asyncio.run(run_video_download_async())

def run_csv_generation():
    print("\n" + "=" * 60)
    print("ГЕНЕРАЦИЯ CSV ТАБЛИЦ")
    print("=" * 60)
    print("  Запустите: python csv_generator.py")

async def run_test_async():
    """Асинхронный тестовый запуск"""
    print("\n" + "=" * 60)
    print("ТЕСТОВЫЙ ЗАПУСК")
    print("=" * 60)
    
    orig_img_limit = config.MAX_IMAGES_PER_QUERY
    orig_vid_limit = config.MAX_VIDEOS_PER_QUERY
    orig_img_queries = config.IMAGE_QUERIES.copy()
    orig_vid_queries = config.VIDEO_QUERIES.copy()
    
    config.MAX_IMAGES_PER_QUERY = 10
    config.MAX_VIDEOS_PER_QUERY = 2
    config.IMAGE_QUERIES = ["cat"]
    config.VIDEO_QUERIES = ["cat"]
    
    await run_image_download_async()
    await run_video_download_async()
    
    config.MAX_IMAGES_PER_QUERY = orig_img_limit
    config.MAX_VIDEOS_PER_QUERY = orig_vid_limit
    config.IMAGE_QUERIES = orig_img_queries
    config.VIDEO_QUERIES = orig_vid_queries
    
    print("\nТестовый запуск завершён!")

def run_test():
    asyncio.run(run_test_async())

async def run_all_async():
    """Асинхронный запуск всего"""
    print("\n" + "=" * 60)
    print("ЗАПУСК ВСЕХ ПРОЦЕССОВ (АСИНХРОННО)")
    print("=" * 60)
    
    confirm = input("Запустить всё? (y/n): ")
    if confirm.lower() == 'y':
        await run_image_download_async()
        await run_video_download_async()
        print("\nВсе процессы завершены!")

def run_all():
    asyncio.run(run_all_async())

def main():
    print_banner()
    ensure_dir(config.IMAGES_ROOT)
    ensure_dir(config.VIDEOS_ROOT)
    
    while True:
        print_menu()
        choice = input("\nВаш выбор (0-5): ").strip()
        
        if choice == '0':
            print("\nДо свидания!")
            break
        elif choice == '1':
            run_image_download()
        elif choice == '2':
            run_video_download()
        elif choice == '3':
            run_csv_generation()
        elif choice == '4':
            run_all()
        elif choice == '5':
            run_test()
        else:
            print("\nНеверный выбор!")

if __name__ == "__main__":
    main()