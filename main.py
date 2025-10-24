import argparse
import asyncio
import json
import os
import sys
import time
import warnings
from pathlib import Path
from tqdm import tqdm

warnings.filterwarnings("ignore", category=ResourceWarning)

# Import modularized components
from src import config
from src.scraper import Scraper
from src.logger import setup_logger
from src import file_manager
from src.ui import print_header, print_fatal_error

async def main():
    """Main function to orchestrate the scraping process."""
    # Set stdout encoding to UTF-8
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
        
    start_time = time.monotonic()
    print_header()

    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(description="Scrape articles from its.1c.ru.")
    
    # Основные аргументы для скрапинга
    parser.add_argument("url", nargs='?', help="The starting URL for scraping.")
    parser.add_argument("-f", "--format", nargs='+', choices=['json', 'pdf', 'txt', 'markdown'], default=['json'], help="Output format(s).")
    parser.add_argument("--no-scrape", action="store_true", help="Only create the index without scraping full articles.")
    parser.add_argument("--force-reindex", action="store_true", help="Force re-indexing of all articles.")
    parser.add_argument("--update", action="store_true", help="Only update articles that have changed since last run.")
    parser.add_argument("-p", "--parallel", type=int, default=1, help="Number of parallel download streams.")
    parser.add_argument("--rag", action="store_true", help="Add breadcrumbs to markdown files for RAG systems.")
    parser.add_argument("--limit", type=int, default=None, help="Limit the number of articles to scrape (for testing).")
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose (DEBUG) logging.")
    
    # Timeout and retry configuration
    parser.add_argument("--timeout", type=int, default=90, help="Page load timeout in seconds (default: 90)")
    parser.add_argument("--network-timeout", type=int, default=60, help="Network operation timeout in seconds (default: 60)")
    parser.add_argument("--retry-count", type=int, default=3, help="Number of retry attempts for failed requests (default: 3)")
    parser.add_argument("--retry-delay", type=float, default=2.0, help="Initial delay between retries in seconds (default: 2.0)")
    parser.add_argument("--delay", type=float, default=0.5, help="Delay between requests in seconds (default: 0.5)")
    
    # Команды объединения файлов
    parser.add_argument("--merge", action="store_true", help="Merge files instead of scraping")
    parser.add_argument("--merge-dir", help="Directory with files to merge")
    parser.add_argument("--merge-output", help="Output directory for merged files")
    parser.add_argument("--merge-format", choices=['json', 'markdown', 'txt'], default='json', help="Output format for merged files")
    parser.add_argument("--max-files", type=int, default=100, help="Maximum files per merged group")
    parser.add_argument("--max-size", type=float, default=50.0, help="Maximum size per merged group in MB")
    parser.add_argument("--merge-filter", help="Filter pattern for files to merge (e.g., '*.json')")
    parser.add_argument("--sort-by", choices=['name', 'size', 'date'], default='name', help="Sort files by")
    parser.add_argument("--compress", action="store_true", help="Compress merged files")
    parser.add_argument("--merge-stats", action="store_true", help="Show merge statistics without merging")
    
    args = parser.parse_args()

    # --- File Merging Mode ---
    if args.merge:
        from src.file_merger import FileMerger, MergeConfig
        
        if not args.merge_dir:
            print("Ошибка: для режима объединения файлов необходимо указать --merge-dir")
            sys.exit(1)
            
        # Настройка логирования для режима объединения
        log_func = setup_logger("merge", verbose=args.verbose, console_output=True)
        
        # Создание конфигурации объединения
        merge_config = MergeConfig(
            max_files=args.max_files,
            max_size_mb=args.max_size,
            output_format=args.merge_format,
            filter_pattern=args.merge_filter,
            sort_by=args.sort_by,
            compress_output=args.compress,
            include_headers=True
        )
        
        merger = FileMerger(merge_config)
        
        try:
            if args.merge_stats:
                # Показать только статистику
                stats = merger.get_merge_statistics(args.merge_dir)
                print("\n📊 Статистика объединения файлов:")
                print(f"Всего файлов: {stats['total_files']}")
                print(f"Общий размер: {stats['total_size_mb']} MB")
                print(f"Средний размер файла: {stats['avg_file_size_mb']} MB")
                print(f"Ожидаемое количество групп: {stats['estimated_groups']}")
                print(f"Файлы по расширениям: {stats['files_by_extension']}")
                
                if stats['total_files'] == 0:
                    print("⚠️  Файлы для объединения не найдены")
                else:
                    print(f"\n💡 Рекомендации:")
                    if stats['estimated_groups'] > 10:
                        print(f"   - Рассмотрите увеличение --max-files до {args.max_files * 2}")
                        print(f"   - Или увеличение --max-size до {args.max_size * 2}")
                    print(f"   - Команда для объединения:")
                    print(f"     python main.py --merge --merge-dir {args.merge_dir} --max-files {args.max_files} --max-size {args.max_size}")
            else:
                # Выполнить объединение
                print(f"\n🔄 Объединение файлов из {args.merge_dir}...")
                log_func.info(f"Starting file merge from {args.merge_dir}")
                
                merged_files = merger.merge_files(
                    args.merge_dir, 
                    args.merge_output
                )
                
                print(f"\n✅ Объединение завершено!")
                print(f"Создано групп: {len(merged_files)}")
                if merged_files:
                    output_location = Path(merged_files[0]).parent
                    print(f"Файлы сохранены в: {output_location}")
                else:
                    print("Файлы не были созданы")
                
                if args.verbose:
                    print(f"\n📁 Созданные файлы:")
                    for i, file_path in enumerate(merged_files, 1):
                        print(f"   {i}. {file_path}")
                        
                log_func.info(f"Merge completed: {len(merged_files)} groups created")
                
        except Exception as e:
            print_fatal_error(f"Ошибка при объединении файлов: {e}", log_func)
            
        return

    # Проверка обязательного URL для режима скрапинга
    if not args.url:
        parser.error("URL is required for scraping mode")

    # --- Dynamic Directory Setup ---
    try:
        from urllib.parse import urlparse
        parsed_url = urlparse(args.url)
        # Extract the last part of the path, ignoring any trailing slashes
        dir_name = os.path.basename(parsed_url.path.rstrip('/'))
        if dir_name:
            config.set_output_dir(dir_name)
    except Exception as e:
        print(f"Could not parse URL to set output directory: {e}")
        # Fallback to default directory if parsing fails
    
    # --- Configure Timeouts and Retry Settings ---
    try:
        config.set_timeouts(
            page_timeout=args.timeout,
            network_timeout=args.network_timeout,
            retry_count=args.retry_count,
            retry_delay=args.retry_delay,
            request_delay=args.delay
        )
        if args.verbose:
            print(f"Timeouts configured: page={args.timeout}s, network={args.network_timeout}s, retry={args.retry_count}, delay={args.delay}s")
    except ValueError as e:
        print(f"Invalid timeout/retry configuration: {e}")
        raise SystemExit(1)

    # Disable console output to avoid conflicts with tqdm progress bar
    # Console output enabled only in verbose mode or when running tests
    console_output = args.verbose
    log_func = setup_logger(config.get_output_dir(), verbose=args.verbose, console_output=console_output)

    scraper_instance = Scraper(log_func)

    try:
        # --- Step 1: Check Dependencies ---
        print("Step 1: Checking dependencies...")
        log_func.info("Step 1: Checking dependencies...")
        if not await config.check_dependencies(log_func):
            raise SystemExit(1) # Exit if checks fail
        print("All checks passed.")
        log_func.info("All dependency checks passed.")

        # --- Step 2: Initial Setup ---
        print("\nStep 2: Setting up output directories...")
        log_func.info("Step 2: Setting up output directories...")
        file_manager.setup_output_directories(args.format, update_mode=args.update)
        print("Directories ready.")
        log_func.info("Directory setup complete.")

        # --- Step 3: Login & Create Index ---
        print("\nStep 3: Logging in and creating article index...")
        log_func.info("Step 3: Logging in and creating article index...")
        await scraper_instance.connect()
        await scraper_instance.login()
        
        # Load existing metadata before index operations for update mode
        existing_meta_data = file_manager.load_existing_meta_data()
        
        if args.force_reindex or not os.path.exists(os.path.join(file_manager.get_index_path(), "_toc_tree.json")):
            toc_tree = await scraper_instance.get_initial_toc(args.url)
            
            # Always attempt recursive discovery - the system will auto-detect the parser type
            print("Discovering nested articles recursively...")
            log_func.info("Discovering nested articles recursively with auto-detection...")
            toc_tree = await scraper_instance.discover_nested_articles(toc_tree, max_depth=3)
            print(f"Recursive discovery complete.")
            log_func.info("Recursive discovery complete.")
            
            file_manager.save_hierarchical_index(toc_tree)
        else:
            print("Index found, skipping index creation. Use --force-reindex to override.")
            log_func.info("Index found, skipping index creation.")
            
            # Load the existing TOC tree to check for structural changes
            index_file = os.path.join(file_manager.get_index_path(), "_toc_tree.json")
            with open(index_file, "r", encoding="utf-8") as f:
                toc_tree = json.load(f)
                
            # Check if structure has changed significantly when using --update flag
            if args.update and file_manager.should_force_reindex(toc_tree, existing_meta_data):
                print("TOC structure changed significantly, forcing reindex for all articles.")
                log_func.warning("TOC structure changed significantly, forcing reindex.")
                args.force_reindex = True  # Set flag to force reindexing of all articles
                
        await scraper_instance.close()

        # --- Step 4: Final Scraping ---
        if not args.no_scrape:
            print(f"\nStep 4: Starting final scrape using {args.parallel} parallel stream(s)...")
            log_func.info(f"Step 4: Starting final scrape using {args.parallel} parallel stream(s)...")
            
            articles_to_scrape = file_manager.load_index_data(limit=args.limit)
            if not articles_to_scrape:
                print_fatal_error("Index is empty. Nothing to scrape.", log_func)
            
            # Log limit information if set
            if args.limit:
                total_articles = len(file_manager.load_index_data())
                print(f"Limit mode: scraping {len(articles_to_scrape)} out of {total_articles} articles.")
                log_func.info(f"Limit mode: scraping {len(articles_to_scrape)} out of {total_articles} articles.")
                
            # If in update mode, determine which articles need updating
            if args.update and not args.force_reindex:
                articles_to_scrape = file_manager.get_articles_to_scrape(articles_to_scrape, existing_meta_data, update_mode=True)
                if not articles_to_scrape:
                    print("No articles need updating. Exiting.")
                    log_func.info("No articles need updating.")
                    return
                print(f"Update mode: {len(articles_to_scrape)} articles need updating out of {len(file_manager.load_index_data())} total.")
                log_func.info(f"Update mode: {len(articles_to_scrape)} articles need updating.")

            shared_hashes = set()

            if args.parallel > 1:
                # --- Worker Pool Setup ---
                queue = asyncio.Queue()
                for i, article_info in enumerate(articles_to_scrape):
                    await queue.put((article_info, i))

                pbar = tqdm(total=len(articles_to_scrape), desc="Scraping Articles", unit="article")

                async def worker(name, queue, pbar):
                    scraper = Scraper(log_func, shared_hashes=shared_hashes)
                    await scraper.connect()
                    await scraper.login()
                    while not queue.empty():
                        try:
                            article_info, index = await queue.get()
                            await scraper.scrape_single_article(article_info, args.format, index, pbar, update_mode=args.update, rag_mode=args.rag)
                            queue.task_done()
                        except asyncio.CancelledError:
                            break
                        except Exception as e:
                            log_func.error(f"Worker {name} error: {e}", worker=name)
                    await scraper.close()

                workers = [asyncio.create_task(worker(f'worker-{i}', queue, pbar)) for i in range(args.parallel)]

                await queue.join()

                for w in workers:
                    w.cancel()
                
                await asyncio.gather(*workers, return_exceptions=True)

                pbar.close()
            else:
                # Run sequentially if parallel is 1
                with tqdm(total=len(articles_to_scrape), desc="Scraping Articles", unit="article") as pbar:
                    scraper = Scraper(log_func, shared_hashes=shared_hashes)
                    await scraper.connect()
                    await scraper.login()
                    for i, article_info in enumerate(articles_to_scrape):
                        await scraper.scrape_single_article(article_info, args.format, i, pbar, update_mode=args.update, rag_mode=args.rag)
                    await scraper.shutdown()

            # --- Step 5: Create TOC and Meta files ---
            print("\nStep 5: Creating Table of Contents and metadata file...")
            log_func.info("Step 5: Creating TOC and meta file...")
            file_manager.create_toc_and_meta(articles_to_scrape, args.format)
            print("TOC and metadata files created.")
            log_func.info("TOC and metadata files created.")
            
            # --- Step 5.5: Log statistics (only in sequential mode) ---
            if args.parallel == 1 and 'scraper' in locals():
                if hasattr(scraper, 'get_statistics'):
                    stats = scraper.get_statistics()
                    if args.verbose:
                        log_func.log_statistics(stats)
                    # Always log to file
                    log_func.debug(f"Scraping statistics: {stats}")

        else:
            print("\n--no-scrape flag is set. Exiting without scraping full articles.")
            log_func.info("Exiting due to --no-scrape flag.")

    except SystemExit as e:
        # This is raised when dependency checks fail, so we don't need to log it as a fatal error
        pass
    except Exception as e:
        print_fatal_error(str(e), log_func)
    finally:
        # --- Step 6: Cleanup ---
        print("\nStep 6: Cleaning up temporary files...")
        log_func.info("Step 6: Cleaning up...")
        file_manager.cleanup_temp_files()
        print("Cleanup complete.")
        log_func.info("Cleanup complete.")
        
        end_time = time.monotonic()
        elapsed_time = end_time - start_time
        minutes, seconds = divmod(elapsed_time, 60)
        time_str = f"Total execution time: {int(minutes)} minutes {int(seconds)} seconds."
        print(f"\n{time_str}")
        log_func.info(time_str)
        
        # Close logger to release file handles
        log_func.close()
        
        # Redirect stderr to devnull to suppress potential cleanup errors on exit
        # This can be removed if debugging cleanup issues
        sys.stderr = open(os.devnull, 'w')

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted by user. Exiting...")
        sys.exit(1)
