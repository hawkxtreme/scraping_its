import argparse
import asyncio
import os
import sys
import time
import warnings
import json
from tqdm import tqdm

warnings.filterwarnings("ignore", category=ResourceWarning)

# Import modularized components
from src import config
from src.scraper import Scraper
from src.logger import setup_logger
from src import file_manager
from src.ui import print_header, print_fatal_error, print_step, print_info, print_success, print_error, print_warning, print_progress, print_performance
from src import filter

async def main():
    """Main function to orchestrate the scraping process."""
    # Set stdout encoding to UTF-8
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
        
    start_time = time.monotonic()
    print_header()

    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(description="Scrape articles from its.1c.ru.")
    parser.add_argument("url", nargs='?', help="The starting URL for scraping.")
    parser.add_argument("-c", "--chapter", help="Scrape a specific chapter title.")
    parser.add_argument("-f", "--format", nargs='+', choices=['json', 'pdf', 'txt', 'markdown', 'docx'], default=['json'], help="Output format(s).")
    parser.add_argument("--no-scrape", action="store_true", help="Only create the index without scraping full articles.")
    parser.add_argument("--force-reindex", action="store_true", help="Force re-indexing of all articles.")
    parser.add_argument("--update", action="store_true", help="Only update articles that have changed since last run.")
    parser.add_argument("-p", "--parallel", type=int, default=1, help="Number of parallel download streams.")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging and more verbose output.")
    parser.add_argument("--use-cache", action="store_true", default=True, help="Enable caching to speed up repeated downloads.")
    parser.add_argument("--clear-cache", action="store_true", help="Clear the cache before starting.")
    parser.add_argument("--cache-stats", action="store_true", help="Show cache statistics and exit.")
    
    # Timeout settings
    parser.add_argument("--page-timeout", type=int, default=90000, help="Page load timeout in milliseconds (default: 90000).")
    parser.add_argument("--login-timeout", type=int, default=60000, help="Login timeout in milliseconds (default: 60000).")
    parser.add_argument("--network-idle-timeout", type=int, default=30000, help="Network idle timeout in milliseconds (default: 30000).")
    parser.add_argument("--worker-timeout", type=int, default=300, help="Worker operation timeout in seconds (default: 300).")
    
    # Rate limiting settings
    parser.add_argument("--request-delay", type=float, default=0.5, help="Delay between requests in seconds (default: 0.5).")
    parser.add_argument("--max-retries", type=int, default=3, help="Maximum number of retries for failed requests (default: 3).")
    parser.add_argument("--retry-delay", type=float, default=2.0, help="Delay between retries in seconds (default: 2.0).")
    
    # Filtering options
    parser.add_argument("--filter-by-title", type=str, help="Filter articles by title (contains this string).")
    parser.add_argument("--exclude-by-title", type=str, help="Exclude articles by title (contains this string).")
    parser.add_argument("--max-articles", type=int, help="Maximum number of articles to scrape.")
    parser.add_argument("--skip-first", type=int, default=0, help="Skip first N articles.")
    parser.add_argument("--random-sample", type=int, help="Randomly sample N articles.")
    args = parser.parse_args()

    # --- Dynamic Directory Setup ---
    dir_name = None
    if args.url:
        try:
            from urllib.parse import urlparse
            parsed_url = urlparse(args.url)
            # Extract the last part of the path, ignoring any trailing slashes
            dir_name = os.path.basename(parsed_url.path.rstrip('/'))
        except Exception as e:
            print(f"Could not parse URL to set output directory: {e}")
    
    if dir_name:
        config.set_output_dir(dir_name)
    else:
        # If no URL is provided (e.g. for --cache-stats), try to find the output dir
        # by looking for a _meta.json file in the 'out' directory.
        out_dir = os.path.join(config.PROJECT_ROOT, "out")
        if os.path.exists(out_dir):
            for d in os.listdir(out_dir):
                meta_path = os.path.join(out_dir, d, "_meta.json")
                if os.path.exists(meta_path):
                    config.set_output_dir(d)
                    break

    log_func = setup_logger(config.get_output_dir(), args.debug)

    # Check if URL is provided when needed
    if not args.url and not args.cache_stats:
        print_fatal_error("URL is required for this operation.", log_func=log_func)
        sys.exit(1)

    scraper_instance = Scraper(log_func, use_cache=args.use_cache)

    # Handle cache statistics command
    if args.cache_stats:
        from src.cache import CacheManager
        cache_manager = CacheManager(log_func)
        cache_manager.set_cache_dir(config.get_output_dir())
        stats = cache_manager.get_cache_stats()
        
        if stats:
            print("\n=== Cache Statistics ===")
            print(f"Cache directory: {stats['cache_dir']}")
            print(f"Total size: {stats['total_size_mb']:.2f} MB")
            print(f"File count: {stats['file_count']}")
            print(f"Entry count: {stats['entry_count']}")
            print(f"Max cache age: {stats['max_cache_age_days']} days")
            print(f"Max cache size: {stats['max_cache_size_mb']} MB")
            
            if stats['oldest_entry_time'] > 0:
                import datetime
                oldest_date = datetime.datetime.fromtimestamp(stats['oldest_entry_time'])
                newest_date = datetime.datetime.fromtimestamp(stats['newest_entry_time'])
                print(f"Oldest entry: {oldest_date.strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"Newest entry: {newest_date.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print("No cache statistics available.")
        
        return

    # Clear cache if requested
    if args.clear_cache:
        from src.cache import CacheManager
        cache_manager = CacheManager(log_func)
        cache_manager.clear_cache()
        print("Cache cleared.")
        log_func.logger.info("Cache cleared by user request")
    
    # Apply timeout settings
    config.set_timeout_settings(
        page_timeout_ms=args.page_timeout,
        login_timeout_ms=args.login_timeout,
        network_idle_timeout_ms=args.network_idle_timeout,
        worker_timeout_sec=args.worker_timeout
    )
    
    # Apply rate limiting settings
    config.set_rate_limiting(
        request_delay_sec=args.request_delay,
        max_retries_count=args.max_retries,
        retry_delay_sec=args.retry_delay
    )
    
    # Log settings if in debug mode
    if args.debug:
        log_func.logger.debug("Timeout settings: " + str(config.get_timeout_settings()))
        log_func.logger.debug("Rate limiting settings: " + str(config.get_rate_limiting_settings()))

    try:
        # --- Step 1: Check Dependencies ---
        print_step(1, "Checking dependencies...")
        log_func.logger.log_step("Checking dependencies", {
            "url": args.url,
            "formats": args.format,
            "parallel": args.parallel,
            "update_mode": args.update,
            "debug_mode": args.debug
        })
        
        if not await config.check_dependencies(log_func):
            raise SystemExit(1) # Exit if checks fail
        print_success("All dependency checks passed.")
        log_func.logger.info("All dependency checks passed.")

        # --- Step 2: Initial Setup ---
        print_step(2, "Setting up output directories...")
        log_func.logger.log_step("Setting up output directories", {
            "formats": args.format,
            "update_mode": args.update
        })
        
        file_manager.setup_output_directories(args.format, update_mode=args.update, log_func=log_func)
        print_success("Directories ready.")
        log_func.logger.info("Directory setup complete.")

        # --- Step 3: Login & Create Index ---
        print_step(3, "Logging in and creating article index...")
        log_func.logger.log_step("Logging in and creating article index")
        
        try:
            await scraper_instance.connect()
            print_success("Connected to browser service.")
            log_func.logger.info("Connected to browser service.")
            
            await scraper_instance.login()
            print_success("Login successful.")
            log_func.logger.info("Login successful.")
        except Exception as e:
            print_error("Failed to connect or login", e, args.debug)
            log_func.logger.error("Connection or login failed", e)
            raise
        
        # Load existing metadata before index operations for update mode
        existing_meta_data = file_manager.load_existing_meta_data()
        
        index_start_time = time.monotonic()
        if args.force_reindex or not os.path.exists(os.path.join(file_manager.get_index_path(), "_toc_tree.json")):
            try:
                toc_tree = await scraper_instance.get_initial_toc(args.url, args.chapter)
                file_manager.save_hierarchical_index(toc_tree, log_func)
                
                index_duration = time.monotonic() - index_start_time
                print_performance("Index creation", index_duration)
                log_func.logger.log_performance("Index creation", index_duration)
            except Exception as e:
                print_error("Failed to create index", e, args.debug)
                log_func.logger.error("Index creation failed", e)
                raise
        else:
            print_info("Index found, skipping index creation. Use --force-reindex to override.")
            log_func.logger.info("Index found, skipping index creation.")
            
            # Load the existing TOC tree to check for structural changes
            index_file = os.path.join(file_manager.get_index_path(), "_toc_tree.json")
            try:
                with open(index_file, "r", encoding="utf-8") as f:
                    toc_tree = json.load(f)
            except Exception as e:
                print_error("Failed to load existing index", e, args.debug)
                log_func.logger.error("Failed to load existing index", e)
                raise
                
            # Check if structure has changed significantly when using --update flag
            if args.update and file_manager.should_force_reindex(toc_tree, existing_meta_data, log_func):
                print_warning("TOC structure changed significantly, forcing reindex for all articles.")
                log_func.logger.warning("TOC structure changed significantly, forcing reindex.")
                args.force_reindex = True  # Set flag to force reindexing of all articles
                
        await scraper_instance.close()

        # --- Step 4: Final Scraping ---
        if not args.no_scrape:
            print_step(4, f"Starting final scrape using {args.parallel} parallel stream(s)...")
            log_func.logger.log_step("Starting final scrape", {
                "parallel_streams": args.parallel,
                "update_mode": args.update,
                "force_reindex": args.force_reindex
            })
            
            articles_to_scrape = file_manager.load_index_data()
            if not articles_to_scrape:
                print_fatal_error("Index is empty. Nothing to scrape.", log_func=log_func)
            
            # Apply filters if specified
            if (args.filter_by_title or args.exclude_by_title or
                args.max_articles is not None or args.skip_first > 0 or
                args.random_sample is not None):
                
                print_info("Applying filters to articles...")
                log_func.logger.info("Applying filters to articles", {
                    "filter_by_title": args.filter_by_title,
                    "exclude_by_title": args.exclude_by_title,
                    "max_articles": args.max_articles,
                    "skip_first": args.skip_first,
                    "random_sample": args.random_sample
                })
                
                articles_to_scrape = filter.filter_articles(
                    articles_to_scrape,
                    filter_by_title=args.filter_by_title,
                    exclude_by_title=args.exclude_by_title,
                    max_articles=args.max_articles,
                    skip_first=args.skip_first,
                    random_sample=args.random_sample,
                    log_func=log_func
                )
                
                if not articles_to_scrape:
                    print_warning("No articles match the specified filters. Exiting.")
                    log_func.logger.warning("No articles match the specified filters")
                    return
                
                print_success(f"Filters applied: {len(articles_to_scrape)} articles remaining.")
                log_func.logger.info(f"Filters applied: {len(articles_to_scrape)} articles remaining")
                
            # If in update mode, determine which articles need updating
            if args.update and not args.force_reindex:
                articles_to_scrape = file_manager.get_articles_to_scrape(articles_to_scrape, existing_meta_data, update_mode=True, log_func=log_func)
                if not articles_to_scrape:
                    print_info("No articles need updating. Exiting.")
                    log_func.logger.info("No articles need updating.")
                    return

            shared_hashes = set()

            if args.parallel > 1:
                # --- Improved Worker Pool Setup ---
                log_func.logger.info(f"Starting parallel scraping with {args.parallel} workers")
                
                # Create a semaphore to limit concurrent connections
                connection_semaphore = asyncio.Semaphore(args.parallel)
                
                # Create a queue with a reasonable size limit to prevent memory issues
                max_queue_size = args.parallel * 10  # 10 jobs per worker in queue
                queue = asyncio.Queue(maxsize=max_queue_size)
                
                # Fill the queue with articles
                for i, article_info in enumerate(articles_to_scrape):
                    await queue.put((article_info, i))

                pbar = tqdm(total=len(articles_to_scrape), desc="Scraping Articles", unit="article")
                
                # Track worker statistics
                worker_stats = {
                    'total_processed': 0,
                    'total_errors': 0,
                    'start_time': time.monotonic()
                }

                async def worker(name, queue, pbar, semaphore):
                    """Improved worker function with better error handling and resource management."""
                    worker_start = time.monotonic()
                    processed_count = 0
                    error_count = 0
                    
                    scraper = None
                    try:
                        # Use semaphore to limit concurrent connections
                        async with semaphore:
                            scraper = Scraper(log_func, shared_hashes=shared_hashes, use_cache=args.use_cache)
                            await scraper.connect()
                            await scraper.login()
                            
                            log_func.logger.debug(f"Worker {name} started and connected")
                            
                            while not queue.empty():
                                try:
                                    # Get article from queue with timeout
                                    article_info, index = await asyncio.wait_for(queue.get(), timeout=1.0)
                                    
                                    # Process the article
                                    updated_article_info = await scraper.scrape_single_article(
                                        article_info, args.format, index, pbar, update_mode=args.update
                                    )
                                    # Update the article info in the list with the returned value
                                    if updated_article_info:
                                        # Find the article in the original list and update it
                                        for j, original_article in enumerate(articles_to_scrape):
                                            if original_article.get('url') == article_info.get('url'):
                                                articles_to_scrape[j] = updated_article_info
                                                break
                                    
                                    processed_count += 1
                                    worker_stats['total_processed'] += 1
                                    queue.task_done()
                                    
                                    # Log progress periodically
                                    if processed_count % 10 == 0:
                                        elapsed = time.monotonic() - worker_start
                                        rate = processed_count / elapsed if elapsed > 0 else 0
                                        log_func.logger.debug(f"Worker {name}: processed {processed_count} articles at {rate:.2f} articles/sec")
                                        
                                except asyncio.TimeoutError:
                                    # No more items in queue, exit gracefully
                                    break
                                except asyncio.CancelledError:
                                    log_func.logger.debug(f"Worker {name} received cancellation signal")
                                    break
                                except Exception as e:
                                    error_count += 1
                                    worker_stats['total_errors'] += 1
                                    log_func.logger.error(f"Worker {name} error processing article: {e}")
                                    # Continue processing other articles
                                    queue.task_done()
                                    
                    except Exception as e:
                        log_func.logger.error(f"Worker {name} failed to initialize: {e}")
                        error_count += 1
                        worker_stats['total_errors'] += 1
                    finally:
                        if scraper:
                            try:
                                await scraper.close()
                            except Exception as e:
                                log_func.logger.warning(f"Worker {name} error during cleanup: {e}")
                        
                        worker_duration = time.monotonic() - worker_start
                        log_func.logger.info(f"Worker {name} finished: processed {processed_count} articles, {error_count} errors, duration: {worker_duration:.2f}s")

                # Create and start workers
                workers = [asyncio.create_task(worker(f'worker-{i}', queue, pbar, connection_semaphore))
                          for i in range(args.parallel)]

                # Wait for queue to be processed
                await queue.join()

                # Cancel any remaining workers
                for w in workers:
                    w.cancel()
                
                # Wait for workers to finish with timeout
                try:
                    await asyncio.wait_for(asyncio.gather(*workers, return_exceptions=True), timeout=30.0)
                except asyncio.TimeoutError:
                    log_func.logger.warning("Some workers did not finish gracefully within timeout")

                pbar.close()
                
                # Log overall statistics
                total_duration = time.monotonic() - worker_stats['start_time']
                overall_rate = worker_stats['total_processed'] / total_duration if total_duration > 0 else 0
                log_func.logger.log_performance("Parallel scraping", total_duration, {
                    "workers": args.parallel,
                    "total_processed": worker_stats['total_processed'],
                    "total_errors": worker_stats['total_errors'],
                    "articles_per_second": overall_rate
                })
            else:
                # Run sequentially if parallel is 1
                with tqdm(total=len(articles_to_scrape), desc="Scraping Articles", unit="article") as pbar:
                    scraper = Scraper(log_func, shared_hashes=shared_hashes)
                    await scraper.connect()
                    await scraper.login()
                    for i, article_info in enumerate(articles_to_scrape):
                        updated_article_info = await scraper.scrape_single_article(article_info, args.format, i, pbar, update_mode=args.update)
                        # Update the article info in the list with the returned value
                        if updated_article_info:
                            articles_to_scrape[i] = updated_article_info
                    await scraper.close()

            # --- Step 5: Create TOC and Meta files ---
            print_step(5, "Creating Table of Contents and metadata file...")
            log_func.logger.log_step("Creating TOC and meta file", {
                "article_count": len(articles_to_scrape),
                "formats": args.format
            })
            
            try:
                # Get all articles for complete metadata, not just scraped ones
                all_articles = file_manager.load_index_data()
                file_manager.create_toc_and_meta(articles_to_scrape, all_articles, args.format, log_func)
                print_success("TOC and metadata files created.")
                log_func.logger.info("TOC and metadata files created.")
            except Exception as e:
                print_error("Failed to create TOC and metadata files", e, args.debug)
                log_func.logger.error("Failed to create TOC and metadata files", e)
                raise

        else:
            print_info("--no-scrape flag is set. Exiting without scraping full articles.")
            log_func.logger.info("Exiting due to --no-scrape flag.")

    except SystemExit as e:
        # This is raised when dependency checks fail, so we don't need to log it as a fatal error
        if e.code != 0:  # Only log if it's an error exit
            log_func.logger.warning(f"System exit with code {e.code}")
    except Exception as e:
        print_fatal_error(str(e), e, log_func, args.debug)
    finally:
        # --- Step 6: Cleanup ---
        print_step(6, "Cleaning up temporary files...")
        log_func.logger.log_step("Cleaning up temporary files")
        
        try:
            file_manager.cleanup_temp_files()
            print_success("Cleanup complete.")
            log_func.logger.info("Cleanup complete.")
        except Exception as e:
            print_warning(f"Cleanup completed with warnings: {str(e)}")
            log_func.logger.warning(f"Cleanup completed with warnings: {str(e)}")
        
        end_time = time.monotonic()
        elapsed_time = end_time - start_time
        minutes, seconds = divmod(elapsed_time, 60)
        time_str = f"Total execution time: {int(minutes)} minutes {int(seconds)} seconds."
        print_performance("Total execution", elapsed_time)
        log_func.logger.log_performance("Total execution", elapsed_time)
        
        # Redirect stderr to devnull to suppress potential cleanup errors on exit
        # This can be removed if debugging cleanup issues
        if not args.debug:
            sys.stderr = open(os.devnull, 'w')

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted by user. Exiting...")
        sys.exit(1)
