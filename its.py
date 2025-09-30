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
    import markdownify
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
    queue = []
    processed_urls = set()

    # Add initial links to the queue, ensuring no duplicates are added from the start.
    for link in initial_links:
        url_without_fragment = link['url'].split('#')[0]
        if url_without_fragment not in processed_urls:
            queue.append(link)
            processed_urls.add(url_without_fragment)

    log_func(f"Initial unique links to process: {len(queue)}")

    processed_for_content = set() # URLs that have been added to all_articles

    while queue:
        article_info = queue.pop(0)
        
        # Primary check to avoid processing the same URL for content twice
        current_url_normalized = article_info['url'].split('#')[0]
        if current_url_normalized in processed_for_content:
            continue

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
                is_content_page = False
                # Heuristic: if the page has a TOC, but also has significant text content, treat it as an article too.
                body_text = soup.body.get_text(strip=True) if soup.body else ""
                if len(body_text) > 200: # Arbitrary threshold for meaningful content
                    is_content_page = True

                for link in nested_index.find_all('a'):
                    href = link.get('href')
                    text = link.get_text(strip=True)
                    if href and text:
                        full_url = f"https://its.1c.ru{href}"
                        url_without_fragment = full_url.split('#')[0]
                        if url_without_fragment not in processed_urls:
                            new_article = {"title": text, "url": full_url}
                            queue.append(new_article)
                            processed_urls.add(url_without_fragment)
                            log_func(f"      - Queued nested link: {text}")
                
                if is_content_page:
                    log_func(f"    - Page '{article_info['title']}' is a TOC but also treated as content.")
                    all_articles.append(article_info)
                    processed_for_content.add(current_url_normalized)

            else:
                log_func(f"    - Confirmed as content page: {article_info['title']}")
                all_articles.append(article_info)
                processed_for_content.add(current_url_normalized)

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
        info_str = f"({current}/{total}) {title}"
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

    base_articles_dir = os.path.join(output_dir, "articles")
    tmp_index_dir = os.path.join(output_dir, "tmp_index")
    json_dir = os.path.join(base_articles_dir, "json")
    pdf_dir = os.path.join(base_articles_dir, "pdf")
    txt_dir = os.path.join(base_articles_dir, "txt")
    markdown_dir = os.path.join(base_articles_dir, "markdown")

    if os.path.exists(base_articles_dir):
        shutil.rmtree(base_articles_dir)
    if os.path.exists(tmp_index_dir):
        shutil.rmtree(tmp_index_dir)
    os.makedirs(json_dir, exist_ok=True)
    os.makedirs(pdf_dir, exist_ok=True)
    os.makedirs(txt_dir, exist_ok=True)
    os.makedirs(markdown_dir, exist_ok=True)
    os.makedirs(tmp_index_dir, exist_ok=True)

    with open(log_file_path, "w", encoding="utf-8") as f:
        pass

    log(f"---\nScript: its_v9.py\nTimestamp: {timestamp}")
    log(f"URL: {toc_url}\nFormats: {formats}\nChapter: {target_chapter}")
    if not await check_dependencies(log):
        return

    username = os.environ.get("LOGIN_1C_USER")
    password = os.environ.get("LOGIN_1C_PASSWORD")
    browserless_url = os.environ.get('BROWSERLESS_URL', 'http://localhost:3000')

    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(browserless_url)
        context = await browser.new_context()
        
        # --- 1. Login --- 
        try:
            print("Step 1: Logging in...")
            log("Step 1: Logging in...")
            page = await context.new_page()
            await page.goto("https://login.1c.ru/login")
            await page.fill("input#username", username)
            await page.fill("input#password", password)
            await page.press('input#password', 'Enter')
            await page.wait_for_load_state('networkidle')
            await page.close()
            print("Login successful.")
            log("Login successful.")
        except Exception as e:
            log(f"FATAL: Login failed: {e}")
            print(f"FATAL: Login failed. Check credentials and network. Error: {e}")
            await browser.close()
            return

        # --- 2. Get Initial TOC ---
        initial_toc_links = []
        try:
            print(f"Step 2: Scraping initial table of contents from {toc_url}...")
            log(f"Step 2: Scraping initial table of contents...")
            page = await context.new_page()
            await page.goto(toc_url)
            await page.wait_for_load_state('networkidle')
            page_content = await page.content()
            await page.close()
            soup = BeautifulSoup(page_content, 'html.parser')
            toc_div = soup.find('div', id='w_metadata_toc')
            if toc_div:
                for i, link in enumerate(toc_div.select('ul li a')):
                    href = link.get('href')
                    text = link.get_text(strip=True)
                    if href and text:
                        initial_toc_links.append({"title": text, "url": f"https://its.1c.ru{href}", "original_order": i})
                log(f"Found {len(initial_toc_links)} initial links.")
            else:
                raise Exception("Could not find the table of contents div with id 'w_metadata_toc'.")
        except Exception as e:
            log(f"FATAL: Failed to get initial TOC: {e}")
            print(f"FATAL: Could not get initial table of contents. Error: {e}")
            await browser.close()
            return

        if target_chapter:
            initial_toc_links = [link for link in initial_toc_links if link['title'] == target_chapter]

        # --- 3. Discovery Pass ---
        print("Step 3: Discovering all unique articles and creating index...")
        log("Step 3: Discovering and Indexing...")
        queue = initial_toc_links[:]
        processed_urls = set()
        scraped_content_hashes = set()
        discovery_count = 0
        while discovery_count < len(queue):
            article_info = queue[discovery_count]
            url_without_fragment = article_info['url'].split('#')[0]
            print_progress(discovery_count, len(queue), "Discovering", article_info['title'])

            if url_without_fragment in processed_urls:
                discovery_count += 1
                continue

            page = None
            try:
                page = await context.new_page()
                await page.goto(article_info['url'], timeout=90000)
                await page.wait_for_load_state('networkidle')
                article_frame = page.frame(name="w_metadata_doc_frame")
                if not article_frame:
                    raise Exception("Could not find article frame.")

                iframe_html = await article_frame.content()
                soup = BeautifulSoup(iframe_html, 'html.parser')
                content_div = soup.find('body')
                if not content_div:
                    raise Exception("Could not find body content.")

                article_text = content_div.get_text(separator='\n', strip=True)
                content_hash = hash(article_text)

                if content_hash not in scraped_content_hashes:
                    scraped_content_hashes.add(content_hash)
                    index_data = {"title": article_info["title"], "url": article_info["url"], "original_order": article_info.get("original_order", 9999)}
                    index_filename = f"{hash(article_info['url'])}.json"
                    with open(os.path.join(tmp_index_dir, index_filename), "w", encoding="utf-8") as f:
                        json.dump(index_data, f)
                
                processed_urls.add(url_without_fragment)
                nested_index = soup.find('div', class_='index')
                if nested_index and nested_index.find('a'):
                    for link in nested_index.find_all('a'):
                        href = link.get('href')
                        text = link.get_text(strip=True)
                        if href and text:
                            full_url = f"https://its.1c.ru{href}"
                            if full_url.split('#')[0] not in processed_urls:
                                queue.append({"title": text, "url": full_url})
                await asyncio.sleep(0.2)
                discovery_count += 1

            except PlaywrightError as e:
                log(f"  - FATAL Playwright error during discovery: {e}")
                print(f"\nPlaywright error, attempting to recover...")
                if page: await page.close()
                try:
                    await context.close()
                    await browser.close()
                except Exception: pass
                browser = await p.chromium.connect_over_cdp(browserless_url)
                context = await browser.new_context()
                log("Re-logging in after error...")
                login_page = await context.new_page()
                await login_page.goto("https://login.1c.ru/login")
                await login_page.fill("input#username", username)
                await login_page.fill("input#password", password)
                await login_page.press('input#password', 'Enter')
                await login_page.wait_for_load_state('networkidle')
                await login_page.close()
                log("Re-login successful. Cooling down for 5 seconds...")
                await asyncio.sleep(5)
                continue
            except Exception as e:
                log(f"  - NON-FATAL ERROR during discovery for {article_info['title']}: {e}")
                discovery_count += 1
                continue
            finally:
                if page: await page.close()

        # --- 4. Scraping Pass ---
        print("\nStep 4: Reading index and starting final scrape...")
        log("Step 4: Reading index and starting final scrape...")
        final_articles_list = []
        for filename in os.listdir(tmp_index_dir):
            with open(os.path.join(tmp_index_dir, filename), "r", encoding="utf-8") as f:
                final_articles_list.append(json.load(f))
        final_articles_list.sort(key=lambda x: (x['original_order'], x['title']))

        i = 0
        while i < len(final_articles_list):
            article_info = final_articles_list[i]
            print_progress(i + 1, len(final_articles_list), "Scraping", article_info['title'])
            page = None
            try:
                page = await context.new_page()
                await page.goto(article_info['url'], timeout=90000)
                await page.wait_for_load_state('networkidle')
                article_frame = page.frame(name="w_metadata_doc_frame")
                if not article_frame:
                    raise Exception("Could not find article frame for final scrape.")

                number = f"{i+1:03d}"
                sanitized_title = "".join([c for c in article_info['title'].lower() if c.isalnum() or c==' ']).rstrip().replace(" ", "_")
                filename_base = f"{number}_{sanitized_title}"

                if 'json' in formats or 'txt' in formats or 'markdown' in formats:
                    iframe_html = await article_frame.content()
                    soup = BeautifulSoup(iframe_html, 'html.parser')
                    content_div = soup.find('body')
                    article_text = content_div.get_text(separator='\n', strip=True)
                    if 'json' in formats:
                        with open(os.path.join(json_dir, f"{filename_base}.json"), "w", encoding="utf-8") as f:
                            json.dump({"title": article_info['title'], "content": article_text}, f, ensure_ascii=False, indent=4)
                    if 'txt' in formats:
                        with open(os.path.join(txt_dir, f"{filename_base}.txt"), "w", encoding="utf-8") as f:
                            f.write(article_text)
                    if 'markdown' in formats:
                        with open(os.path.join(markdown_dir, f"{filename_base}.md"), "w", encoding="utf-8") as f:
                            f.write(markdownify.markdownify(str(content_div), heading_style="ATX"))
                
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
                                with open(pdf_path, "wb") as f:
                                    f.write(await print_page.pdf(format='A4', print_background=True))
                            finally:
                                await print_page.close()
                    else:
                        with open(pdf_path, "wb") as f:
                            f.write(await page.pdf(format='A4', print_background=True))
                
                await asyncio.sleep(0.5)
                i += 1
            except PlaywrightError as e:
                log(f"  - FATAL Playwright error during final scrape: {e}")
                print(f"\nPlaywright error, attempting to recover...")
                if page: await page.close()
                try:
                    await context.close()
                    await browser.close()
                except Exception: pass
                browser = await p.chromium.connect_over_cdp(browserless_url)
                context = await browser.new_context()
                log("Re-logging in after error...")
                login_page = await context.new_page()
                await login_page.goto("https://login.1c.ru/login")
                await login_page.fill("input#username", username)
                await login_page.fill("input#password", password)
                await login_page.press('input#password', 'Enter')
                await login_page.wait_for_load_state('networkidle')
                await login_page.close()
                log("Re-login successful. Cooling down for 5 seconds...")
                await asyncio.sleep(5)
                continue
            except Exception as e:
                log(f"  - NON-FATAL ERROR during final scraping of {article_info['title']}: {e}")
                i += 1
                continue
            finally:
                if page: await page.close()

        # --- 5. Cleanup ---
        print("\nStep 5: Cleaning up temporary files...")
        log("Step 5: Cleaning up temporary files...")
        shutil.rmtree(tmp_index_dir)

        print(f"\nScraping complete. Saved {len(final_articles_list)} unique articles.")
        log(f"Scraping complete. Saved {len(final_articles_list)} unique articles.")

        await browser.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Scrape articles from its.1c.ru.')
    parser.add_argument('url', type=str, help='The URL of the table of contents page.')
    parser.add_argument('--formats', type=str, default='json,pdf,txt', help='Comma-separated list of formats to save (e.g., "json,pdf,txt").')
    parser.add_argument('--chapter', type=str, help='The specific chapter title to scrape (for testing).')
    args = parser.parse_args()
    format_list = [f.strip() for f in args.formats.split(',')]
    asyncio.run(main(args.url, format_list, args.chapter))
