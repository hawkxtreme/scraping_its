import asyncio
import os
import json
import shutil
import argparse
import sys
from datetime import datetime

try:
    from playwright.async_api import async_playwright, Error as PlaywrightError, Page
    from dotenv import load_dotenv
    from bs4 import BeautifulSoup
except ImportError as e:
    print(f"[ERROR] A required library is not installed: {e.name}")
    print("Please install the required libraries by running the following command:")
    print("pip install -r requirements.txt")
    sys.exit(1)

load_dotenv()

async def check_dependencies(log_func):
    print("Step 0: Checking dependencies...")
    log_func("Step 0: Checking dependencies...")
    username = os.environ.get("LOGIN_1C_USER")
    password = os.environ.get("LOGIN_1C_PASSWORD")
    if not username or not password or username == "your_username":
        print("  - [FAIL] Credentials not found.")
        log_func("Result: Failed - Credentials not set.")
        return False
    print("  - [OK] Credentials found.")
    log_func("  - Credentials check passed.")
    browserless_url = os.environ.get('BROWSERLESS_URL', 'http://localhost:3000')
    try:
        async with async_playwright() as p:
            browser = await p.chromium.connect_over_cdp(browserless_url, timeout=5000)
            await browser.close()
        print(f"  - [OK] Browserless service is running at {browserless_url}.")
        log_func(f"  - Browserless service check passed at {browserless_url}.")
    except Exception as e:
        print(f"  - [FAIL] Browserless service not found at {browserless_url}.")
        log_func(f"Result: Failed - Browserless service not available: {e}")
        return False
    print("All checks passed.")
    log_func("All dependency checks passed.")
    return True

async def discover_articles(page: Page, log_func, initial_links: list) -> list:
    log_func("Starting article discovery...")
    all_articles = []
    queue = initial_links[:]
    processed_urls = set(link['url'] for link in queue)
    while queue:
        article_info = queue.pop(0)
        log_func(f"  - Checking: {article_info['title']} ({article_info['url']})")
        try:
            await page.goto(article_info['url'], timeout=60000)
            await page.wait_for_load_state('networkidle')
            article_frame = page.frame(name="w_metadata_doc_frame")
            if not article_frame:
                log_func(f"  - WARNING: Could not find article frame for {article_info['url']}")
                continue
            iframe_html = await article_frame.content()
            soup = BeautifulSoup(iframe_html, 'html.parser')
            nested_index = soup.find('div', class_='index')
            if nested_index and nested_index.find('a'):
                log_func(f"    - Found nested TOC in '{article_info['title']}'.")
                for link in nested_index.find_all('a'):
                    href = link.get('href')
                    text = link.get_text(strip=True)
                    if href and text:
                        full_url = f"https://its.1c.ru{href}"
                        if full_url not in processed_urls:
                            new_article = {"title": text, "url": full_url}
                            queue.append(new_article)
                            processed_urls.add(full_url)
                            log_func(f"      - Queued nested link: {text}")
            else:
                log_func(f"    - Confirmed as content page: {article_info['title']}")
                all_articles.append(article_info)
        except Exception as e:
            log_func(f"  - ERROR during discovery at {article_info['url']}: {e}")
    log_func(f"Discovery complete. Found {len(all_articles)} total articles to scrape.")
    return all_articles

async def main(toc_url, formats, target_chapter):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "out")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file_path = os.path.join(output_dir, "script_log.txt")
    def print_progress(current, total, title, url):
        if total == 0:
            progress = 1.0
        else:
            progress = current / total
        bar_length = 30
        filled_len = int(bar_length * progress)
        bar = '█' * filled_len + '─' * (bar_length - filled_len)
        percent = progress * 100
        info_str = f"({current}/{total}) Scraping: {title}"
        try:
            terminal_width = shutil.get_terminal_size().columns
        except Exception:
            terminal_width = 80
        max_info_len = terminal_width - (bar_length + 10)
        if len(info_str) > max_info_len > 0:
            info_str = info_str[:max_info_len - 3] + "..."
        progress_str = f"Progress: [{bar}] {percent:.1f}% | {info_str}"
        output_str = f"\r{progress_str.ljust(terminal_width)}"
        try:
            sys.stdout.write(output_str)
        except UnicodeEncodeError:
            sys.stdout.buffer.write(output_str.encode('utf-8', 'replace'))
        sys.stdout.flush()

    def log(message):
        with open(log_file_path, "a", encoding="utf-8") as f:
            f.write(f"{message}\n")

    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "out")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file_path = os.path.join(output_dir, "script_log.txt")
    base_articles_dir = os.path.join(output_dir, "articles")
    json_dir = os.path.join(base_articles_dir, "json")
    pdf_dir = os.path.join(base_articles_dir, "pdf")
    txt_dir = os.path.join(base_articles_dir, "txt")
    os.makedirs(output_dir, exist_ok=True)
    if os.path.exists(base_articles_dir):
        shutil.rmtree(base_articles_dir)
    os.makedirs(json_dir, exist_ok=True)
    os.makedirs(pdf_dir, exist_ok=True)
    os.makedirs(txt_dir, exist_ok=True)

    log(f"---_\nScript: its_v3.py\nTimestamp: {timestamp}")
    log(f"URL: {toc_url}\nFormats: {formats}\nChapter: {target_chapter}")
    if not await check_dependencies(log):
        return
    username = os.environ.get("LOGIN_1C_USER")
    password = os.environ.get("LOGIN_1C_PASSWORD")
    browserless_url = os.environ.get('BROWSERLESS_URL', 'http://localhost:3000')
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(browserless_url)
        context = await browser.new_context()
        page = await context.new_page()
        page.set_default_timeout(90000)
        # --- 1. Login ---
        print("Step 1: Logging in...")
        log("Step 1: Logging in...")
        await page.goto("https://login.1c.ru/login")
        await page.fill("input#username", username)
        await page.fill("input#password", password)
        await page.press('input#password', 'Enter')
        await page.wait_for_load_state('networkidle')
        print("Login successful.")
        log("Login successful.")
        # --- 2. Get Initial Table of Contents ---
        print(f"Step 2: Scraping initial table of contents from {toc_url}...")
        log(f"Step 2: Scraping initial table of contents from {toc_url}...")
        await page.goto(toc_url)
        await page.wait_for_load_state('networkidle')
        iframe = page.frame(name="w_metadata_doc_frame")
        if not iframe:
            print("Result: Failed - Could not find the main iframe.")
            log("Result: Failed - Could not find the main iframe.")
            await browser.close()
            return
        iframe_content = await iframe.content()
        soup = BeautifulSoup(iframe_content, 'html.parser')
        index_div = soup.find('div', class_='index')
        initial_toc_links = []
        if index_div:
            for link in index_div.find_all('a'):
                href = link.get('href')
                text = link.get_text(strip=True)
                if href and text:
                    initial_toc_links.append({"title": text, "url": f"https://its.1c.ru{href}"})
            log(f"Found {len(initial_toc_links)} initial links.")
        else:
            print("Result: Failed - Could not find the table of contents div.")
            log("Result: Failed - Could not find the table of contents div.")
            await browser.close()
            return
        if target_chapter:
            initial_toc_links = [link for link in initial_toc_links if link['title'] == target_chapter]
            print(f"Testing on a single chapter: {target_chapter}")
            log(f"Testing on a single chapter: {target_chapter}")
        # --- 3. Discover All Articles ---
        print("Step 3: Discovering all articles (including nested)...")
        articles_to_scrape = await discover_articles(page, log, initial_toc_links)
        total_articles = len(articles_to_scrape)
        print(f"Found {total_articles} total articles to scrape.")
        # --- 4. Scrape Articles ---
        print("Step 4: Scraping articles...")
        log("Step 4: Scraping articles...")
        i = 0
        while i < total_articles:
            title = articles_to_scrape[i]['title']
            url = articles_to_scrape[i]['url']
            print_progress(i, total_articles, title, "")
            log(f"- Scraping ({i+1}/{total_articles}): {title} ({url})")
            filename_base = "".join([c for c in title.lower() if c.isalnum() or c==' ']).rstrip().replace(" ", "_")
            try:
                await page.goto(url, timeout=90000)
                await page.wait_for_load_state('networkidle')
                article_frame = page.frame(name="w_metadata_doc_frame")
                if not article_frame:
                    log(f"  - ERROR: Could not find article frame for {title}.")
                    i += 1
                    continue
                iframe_html = await article_frame.content()
                soup = BeautifulSoup(iframe_html, 'html.parser')
                content_div = soup.find('body')
                if not content_div:
                    log(f"  - WARNING: No <body> tag found for '{title}'. Skipping content extraction.")
                    i += 1
                    continue
                article_text = content_div.get_text(separator='\n', strip=True)
                if not article_text.strip() or len(article_text.strip().splitlines()) < 2:
                    log(f"  - WARNING: Scraped text for '{title}' is very short or empty.")
                if 'json' in formats:
                    json_path = os.path.join(json_dir, f"{filename_base}.json")
                    with open(json_path, "w", encoding="utf-8") as json_file:
                        json.dump({"url": url, "title": title, "content": article_text}, json_file, ensure_ascii=False, indent=4)
                    log(f"  - Saved JSON to {filename_base}.json")
                if 'txt' in formats:
                    txt_path = os.path.join(txt_dir, f"{filename_base}.txt")
                    with open(txt_path, "w", encoding="utf-8") as txt_file:
                        txt_file.write(article_text)
                    log(f"  - Saved TXT to {filename_base}.txt")
                if 'pdf' in formats:
                    pdf_path = os.path.join(pdf_dir, f"{filename_base}.pdf")
                    print_link_element = await page.query_selector('#w_metadata_print_href')
                    if print_link_element:
                        print_url = await print_link_element.get_attribute('href')
                        if print_url:
                            if not print_url.startswith('http'):
                                print_url = f"https://its.1c.ru{print_url}"
                            print_page = await context.new_page()
                            try:
                                await print_page.goto(print_url, timeout=90000)
                                await print_page.wait_for_load_state('networkidle', timeout=60000)
                                pdf_bytes = await print_page.pdf(format='A4', print_background=True)
                                with open(pdf_path, "wb") as pdf_file:
                                    pdf_file.write(pdf_bytes)
                                log(f"  - Saved PDF (print version) to {filename_base}.pdf")
                            except Exception as pdf_ex:
                                log(f"  - ERROR saving PDF for {title}: {pdf_ex}")
                            finally:
                                try:
                                    await print_page.close()
                                except Exception:
                                    pass
                        else:
                            log(f"  - WARNING: Could not get print URL for {title}")
                    else:
                        try:
                            await page.pdf(path=pdf_path, format='A4', print_background=True)
                            log(f"  - Saved PDF (direct) to {filename_base}.pdf")
                        except Exception as pdf_ex:
                            log(f"  - ERROR saving direct PDF for {title}: {pdf_ex}")
                await asyncio.sleep(1)
                i += 1
            except PlaywrightError as e:
                log(f"  - FATAL Playwright error scraping {title}: {e}")
                print(f"\nPlaywright error, attempting to recover... (see log for details)")
                # Пересоздаём браузер и контекст
                try:
                    await context.close()
                except Exception:
                    pass
                try:
                    await browser.close()
                except Exception:
                    pass
                browser = await p.chromium.connect_over_cdp(browserless_url)
                context = await browser.new_context()
                page = await context.new_page()
                # Re-login
                log("Re-logging in after error...")
                await page.goto("https://login.1c.ru/login")
                await page.fill("input#username", username)
                await page.fill("input#password", password)
                await page.press('input#password', 'Enter')
                await page.wait_for_load_state('networkidle')
                log("Re-login successful.")
                # Не увеличиваем i, повторяем попытку для той же статьи
            except Exception as e:
                log(f"  - ERROR scraping {title}: {e}")
                i += 1
                continue
        print_progress(total_articles, total_articles, "Done", "")
        print("\nScraping complete.")
        log("Scraping complete.")

        await browser.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Scrape articles from its.1c.ru.')
    parser.add_argument('url', type=str, help='The URL of the table of contents page.')
    parser.add_argument('--formats', type=str, default='json,pdf,txt', help='Comma-separated list of formats to save (e.g., "json,pdf,txt").')
    parser.add_argument('--chapter', type=str, help='The specific chapter title to scrape (for testing).')
    args = parser.parse_args()
    format_list = [f.strip() for f in args.formats.split(',')]
    asyncio.run(main(args.url, format_list, args.chapter))
