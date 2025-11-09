import asyncio
import os
from playwright.async_api import async_playwright, Error as PlaywrightError, Page, Browser, BrowserContext
from bs4 import BeautifulSoup
from tqdm import tqdm

# Import modularized components
from . import config
from . import parser
from . import file_manager
from .utils import retry_on_error, retry_on_timeout

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
        
        # Initialize error counter for statistics
        self.errors_count = 0
        self.warnings_count = 0

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
        self.log.debug("Browser context closed, connection remains open for other workers.")

    async def shutdown(self):
        """Fully closes all playwright resources."""
        self.log.info("Shutting down all Playwright resources...")
        try:
            if self.context:
                await self.context.close()
        except Exception as e:
            self.log.debug(f"Error closing context during shutdown: {e}")
        try:
            if self.browser and self.browser.is_connected():
                await self.browser.close()
        except Exception as e:
            self.log.debug(f"Error closing browser during shutdown: {e}")
        try:
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            self.log.debug(f"Error stopping playwright during shutdown: {e}")
        self.log.info("Playwright shutdown complete.")

    async def reconnect(self):
        """Safely closes existing connections and re-establishes a new one."""
        self.log.debug("Attempting to reconnect...")
        try:
            if self.context:
                await self.context.close()
        except Exception as e:
            self.log.debug(f"Error closing context during reconnect: {e}")
        try:
            if self.browser and self.browser.is_connected():
                await self.browser.close()
        except Exception as e:
            self.log.debug(f"Error closing browser during reconnect: {e}")
        try:
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            self.log.debug(f"Error stopping playwright during reconnect: {e}")
        
        await self.connect()
        await self.login()
        self.log.debug("Reconnect successful.")

    @retry_on_error(max_attempts=3, delay=2.0)
    async def login(self):
        """Performs login to the website with automatic retry."""
        page = None
        try:
            self.log.info("Step 3: Logging in...")
            page = await self.context.new_page()
            
            self.log.debug("Navigating to login page", url=config.LOGIN_URL)
            await page.goto(config.LOGIN_URL, timeout=config.get_network_timeout())
            await page.wait_for_load_state('networkidle', timeout=config.get_network_timeout())
            
            self.log.debug("Filling login credentials", username=config.LOGIN_1C_USER)
            await page.fill("input#username", config.LOGIN_1C_USER)
            await page.fill("input#password", config.LOGIN_1C_PASSWORD)
            
            self.log.debug("Clicking login button")
            await page.click('#loginButton')
            await page.wait_for_load_state('networkidle', timeout=config.get_network_timeout())
            
            # Check for login success by looking for the profile URL
            if page.url != "https://login.1c.ru/user/profile":
                raise PlaywrightError("Login failed, did not redirect to profile page.")
            
            self.log.info("Login successful", profile_url=page.url)
        except Exception as e:
            self.log.log_error_with_context(e, "login", url=config.LOGIN_URL)
            raise # Re-raise the exception to be caught by the main loop
        finally:
            await self._safely_close_page(page)

    @retry_on_timeout()
    async def get_initial_toc(self, url):
        """Scrapes the initial table of contents with retry on timeout."""
        page = None
        try:
            self.log.info(f"Step 4: Scraping initial table of contents from {url}...")
            page = await self.context.new_page()
            
            self.log.debug("Loading TOC page", url=url)
            await page.goto(url, timeout=config.get_page_timeout())
            await page.wait_for_load_state('networkidle', timeout=config.get_network_timeout())
            
            parser_module = parser.get_parser_for_url(url)
            self.log.debug("Extracting TOC links", parser=parser_module.__name__)
            
            # Для parser_v3 используем динамическое раскрытие дерева
            if parser_module.__name__ == 'src.parser_v3':
                initial_toc_links = await self._expand_tree_and_collect_links(page, url)
            else:
                page_content = await page.content()
                initial_toc_links = parser_module.extract_toc_links(page_content)
            
            self.log.info(f"Found {len(initial_toc_links)} initial links", count=len(initial_toc_links))

            return initial_toc_links
        except Exception as e:
            self.log.log_error_with_context(e, "get_initial_toc", url=url)
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
                await page.goto(url, timeout=config.get_page_timeout())
                await page.wait_for_load_state('networkidle', timeout=config.get_network_timeout())
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
                        self.log.debug(f"Could not parse nested links", url=url, error=str(e))
                        
            except Exception as e:
                self.log.debug(f"Could not visit URL for nested discovery", url=url, error=str(e))
            finally:
                await self._safely_close_page(page)
            
            # Process existing children
            for child in node.get("children", []):
                await process_node(child, current_depth + 1)
        
        # Process all top-level nodes
        for node in toc_tree:
            await process_node(node, 0)
            
        total_discovered = len(visited_urls)
        self.log.info(f"Discovered {total_discovered} total articles through recursive search", 
                     count=total_discovered)
        
        return toc_tree



    async def scrape_single_article(self, article_info, formats, i, pbar, update_mode=False, rag_mode=False):
        """Scrapes the final content for a single article."""
        page = None
        try:
            self.log.debug(f"Attempting to scrape article", 
                          title=article_info['title'], 
                          url=article_info['url'])
            page = await self.context.new_page()

            try:
                await page.goto(article_info['url'], timeout=config.get_page_timeout())
                await page.wait_for_load_state('networkidle', timeout=config.get_network_timeout())

                parser_module = parser.get_parser_for_url(article_info['url'])

                # For parser_v2, check if page uses iframe (like /content/XXX/hdoc pages)
                if parser_module.__name__ == 'src.parser_v2':
                    # Check if page has iframe with content
                    article_frame = page.frame(name="w_metadata_doc_frame")
                    if article_frame:
                        # Content is in iframe (like /content/ pages)
                        self.log.debug("Extracting from iframe", url=article_info['url'])
                        iframe_html = await article_frame.content()
                        soup, _, content_hash = parser_module.parse_article_page(iframe_html, article_info['url'])
                    else:
                        # Content is in main page (like /browse/ pages)
                        self.log.debug("Extracting from main page", url=article_info['url'])
                        content_html = await page.content()
                        soup, _, content_hash = parser_module.parse_article_page(content_html, article_info['url'])
                else:
                    # Parser V1 - more robust handling
                    article_frame = page.frame(name="w_metadata_doc_frame")
                    if article_frame:
                        # Content is in iframe
                        self.log.debug("Extracting from iframe", url=article_info['url'])
                        content_html = await article_frame.content()
                    else:
                        # Content is in main page
                        self.log.debug("No iframe found, extracting from main page", url=article_info['url'])
                        content_html = await page.content()
                    
                    soup, _, content_hash = parser_module.parse_article_page(content_html, article_info['url'])

            except PlaywrightError as pe:
                self.log.debug(f"Playwright error, will attempt reconnect", 
                              title=article_info['title'], 
                              error=str(pe))
                # This error is often fatal to the browser connection, so we trigger the reconnect logic.
                raise pe

            # Check for duplicate content
            if content_hash in self.scraped_content_hashes:
                self.log.debug(f"Skipping duplicate content", 
                              title=article_info['title'], 
                              hash=content_hash)
                return
            
            if update_mode and 'content_hash' in article_info and article_info.get('content_hash') == content_hash:
                self.log.debug(f"Skipping unchanged article", title=article_info['title'])
                return

            if content_hash != 0 and content_hash is not None:
                self.scraped_content_hashes.add(content_hash)
            else:
                self.log.debug(f"Empty or invalid content hash, proceeding anyway", 
                              title=article_info['title'])

            filename_base = article_info.get("filename_base")
            if not filename_base:
                self.log.debug(f"filename_base not found, generating fallback", 
                              title=article_info['title'])
                number = f"{i+1:03d}"
                sanitized_title = "".join([c for c in article_info['title'].lower() if c.isalnum() or c==' ']).rstrip().replace(" ", "_")
                filename_base = f"{number}_{sanitized_title[:50]}"
            
            article_info["filename_base"] = filename_base
            article_info["content_hash"] = content_hash

            file_manager.save_article_content(filename_base, formats, soup, article_info, rag_mode=rag_mode)
            self.log.info(f"Saved article", 
                         title=article_info['title'], 
                         filename=filename_base,
                         formats=','.join(formats))
            
            if 'pdf' in formats:
                pdf_path = os.path.join(config.get_pdf_dir(), f"{filename_base}.pdf")
                await self._save_as_pdf(page, pdf_path)
                self.log.debug(f"Saved PDF", path=pdf_path)
            
            # Use configured delay between requests
            await asyncio.sleep(config.get_request_delay())

        except Exception as e:
            self.errors_count += 1
            # Log error details only to file (debug level to avoid console spam)
            self.log.debug(f"Error during article scrape, will attempt to continue", 
                          title=article_info.get('title', 'Unknown'),
                          url=article_info.get('url', 'Unknown'),
                          error=str(e))
            error_str = str(e).lower()
            if "browser has been closed" in error_str or "target page, context" in error_str:
                self.log.debug("Browser connection lost, reconnecting...")
                try:
                    await self.reconnect()
                except Exception as recon_e:
                    self.log.error(f"Reconnect failed: {recon_e}")
                    # This is critical, let it propagate
                    raise
        finally:
            await self._safely_close_page(page)
            pbar.update(1) # Ensure progress bar always updates

    async def _safely_close_page(self, page: Page):
        """Helper function to safely close a page."""
        try:
            if page:
                await page.close()
        except Exception as e:
            self.log.debug(f"Error closing page: {e}")
    
    async def _expand_tree_and_collect_links(self, page, base_url, max_depth=4):
        """
        Динамически раскрывает дерево навигации и собирает все ссылки.
        Используется для parser_v3 (v8327doc, method_dev, metod81)
        
        Args:
            page: Playwright page объект
            base_url: Базовый URL страницы
            max_depth: Максимальная глубина рекурсии
            
        Returns:
            List[dict]: Список ссылок с заголовками
        """
        all_pages = []
        processed_urls = set()
        
        self.log.debug("Starting tree expansion", max_depth=max_depth)
        
        async def click_and_extract(current_depth=0):
            """Рекурсивно кликает на ссылки дерева и извлекает контент"""
            if current_depth >= max_depth:
                self.log.debug(f"Max depth {max_depth} reached")
                return
            
            # Получаем все ссылки в дереве навигации
            tree_links = await page.evaluate('''() => {
                const tree = document.querySelector('.tree');
                if (!tree) return [];
                
                const links = Array.from(tree.querySelectorAll('a'));
                return links.map((link, idx) => ({
                    href: link.href,
                    text: link.textContent.trim(),
                    index: idx
                }));
            }''')
            
            if not tree_links:
                self.log.debug("No tree links found")
                return
            
            self.log.debug(f"Depth {current_depth}: found {len(tree_links)} tree links")
            
            # Запоминаем обработанные на этом уровне
            links_processed_at_level = set()
            
            i = 0
            while i < len(tree_links):
                try:
                    # Перечитываем ссылки (DOM мог измениться)
                    current_tree_links = await page.evaluate('''() => {
                        const tree = document.querySelector('.tree');
                        if (!tree) return [];
                        const links = Array.from(tree.querySelectorAll('a'));
                        return links.map((link, idx) => ({
                            href: link.href,
                            text: link.textContent.trim(),
                            index: idx
                        }));
                    }''')
                    
                    if i >= len(current_tree_links):
                        break
                    
                    link_info = current_tree_links[i]
                    href = link_info['href']
                    text = link_info['text']
                    
                    # Пропускаем обработанные
                    if href in links_processed_at_level or href in processed_urls:
                        i += 1
                        continue
                    
                    links_processed_at_level.add(href)
                    
                    if not text or not href:
                        i += 1
                        continue
                    
                    self.log.debug(f"  [{current_depth}] Clicking: {text[:50]}", url=href)
                    
                    # Кликаем на ссылку в дереве
                    try:
                        await page.evaluate(f'''() => {{
                            const tree = document.querySelector('.tree');
                            if (!tree) return;
                            const links = Array.from(tree.querySelectorAll('a'));
                            if (links[{i}]) {{
                                links[{i}].scrollIntoView({{behavior: 'auto', block: 'center'}});
                                links[{i}].click();
                            }}
                        }}''')
                        
                        # Ждем немного для загрузки контента
                        await page.wait_for_timeout(500)
                        
                    except Exception as e:
                        self.log.debug(f"    -> Click error: {str(e)[:80]}")
                        i += 1
                        continue
                    
                    # Извлекаем контентные ссылки справа после клика
                    try:
                        content_links = await page.evaluate('''() => {
                            // Ищем li.doc a - специфичные элементы контента в правой панели
                            const docLinks = Array.from(document.querySelectorAll('li.doc a'));
                            return docLinks.map(link => ({
                                href: link.href,
                                text: link.textContent.trim()
                            })).filter(l => l.href && l.text);
                        }''')
                        
                        self.log.debug(f"    -> Found {len(content_links)} li.doc links in content area")
                        
                        # Добавляем найденные ссылки
                        for content_link in content_links:
                            content_url = content_link['href']
                            if content_url not in processed_urls:
                                all_pages.append({
                                    "title": content_link['text'],
                                    "url": content_url,
                                    "children": []
                                })
                                processed_urls.add(content_url)
                                self.log.debug(f"       • {content_link['text'][:60]}")
                        
                    except Exception as e:
                        self.log.debug(f"    -> Error extracting content links: {str(e)[:80]}")
                    
                    # Проверяем, появились ли новые элементы в дереве
                    try:
                        new_tree_links = await page.evaluate('''() => {
                            const tree = document.querySelector('.tree');
                            if (!tree) return [];
                            const links = Array.from(tree.querySelectorAll('a'));
                            return links.map(link => ({href: link.href, text: link.textContent.trim()}));
                        }''')
                        
                        new_count = len(new_tree_links) - len(current_tree_links)
                        
                        # Если есть новые подразделы, рекурсивно обрабатываем
                        if new_count > 0 and current_depth < max_depth - 1:
                            self.log.debug(f"    -> {new_count} new sub-sections found, going deeper...")
                            await click_and_extract(current_depth + 1)
                            
                            # После рекурсии обновляем список ссылок
                            tree_links = await page.evaluate('''() => {
                                const tree = document.querySelector('.tree');
                                if (!tree) return [];
                                const links = Array.from(tree.querySelectorAll('a'));
                                return links.map((link, idx) => ({href: link.href, text: link.textContent.trim(), index: idx}));
                            }''')
                    
                    except Exception as e:
                        self.log.debug(f"    -> Error checking new tree links: {str(e)[:80]}")
                    
                except Exception as e:
                    self.log.debug(f"  Error processing link {i}: {str(e)[:80]}")
                
                i += 1
        
        # Запускаем рекурсивное раскрытие
        await click_and_extract(current_depth=0)
        
        self.log.debug(f"Tree fully expanded. Total pages found: {len(all_pages)}")
        
        return all_pages

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
                    
                    self.log.debug("Using print-friendly URL for PDF", url=print_url)
                    print_page = await self.context.new_page()
                    await print_page.goto(print_url, timeout=config.get_page_timeout())
                    await print_page.wait_for_load_state('networkidle', timeout=config.get_network_timeout())
                    pdf_bytes = await print_page.pdf(format='A4', print_background=True)
                    with open(path, "wb") as f:
                        f.write(pdf_bytes)
                    return

            pdf_bytes = await page.pdf(format='A4', print_background=True)
            with open(path, "wb") as f:
                f.write(pdf_bytes)

        except Exception as e:
            self.errors_count += 1
            self.log.error(f"Could not save PDF", url=page.url, error=str(e))
            with open(f"{path}.error.txt", "w") as f:
                f.write(f"Failed to generate PDF due to: {e}")
        finally:
            if print_page: await print_page.close()
    
    def get_statistics(self):
        """Returns statistics about the scraping session."""
        return {
            "errors_count": self.errors_count,
            "warnings_count": self.warnings_count,
            "scraped_unique_articles": len(self.scraped_content_hashes)
        }