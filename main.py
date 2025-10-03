import argparse
import asyncio
import os
import sys
import warnings

warnings.filterwarnings("ignore", category=ResourceWarning)

# Import modularized components
from src import config
from src.scraper import Scraper
from src.logger import setup_logger
from src import file_manager
from src.ui import print_header, print_fatal_error, print_progress

async def main():
    """Main function to orchestrate the scraping process."""
    print_header()
    log_func = setup_logger(config.OUTPUT_DIR)

    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(description="Scrape articles from its.1c.ru.")
    parser.add_argument("url", help="The starting URL for scraping.")
    parser.add_argument("-c", "--chapter", help="Scrape a specific chapter title.")
    parser.add_argument("-f", "--format", nargs='+', choices=['json', 'pdf', 'txt', 'markdown'], default=['json'], help="Output format(s).")
    parser.add_argument("--no-scrape", action="store_true", help="Only create the index without scraping full articles.")
    parser.add_argument("--force-reindex", action="store_true", help="Force re-indexing of all articles.")
    args = parser.parse_args()

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
        file_manager.setup_output_directories()
        print("Directories ready.")
        log_func("Directory setup complete.")

        # --- Step 3: Login & Discover ---
        print("\nStep 3: Logging in and discovering articles...")
        log_func("Step 3: Logging in and discovering articles...")
        await scraper_instance.connect()
        await scraper_instance.login()
        if args.force_reindex or not os.path.exists(file_manager.get_index_path()) or not os.listdir(file_manager.get_index_path()):
            initial_links = await scraper_instance.get_initial_toc(args.url, args.chapter)
            await scraper_instance.discover_articles(initial_links)
        else:
            print("Index found, skipping discovery. Use --force-reindex to override.")
            log_func("Index found, skipping discovery.")
        await scraper_instance.close()

        # --- Step 4: Final Scraping ---
        if not args.no_scrape:
            print("\nStep 4: Starting final scrape...")
            log_func("Step 4: Starting final scrape...")
            articles_to_scrape = file_manager.load_index_data()
            if not articles_to_scrape:
                print_fatal_error("Index is empty. Nothing to scrape.", log_func)
            
            total_articles = len(articles_to_scrape)
            for i, article_info in enumerate(articles_to_scrape):
                scraper = Scraper(log_func)
                try:
                    await scraper.connect()
                    await scraper.login()
                    await scraper.scrape_single_article(article_info, args.format, i, total_articles)
                finally:
                    await scraper.close()

        else:
            print("\n--no-scrape flag is set. Exiting without scraping full articles.")
            log_func("Exiting due to --no-scrape flag.")

    except SystemExit as e:
        # This is raised when dependency checks fail, so we don't need to log it as a fatal error
        pass
    except Exception as e:
        print_fatal_error(str(e), log_func)
    finally:
        # --- Step 5: Cleanup ---
        print("\nStep 5: Cleaning up temporary files...")
        log_func("Step 5: Cleaning up...")
        file_manager.cleanup_temp_files()
        print("Cleanup complete.")
        log_func("Cleanup complete.")
        sys.stderr = open(os.devnull, 'w')

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted by user. Exiting...")
        sys.exit(1)