import argparse
import asyncio
import json
import os
import sys
import time
import warnings
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
    parser.add_argument("url", help="The starting URL for scraping.")
    parser.add_argument("-f", "--format", nargs='+', choices=['json', 'pdf', 'txt', 'markdown'], default=['json'], help="Output format(s).")
    parser.add_argument("--no-scrape", action="store_true", help="Only create the index without scraping full articles.")
    parser.add_argument("--force-reindex", action="store_true", help="Force re-indexing of all articles.")
    parser.add_argument("--update", action="store_true", help="Only update articles that have changed since last run.")
    parser.add_argument("-p", "--parallel", type=int, default=1, help="Number of parallel download streams.")
    parser.add_argument("--rag", action="store_true", help="Add breadcrumbs to markdown files for RAG systems.")
    parser.add_argument("--limit", type=int, default=None, help="Limit the number of articles to scrape (for testing).")
    args = parser.parse_args()

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

    log_func = setup_logger(config.get_output_dir())

    scraper_instance = Scraper(log_func)

    try:
        # --- Step 1: Check Dependencies ---
        print("Step 1: Checking dependencies...")
        log_func("Step 1: Checking dependencies...")
        if not await config.check_dependencies(log_func):
            raise SystemExit(1) # Exit if checks fail
        print("All checks passed.")
        log_func("All dependency checks passed.")

        # --- Step 2: Initial Setup ---
        print("\nStep 2: Setting up output directories...")
        log_func("Step 2: Setting up output directories...")
        file_manager.setup_output_directories(args.format, update_mode=args.update)
        print("Directories ready.")
        log_func("Directory setup complete.")

        # --- Step 3: Login & Create Index ---
        print("\nStep 3: Logging in and creating article index...")
        log_func("Step 3: Logging in and creating article index...")
        await scraper_instance.connect()
        await scraper_instance.login()
        
        # Load existing metadata before index operations for update mode
        existing_meta_data = file_manager.load_existing_meta_data()
        
        if args.force_reindex or not os.path.exists(os.path.join(file_manager.get_index_path(), "_toc_tree.json")):
            toc_tree = await scraper_instance.get_initial_toc(args.url)
            
            # For parser_v2 (v8std), discover nested articles recursively
            if "v8std" in args.url:
                print("Discovering nested articles recursively...")
                log_func("Discovering nested articles recursively for parser_v2...")
                toc_tree = await scraper_instance.discover_nested_articles(toc_tree, max_depth=3)
                print(f"Recursive discovery complete.")
                log_func("Recursive discovery complete.")
            
            file_manager.save_hierarchical_index(toc_tree)
        else:
            print("Index found, skipping index creation. Use --force-reindex to override.")
            log_func("Index found, skipping index creation.")
            
            # Load the existing TOC tree to check for structural changes
            index_file = os.path.join(file_manager.get_index_path(), "_toc_tree.json")
            with open(index_file, "r", encoding="utf-8") as f:
                toc_tree = json.load(f)
                
            # Check if structure has changed significantly when using --update flag
            if args.update and file_manager.should_force_reindex(toc_tree, existing_meta_data):
                print("TOC structure changed significantly, forcing reindex for all articles.")
                log_func("TOC structure changed significantly, forcing reindex.")
                args.force_reindex = True  # Set flag to force reindexing of all articles
                
        await scraper_instance.close()

        # --- Step 4: Final Scraping ---
        if not args.no_scrape:
            print(f"\nStep 4: Starting final scrape using {args.parallel} parallel stream(s)...")
            log_func(f"Step 4: Starting final scrape using {args.parallel} parallel stream(s)...")
            
            articles_to_scrape = file_manager.load_index_data(limit=args.limit)
            if not articles_to_scrape:
                print_fatal_error("Index is empty. Nothing to scrape.", log_func)
            
            # Log limit information if set
            if args.limit:
                total_articles = len(file_manager.load_index_data())
                print(f"Limit mode: scraping {len(articles_to_scrape)} out of {total_articles} articles.")
                log_func(f"Limit mode: scraping {len(articles_to_scrape)} out of {total_articles} articles.")
                
            # If in update mode, determine which articles need updating
            if args.update and not args.force_reindex:
                articles_to_scrape = file_manager.get_articles_to_scrape(articles_to_scrape, existing_meta_data, update_mode=True)
                if not articles_to_scrape:
                    print("No articles need updating. Exiting.")
                    log_func("No articles need updating.")
                    return
                print(f"Update mode: {len(articles_to_scrape)} articles need updating out of {len(file_manager.load_index_data())} total.")
                log_func(f"Update mode: {len(articles_to_scrape)} articles need updating.")

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
                            log_func(f"Worker {name} error: {e}")
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
                    await scraper.close()

            # --- Step 5: Create TOC and Meta files ---
            print("\nStep 5: Creating Table of Contents and metadata file...")
            log_func("Step 5: Creating TOC and meta file...")
            file_manager.create_toc_and_meta(articles_to_scrape, args.format)
            print("TOC and metadata files created.")
            log_func("TOC and metadata files created.")

        else:
            print("\n--no-scrape flag is set. Exiting without scraping full articles.")
            log_func("Exiting due to --no-scrape flag.")

    except SystemExit as e:
        # This is raised when dependency checks fail, so we don't need to log it as a fatal error
        pass
    except Exception as e:
        print_fatal_error(str(e), log_func)
    finally:
        # --- Step 6: Cleanup ---
        print("\nStep 6: Cleaning up temporary files...")
        log_func("Step 6: Cleaning up...")
        file_manager.cleanup_temp_files()
        print("Cleanup complete.")
        log_func("Cleanup complete.")
        
        end_time = time.monotonic()
        elapsed_time = end_time - start_time
        minutes, seconds = divmod(elapsed_time, 60)
        time_str = f"Total execution time: {int(minutes)} minutes {int(seconds)} seconds."
        print(f"\n{time_str}")
        log_func(time_str)
        
        # Redirect stderr to devnull to suppress potential cleanup errors on exit
        # This can be removed if debugging cleanup issues
        sys.stderr = open(os.devnull, 'w')

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted by user. Exiting...")
        sys.exit(1)
