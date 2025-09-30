import asyncio
import os
from playwright.async_api import async_playwright, Error as PlaywrightError, Page, Browser, BrowserContext
from bs4 import BeautifulSoup

# Import modularized components
import config
import parser
import file_manager
from ui import print_progress

class Scraper:
    """Manages all web scraping operations using Playwright."""

    def __init__(self, log_func):
        self.log = log_func
        self.browser: Browser = None
        self.context: BrowserContext = None
        self.scraped_content_hashes = set()

    async def connect(self):
        """Connects to the browser."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.connect_over_cdp(config.BROWSERLESS_URL)
        self.context = await self.browser.new_context()

    async def close(self):
        """Closes browser connection and Playwright instance."""
        if self.context: await self.context.close()
        if self.browser: await self.browser.close()
        if self.playwright: await self.playwright.stop()
        self.log("Browser connection closed.")

    async def login(self):
        """Performs login to the website."""
        page = None
        try:
            self.log("Step 3: Logging in...")
            page = await self.context.new_page()
            await page.goto(config.LOGIN_URL, timeout=60000)
            await page.wait_for_load_state('networkidle')
            await page.fill("input#username", config.LOGIN_1C_USER)
            await page.fill("input#password", config.LOGIN_1C_PASSWORD)
            await page.click('#loginButton')
            await page.wait_for_load_state('networkidle')
            # Check for login success by looking for the profile URL
            if page.url != "https://login.1c.ru/user/profile":
                raise PlaywrightError("Login failed, did not redirect to profile page.")
            self.log("Login successful.")
        except Exception as e:
            self.log(f"FATAL: Login failed: {e}")
            raise # Re-raise the exception to be caught by the main loop
        finally:
            if page: await page.close()

    async def get_initial_toc(self, url, target_chapter):
        """Scrapes the initial table of contents."""
        page = None
        try:
            self.log(f"Step 4: Scraping initial table of contents from {url}...")
            page = await self.context.new_page()
            await page.goto(url, timeout=90000)
            await page.wait_for_load_state('networkidle')
            page_content = await page.content()
            
            initial_toc_links = parser.extract_toc_links(page_content)
            self.log(f"Found {len(initial_toc_links)} initial links.")

            if target_chapter:
                initial_toc_links = [link for link in initial_toc_links if link['title'] == target_chapter]
                self.log(f"Filtered to {len(initial_toc_links)} links based on chapter: '{target_chapter}'.")

            return initial_toc_links
        except Exception as e:
            self.log(f"FATAL: Failed to get initial TOC: {e}")
            raise
        finally:
            if page: await page.close()

    async def discover_articles(self, initial_links):
        """Discovers all unique articles by crawling from the initial TOC."""
        self.log("Step 4: Discovering and Indexing...")
        
        queue = initial_links[:]
        processed_urls = set()
        i = 0
        while i < len(queue):
            article_info = queue[i]
            url_without_fragment = article_info['url'].split('#')[0]
            print_progress(i, len(queue), "Discovering", article_info['title'])

            if url_without_fragment in processed_urls:
                i += 1
                continue

            page = None
            try:
                page = await self.context.new_page()
                await page.goto(article_info['url'], timeout=90000)
                await page.wait_for_load_state('networkidle')
                article_frame = page.frame(name="w_metadata_doc_frame")
                if not article_frame:
                    raise PlaywrightError(f"Could not find article frame for {article_info['url']}")

                iframe_html = await article_frame.content()
                soup, nested_links, content_hash = parser.parse_article_page(iframe_html)

                if content_hash not in self.scraped_content_hashes:
                    self.scraped_content_hashes.add(content_hash)
                    file_manager.save_index_data(article_info)
                
                processed_urls.add(url_without_fragment)

                for link_info in nested_links:
                    if link_info['url'].split('#')[0] not in processed_urls:
                        queue.append(link_info)
                
                await asyncio.sleep(0.2) # Be respectful to the server
            except Exception as e:
                self.log(f"  - ERROR during discovery for {article_info['title']}: {e}")
                # In a real-world scenario, you might add retry logic here
            finally:
                i += 1
                if page: await page.close()
        
        print_progress(len(queue), len(queue), "Discovering", "Done!")

    async def scrape_final_articles(self, articles_to_scrape, formats):
        """Scrapes the final content for each article in the list."""
        self.log("Step 5: Reading index and starting final scrape...")
        total_articles = len(articles_to_scrape)

        for i, article_info in enumerate(articles_to_scrape):
            print_progress(i + 1, total_articles, "Scraping", article_info['title'])
            page = None
            try:
                page = await self.context.new_page()
                await page.goto(article_info['url'], timeout=90000)
                await page.wait_for_load_state('networkidle')
                article_frame = page.frame(name="w_metadata_doc_frame")
                if not article_frame:
                    raise PlaywrightError("Could not find article frame for final scrape.")

                number = f"{i+1:03d}"
                sanitized_title = "".join([c for c in article_info['title'].lower() if c.isalnum() or c==' ']).rstrip().replace(" ", "_")
                filename_base = f"{number}_{sanitized_title[:50]}" # Truncate long titles

                # Save text-based formats
                iframe_html = await article_frame.content()
                soup = BeautifulSoup(iframe_html, 'html.parser')
                file_manager.save_article_content(filename_base, formats, soup, article_info)
                
                # Save PDF format
                if 'pdf' in formats:
                    pdf_path = os.path.join(config.PDF_DIR, f"{filename_base}.pdf")
                    await self._save_as_pdf(page, pdf_path)
                
                await asyncio.sleep(0.5) # Be respectful
            except Exception as e:
                self.log(f"  - NON-FATAL ERROR during final scraping of {article_info['title']}: {e}")
                continue # Skip to the next article
            finally:
                if page: await page.close()
        print_progress(total_articles, total_articles, "Scraping", "Done!")

    async def _save_as_pdf(self, page: Page, path: str):
        """Helper function to save a page as a PDF, trying the print-friendly link first."""
        print_page = None
        try:
            # Check for a print-friendly version link
            print_link_element = await page.query_selector('#w_metadata_print_href')
            if print_link_element:
                print_url = await print_link_element.get_attribute('href')
                if print_url:
                    if not print_url.startswith('http'):
                        print_url = f"{config.BASE_URL}{print_url}"
                    
                    print_page = await self.context.new_page()
                    await print_page.goto(print_url, timeout=90000)
                    await print_page.wait_for_load_state('networkidle', timeout=60000)
                    pdf_bytes = await print_page.pdf(format='A4', print_background=True)
                    with open(path, "wb") as f:
                        f.write(pdf_bytes)
                    return

            # Fallback to printing the main page if no print link is found
            pdf_bytes = await page.pdf(format='A4', print_background=True)
            with open(path, "wb") as f:
                f.write(pdf_bytes)

        except Exception as e:
            self.log(f"    - Could not save PDF for {page.url}: {e}")
            # Optionally, create an empty file or a text file with the error
            with open(f"{path}.error.txt", "w") as f:
                f.write(f"Failed to generate PDF due to: {e}")
        finally:
            if print_page: await print_page.close()
