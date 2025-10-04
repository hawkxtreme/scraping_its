import asyncio
import os
from playwright.async_api import async_playwright, Error as PlaywrightError, Page, Browser, BrowserContext
from bs4 import BeautifulSoup
from tqdm import tqdm

# Import modularized components
from . import config
from . import parser
from . import file_manager

class Scraper:
    """Manages all web scraping operations using Playwright."""

    def __init__(self, log_func, shared_hashes=None):
        self.log = log_func
        self.playwright = None
        self.browser: Browser = None
        self.context: BrowserContext = None
        if shared_hashes is not None:
            self.scraped_content_hashes = shared_hashes
        else:
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
            await self._safely_close_page(page)

    async def get_initial_toc(self, url, target_chapter):
        """Scrapes the initial table of contents."""
        page = None
        try:
            self.log(f"Step 4: Scraping initial table of contents from {url}...")
            page = await self.context.new_page()
            await page.goto(url, timeout=90000)
            await page.wait_for_load_state('networkidle')
            page_content = await page.content()
            
            parser_module = parser.get_parser_for_url(url)
            initial_toc_links = parser_module.extract_toc_links(page_content)
            self.log(f"Found {len(initial_toc_links)} initial links.")

            if target_chapter:
                initial_toc_links = [link for link in initial_toc_links if link['title'] == target_chapter]
                self.log(f"Filtered to {len(initial_toc_links)} links based on chapter: '{target_chapter}'.")

            return initial_toc_links
        except Exception as e:
            self.log(f"FATAL: Failed to get initial TOC: {e}")
            raise
        finally:
            await self._safely_close_page(page)



    async def scrape_single_article(self, article_info, formats, i, pbar):
        """Scrapes the final content for a single article."""
        page = None
        try:
            page = await self.context.new_page()
            await page.goto(article_info['url'], timeout=90000)
            await page.wait_for_load_state('networkidle')

            parser_module = parser.get_parser_for_url(article_info['url'])

            if parser_module.__name__ == 'src.parser_v2' or 'cabinetdoc' in article_info['url']:
                content_html = await page.content()
                soup, _, content_hash = parser_module.parse_article_page(content_html)
            else:
                article_frame = page.frame(name="w_metadata_doc_frame")
                if not article_frame:
                    raise PlaywrightError(f"Could not find article frame for {article_info['url']}")
                iframe_html = await article_frame.content()
                soup, _, content_hash = parser_module.parse_article_page(iframe_html)

            # Check for duplicate content - but be less aggressive
            if content_hash in self.scraped_content_hashes:
                self.log(f"  - Skipping duplicate content: {article_info['title']} (hash: {content_hash})")
                pbar.update(1)
                return
            
            # Add to hashes only if content is not empty
            if content_hash != 0 and content_hash is not None:
                self.scraped_content_hashes.add(content_hash)
            else:
                self.log(f"  - Warning: Empty or invalid content hash for {article_info['title']}, proceeding anyway")

            # Use the filename_base provided by the index loader
            filename_base = article_info.get("filename_base")
            if not filename_base:
                # Fallback for safety, though it shouldn't be needed
                self.log(f"Warning: filename_base not found for {article_info['title']}. Generating a fallback.")
                number = f"{i+1:03d}"
                sanitized_title = "".join([c for c in article_info['title'].lower() if c.isalnum() or c==' ']).rstrip().replace(" ", "_")
                filename_base = f"{number}_{sanitized_title[:50]}"
            # IMPORTANT: Ensure the filename_base is stored back in the article_info dict 
            # so it can be used by the TOC and metadata generation.
            article_info["filename_base"] = filename_base

            # Save article content in specified formats
            file_manager.save_article_content(filename_base, formats, soup, article_info)
            self.log(f"  - Saved article: {article_info['title']} (filename: {filename_base})")
            
            if 'pdf' in formats:
                pdf_path = os.path.join(config.get_pdf_dir(), f"{filename_base}.pdf")
                await self._save_as_pdf(page, pdf_path)
                self.log(f"  - Saved PDF: {pdf_path}")
            
            await asyncio.sleep(0.5)
            pbar.update(1)
        except Exception as e:
            self.log(f"  - NON-FATAL ERROR during final scraping of {article_info['title']}: {e}")
        finally:
            await self._safely_close_page(page)

    async def _safely_close_page(self, page: Page):
        """Helper function to safely close a page."""
        try:
            if page:
                await page.close()
        except Exception as e:
            self.log(f"Warning: Error closing page: {e}")

    async def _save_as_pdf(self, page: Page, path: str):
        """Helper function to save a page as a PDF, trying the print-friendly link first."""
        print_page = None
        try:
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

            pdf_bytes = await page.pdf(format='A4', print_background=True)
            with open(path, "wb") as f:
                f.write(pdf_bytes)

        except Exception as e:
            self.log(f"    - Could not save PDF for {page.url}: {e}")
            with open(f"{path}.error.txt", "w") as f:
                f.write(f"Failed to generate PDF due to: {e}")
        finally:
            if print_page: await print_page.close()