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
        """Closes the browser context, leaving the browser connection open for other workers."""
        if self.context:
            await self.context.close()
        # The browser connection and Playwright instance are managed by other workers
        # or the main process and should not be closed here to prevent race conditions.
        self.log("Browser context closed, connection remains open for other workers.")

    async def reconnect(self):
        """Safely closes existing connections and re-establishes a new one."""
        self.log("Attempting to reconnect...")
        try:
            if self.context and not self.context.is_closed():
                await self.context.close()
        except Exception as e:
            self.log(f"Warning: Error closing context during reconnect: {e}")
        try:
            if self.browser and self.browser.is_connected():
                await self.browser.close()
        except Exception as e:
            self.log(f"Warning: Error closing browser during reconnect: {e}")
        try:
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            self.log(f"Warning: Error stopping playwright during reconnect: {e}")
        
        await self.connect()
        await self.login()
        self.log("Reconnect successful.")

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

    async def get_initial_toc(self, url):
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

            return initial_toc_links
        except Exception as e:
            self.log(f"FATAL: Failed to get initial TOC: {e}")
            raise
        finally:
            await self._safely_close_page(page)

    async def discover_nested_articles(self, toc_tree, max_depth=3):
        """
        Recursively discovers nested articles within pages (for parser_v2).
        
        Args:
            toc_tree: Initial TOC tree structure
            max_depth: Maximum recursion depth
            
        Returns:
            Updated TOC tree with discovered nested articles
        """
        visited_urls = set()
        
        async def process_node(node, current_depth):
            """Recursively process a node and discover nested links."""
            if current_depth >= max_depth:
                return
                
            url = node.get("url")
            if not url or url in visited_urls:
                return
                
            visited_urls.add(url)
            
            # Visit the page and extract nested links
            page = None
            try:
                page = await self.context.new_page()
                await page.goto(url, timeout=90000)
                await page.wait_for_load_state('networkidle')
                page_content = await page.content()
                
                parser_module = parser.get_parser_for_url(url)
                
                # For parser_v2, parse the page to find nested links
                if parser_module.__name__ == 'src.parser_v2':
                    try:
                        # Check if page has iframe with content
                        article_frame = page.frame(name="w_metadata_doc_frame")
                        if article_frame:
                            # Content is in iframe (like /content/ pages)
                            iframe_html = await article_frame.content()
                            _, nested_links, _ = parser_module.parse_article_page(iframe_html)
                        else:
                            # Content is in main page (like /browse/ pages)
                            _, nested_links, _ = parser_module.parse_article_page(page_content)
                        
                        # Add nested links as children if not already present
                        existing_urls = {child.get("url") for child in node.get("children", [])}
                        
                        for nested_link in nested_links:
                            nested_url = nested_link.get("url")
                            if nested_url and nested_url not in existing_urls and nested_url not in visited_urls:
                                new_node = {
                                    "title": nested_link.get("title"),
                                    "url": nested_url,
                                    "children": []
                                }
                                node.setdefault("children", []).append(new_node)
                                
                                # Recursively process the new node
                                await process_node(new_node, current_depth + 1)
                                
                    except Exception as e:
                        self.log(f"  - Could not parse nested links from {url}: {e}")
                        
            except Exception as e:
                self.log(f"  - Could not visit {url} for nested discovery: {e}")
            finally:
                await self._safely_close_page(page)
            
            # Process existing children
            for child in node.get("children", []):
                await process_node(child, current_depth + 1)
        
        # Process all top-level nodes
        for node in toc_tree:
            await process_node(node, 0)
            
        total_discovered = len(visited_urls)
        self.log(f"Discovered {total_discovered} total articles through recursive search.")
        
        return toc_tree



    async def scrape_single_article(self, article_info, formats, i, pbar, update_mode=False, rag_mode=False):
        """Scrapes the final content for a single article."""
        page = None
        try:
            self.log(f"  -> Attempting to scrape: {article_info['title']} ({article_info['url']})")
            page = await self.context.new_page()

            try:
                await page.goto(article_info['url'], timeout=120000) # Increased timeout
                await page.wait_for_load_state('networkidle', timeout=60000)

                parser_module = parser.get_parser_for_url(article_info['url'])

                # For parser_v2, check if page uses iframe (like /content/XXX/hdoc pages)
                if parser_module.__name__ == 'src.parser_v2':
                    # Check if page has iframe with content
                    article_frame = page.frame(name="w_metadata_doc_frame")
                    if article_frame:
                        # Content is in iframe (like /content/ pages)
                        self.log(f"  - Extracting from iframe for {article_info['url']}")
                        iframe_html = await article_frame.content()
                        soup, _, content_hash = parser_module.parse_article_page(iframe_html)
                    else:
                        # Content is in main page (like /browse/ pages)
                        content_html = await page.content()
                        soup, _, content_hash = parser_module.parse_article_page(content_html)
                else:
                    # Parser V1 - always uses iframe
                    article_frame = page.frame(name="w_metadata_doc_frame")
                    if not article_frame:
                        raise PlaywrightError(f"Could not find article frame for {article_info['url']}")
                    iframe_html = await article_frame.content()
                    soup, _, content_hash = parser_module.parse_article_page(iframe_html)

            except PlaywrightError as pe:
                self.log(f"  - SKIPPING ARTICLE due to page-level PlaywrightError: {article_info['title']} - {pe}")
                # This error is often fatal to the browser connection, so we trigger the reconnect logic.
                raise pe

            # Check for duplicate content
            if content_hash in self.scraped_content_hashes:
                self.log(f"  - Skipping duplicate content: {article_info['title']} (hash: {content_hash})")
                return
            
            if update_mode and 'content_hash' in article_info and article_info.get('content_hash') == content_hash:
                self.log(f"  - Skipping unchanged article: {article_info['title']}")
                return

            if content_hash != 0 and content_hash is not None:
                self.scraped_content_hashes.add(content_hash)
            else:
                self.log(f"  - Warning: Empty or invalid content hash for {article_info['title']}, proceeding anyway")

            filename_base = article_info.get("filename_base")
            if not filename_base:
                self.log(f"Warning: filename_base not found for {article_info['title']}. Generating fallback.")
                number = f"{i+1:03d}"
                sanitized_title = "".join([c for c in article_info['title'].lower() if c.isalnum() or c==' ']).rstrip().replace(" ", "_")
                filename_base = f"{number}_{sanitized_title[:50]}"
            
            article_info["filename_base"] = filename_base
            article_info["content_hash"] = content_hash

            file_manager.save_article_content(filename_base, formats, soup, article_info, rag_mode=rag_mode)
            self.log(f"  - Saved article: {article_info['title']} (filename: {filename_base})")
            
            if 'pdf' in formats:
                pdf_path = os.path.join(config.get_pdf_dir(), f"{filename_base}.pdf")
                await self._save_as_pdf(page, pdf_path)
                self.log(f"  - Saved PDF: {pdf_path}")
            
            await asyncio.sleep(0.5)

        except Exception as e:
            self.log(f"  - NON-FATAL WORKER-LEVEL ERROR for {article_info['title']}: {e}")
            error_str = str(e).lower()
            if "browser has been closed" in error_str or "target page, context" in error_str:
                self.log("!!! Critical browser error detected. Attempting to recover by reconnecting...")
                try:
                    await self.reconnect()
                except Exception as recon_e:
                    self.log(f"!!! RECONNECT FAILED: {recon_e}. This worker will likely fail on subsequent tasks.")
        finally:
            await self._safely_close_page(page)
            pbar.update(1) # Ensure progress bar always updates

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