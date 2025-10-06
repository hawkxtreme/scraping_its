import asyncio
import os
import time
from playwright.async_api import async_playwright, Error as PlaywrightError, Page, Browser, BrowserContext
from bs4 import BeautifulSoup
from tqdm import tqdm

# Import modularized components
from . import config
from . import parser
from . import file_manager
from . import cache

class Scraper:
    """Manages all web scraping operations using Playwright."""

    def __init__(self, log_func, shared_hashes=None, use_cache=True):
        self.log = log_func
        self.playwright = None
        self.browser: Browser = None
        self.context: BrowserContext = None
        if shared_hashes is not None:
            self.scraped_content_hashes = shared_hashes
        else:
            self.scraped_content_hashes = set()
        
        # Initialize cache manager
        self.use_cache = use_cache
        if self.use_cache:
            self.cache_manager = cache.CacheManager(log_func)
        else:
            self.cache_manager = None

    async def connect(self):
        """Connects to the browser."""
        connect_start = time.monotonic()
        try:
            self.log.logger.debug("Attempting to connect to browserless service")
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.connect_over_cdp(config.BROWSERLESS_URL)
            self.context = await self.browser.new_context()
            
            connect_duration = time.monotonic() - connect_start
            self.log.logger.log_performance("Browser connection", connect_duration)
        except Exception as e:
            self.log.logger.error("Failed to connect to browser", e)
            raise

    async def close(self):
        """Closes browser connection and Playwright instance."""
        close_start = time.monotonic()
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            
            close_duration = time.monotonic() - close_start
            self.log.logger.log_performance("Browser disconnection", close_duration)
            self.log.logger.info("Browser connection closed.")
        except Exception as e:
            self.log.logger.warning("Error during browser cleanup", e)

    async def login(self):
        """Performs login to the website."""
        page = None
        login_start = time.monotonic()
        try:
            self.log.logger.log_step("Performing login to 1C website")
            page = await self.context.new_page()
            
            # Navigate to login page
            self.log.logger.debug("Navigating to login page")
            await page.goto(config.LOGIN_URL, timeout=config.login_timeout)
            await page.wait_for_load_state('networkidle', timeout=config.network_idle_timeout)
            
            # Fill login form
            self.log.logger.debug("Filling login form")
            await page.fill("input#username", config.LOGIN_1C_USER)
            await page.fill("input#password", config.LOGIN_1C_PASSWORD)
            await page.click('#loginButton')
            await page.wait_for_load_state('networkidle')
            
            # Check for login success by looking for the profile URL
            current_url = page.url
            self.log.logger.debug(f"Login redirected to: {current_url}")
            
            if current_url != "https://login.1c.ru/user/profile":
                # Try to get error message if login failed
                try:
                    error_element = await page.query_selector('.error-message, .alert-danger, [class*="error"]')
                    error_text = await error_element.text_content() if error_element else "No error message found"
                    self.log.logger.error(f"Login failed with error: {error_text}")
                except:
                    self.log.logger.error("Login failed, did not redirect to profile page")
                raise PlaywrightError("Login failed, did not redirect to profile page.")
            
            login_duration = time.monotonic() - login_start
            self.log.logger.log_performance("Login process", login_duration)
            self.log.logger.info("Login successful.")
        except Exception as e:
            self.log.logger.error("Login process failed", e)
            raise # Re-raise the exception to be caught by the main loop
        finally:
            await self._safely_close_page(page)

    async def get_initial_toc(self, url, target_chapter):
        """Scrapes the initial table of contents."""
        page = None
        toc_start = time.monotonic()
        try:
            self.log.logger.log_step("Scraping initial table of contents", {
                "url": url,
                "target_chapter": target_chapter
            })
            
            page = await self.context.new_page()
            await page.goto(url, timeout=config.page_timeout)
            await page.wait_for_load_state('networkidle', timeout=config.network_idle_timeout)
            page_content = await page.content()
            
            parser_module = parser.get_parser_for_url(url)
            initial_toc_links = parser_module.extract_toc_links(page_content)
            
            self.log.logger.info(f"Found {len(initial_toc_links)} initial links.")

            if target_chapter:
                initial_toc_links = [link for link in initial_toc_links if link['title'] == target_chapter]
                self.log.logger.info(f"Filtered to {len(initial_toc_links)} links based on chapter: '{target_chapter}'.")

            toc_duration = time.monotonic() - toc_start
            self.log.logger.log_performance("TOC scraping", toc_duration, {
                "links_found": len(initial_toc_links)
            })
            
            return initial_toc_links
        except Exception as e:
            self.log.logger.error("Failed to get initial TOC", e)
            raise
        finally:
            await self._safely_close_page(page)



    async def scrape_single_article(self, article_info, formats, i, pbar, update_mode=False):
        """Scrapes the final content for a single article."""
        page = None
        scrape_start = time.monotonic()
        article_title = article_info.get('title', 'Unknown Article')
        article_url = article_info['url']
        
        try:
            # Check cache first if enabled
            if self.use_cache and self.cache_manager:
                existing_hash = article_info.get('content_hash')
                if self.cache_manager.is_cached(article_url, formats, existing_hash):
                    self.log.logger.info(f"Using cached content for: {article_title}")
                    
                    # Get cached content
                    cached_files = self.cache_manager.get_cached_content(article_url, formats, config.get_output_dir())
                    
                    if cached_files:
                        # Update progress bar
                        pbar.update(1)
                        
                        # For cached content, we need to try to get the content hash from the cache manager
                        # The cache manager should have stored the hash when the content was originally cached
                        cache_entry_hash = self.cache_manager.get_content_hash(article_url, formats)
                        if cache_entry_hash:
                            article_info["content_hash"] = cache_entry_hash
                            self.log.logger.debug(f"Retrieved content hash from cache: {cache_entry_hash}")
                        
                        # Log performance
                        scrape_duration = time.monotonic() - scrape_start
                        self.log.logger.log_performance(f"Article retrieval from cache: {article_title}", scrape_duration)
                        return article_info  # Return article_info with content_hash
                    else:
                        self.log.logger.warning(f"Cache entry existed but files were missing for: {article_title}")
            
            self.log.logger.debug(f"Starting to scrape article: {article_title}")
            page = await self.context.new_page()
            await page.goto(article_url, timeout=90000)
            await page.wait_for_load_state('networkidle')

            parser_module = parser.get_parser_for_url(article_url)

            if parser_module.__name__ == 'src.parser_v2' or 'cabinetdoc' in article_url:
                content_html = await page.content()
                soup, _, content_hash = parser_module.parse_article_page(content_html)
            else:
                article_frame = page.frame(name="w_metadata_doc_frame")
                if not article_frame:
                    raise PlaywrightError(f"Could not find article frame for {article_url}")
                iframe_html = await article_frame.content()
                soup, _, content_hash = parser_module.parse_article_page(iframe_html)

            # Check for duplicate content - but be less aggressive
            if content_hash in self.scraped_content_hashes:
                self.log.logger.debug(f"Skipping duplicate content: {article_title} (hash: {content_hash})")
                pbar.update(1)
                return article_info  # Return article_info with existing content_hash
            
            # In update mode, check if content has changed compared to existing metadata
            if update_mode and 'content_hash' in article_info:
                existing_hash = article_info.get('content_hash')
                if existing_hash == content_hash:
                    self.log.logger.debug(f"Skipping unchanged article: {article_title}")
                    pbar.update(1)
                    return article_info  # Return article_info with existing content_hash
            
            # Add to hashes only if content is not empty
            if content_hash != 0 and content_hash is not None:
                self.scraped_content_hashes.add(content_hash)
            else:
                self.log.logger.warning(f"Empty or invalid content hash for {article_title}, proceeding anyway")

            # Use the filename_base provided by the index loader
            filename_base = article_info.get("filename_base")
            if not filename_base:
                # Fallback for safety, though it shouldn't be needed
                self.log.logger.warning(f"filename_base not found for {article_title}. Generating a fallback.")
                number = f"{i+1:03d}"
                sanitized_title = "".join([c for c in article_title.lower() if c.isalnum() or c==' ']).rstrip().replace(" ", "_")
                filename_base = f"{number}_{sanitized_title[:50]}"
            # IMPORTANT: Ensure the filename_base is stored back in the article_info dict
            # so it can be used by the TOC and metadata generation.
            article_info["filename_base"] = filename_base

            # Add content hash to article_info so it's preserved in meta.json
            article_info["content_hash"] = content_hash

            # Save article content in specified formats
            file_manager.save_article_content(filename_base, formats, soup, article_info, self.log)
            self.log.logger.info(f"Saved article: {article_title} (filename: {filename_base})")
            
            # Collect saved files for caching
            saved_files = {}
            for format_type in formats:
                if format_type == 'json':
                    saved_files[format_type] = os.path.join(config.get_json_dir(), f"{filename_base}.json")
                elif format_type == 'pdf':
                    pdf_path = os.path.join(config.get_pdf_dir(), f"{filename_base}.pdf")
                    await self._save_as_pdf(page, pdf_path)
                    saved_files[format_type] = pdf_path
                    self.log.logger.info(f"Saved PDF: {pdf_path}")
                elif format_type == 'txt':
                    saved_files[format_type] = os.path.join(config.get_txt_dir(), f"{filename_base}.txt")
                elif format_type == 'markdown':
                    saved_files[format_type] = os.path.join(config.get_markdown_dir(), f"{filename_base}.md")
                elif format_type == 'docx':
                    saved_files[format_type] = os.path.join(config.get_docx_dir(), f"{filename_base}.docx")
            
            # Cache the content if caching is enabled
            if self.use_cache and self.cache_manager:
                self.cache_manager.cache_content(article_url, formats, saved_files, content_hash)
            
            scrape_duration = time.monotonic() - scrape_start
            self.log.logger.log_performance(f"Article scraping: {article_title}", scrape_duration)
            
            await asyncio.sleep(0.5)
            pbar.update(1)
            
            # Return the updated article_info with content_hash
            return article_info
        except Exception as e:
            self.log.logger.error(f"Non-fatal error during scraping of {article_title}", e)
            return article_info  # Return article_info even if there was an error
        finally:
            await self._safely_close_page(page)

    async def _safely_close_page(self, page: Page):
        """Helper function to safely close a page."""
        try:
            if page:
                await page.close()
        except Exception as e:
            self.log.logger.warning("Error closing page", e)

    async def _save_as_pdf(self, page: Page, path: str):
        """Helper function to save a page as a PDF, trying the print-friendly link first."""
        print_page = None
        pdf_start = time.monotonic()
        try:
            self.log.logger.debug(f"Generating PDF for {page.url}")
            
            print_link_element = await page.query_selector('#w_metadata_print_href')
            if print_link_element:
                print_url = await print_link_element.get_attribute('href')
                if print_url:
                    if not print_url.startswith('http'):
                        print_url = f"{config.BASE_URL}{print_url}"
                    
                    self.log.logger.debug(f"Using print-friendly URL: {print_url}")
                    print_page = await self.context.new_page()
                    await print_page.goto(print_url, timeout=90000)
                    await print_page.wait_for_load_state('networkidle', timeout=60000)
                    pdf_bytes = await print_page.pdf(format='A4', print_background=True)
                    with open(path, "wb") as f:
                        f.write(pdf_bytes)
                    
                    pdf_duration = time.monotonic() - pdf_start
                    self.log.logger.log_performance("PDF generation (print-friendly)", pdf_duration)
                    return

            # Fallback to direct PDF generation
            self.log.logger.debug("Using direct PDF generation")
            pdf_bytes = await page.pdf(format='A4', print_background=True)
            with open(path, "wb") as f:
                f.write(pdf_bytes)
            
            pdf_duration = time.monotonic() - pdf_start
            self.log.logger.log_performance("PDF generation (direct)", pdf_duration)

        except Exception as e:
            self.log.logger.error(f"Could not save PDF for {page.url}", e)
            with open(f"{path}.error.txt", "w") as f:
                f.write(f"Failed to generate PDF due to: {e}")
        finally:
            if print_page:
                await print_page.close()