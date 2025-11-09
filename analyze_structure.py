# Диагностика структуры страниц 1C ITS
# Проверяет различные типы структур для автоматического определения парсера

import asyncio
from playwright.async_api import async_playwright
import os
from dotenv import load_dotenv

load_dotenv()

async def analyze_page_structure(url):
    """Анализирует структуру страницы и определяет тип парсера"""
    
    print(f"\n{'='*80}")
    print(f"Анализ страницы: {url}")
    print(f"{'='*80}\n")
    
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp('http://localhost:3000')
        context = await browser.new_context()
        page = await context.new_page()
        
        # Авторизация
        await page.goto('https://login.1c.ru/login', timeout=60000)
        await page.fill('input[name="USER_LOGIN"]', os.getenv('LOGIN_1C_USER'))
        await page.fill('input[name="USER_PASSWORD"]', os.getenv('LOGIN_1C_PASSWORD'))
        await page.click('button[type="submit"]')
        await page.wait_for_load_state('networkidle', timeout=60000)
        
        # Переход на целевую страницу
        await page.goto(url, timeout=60000)
        await page.wait_for_load_state('networkidle', timeout=60000)
        
        # Проверяем различные элементы
        checks = {
            'w_metadata_toc': await page.query_selector('#w_metadata_toc'),
            'w_metadata_navtree': await page.query_selector('#w_metadata_navtree'),
            'w_metadata_doc_frame': await page.query_selector('#w_metadata_doc_frame'),
            'tree_class': await page.query_selector('.tree'),
            'content_class': await page.query_selector('.content'),
            'index_class': await page.query_selector('.index'),
            'doc_list': await page.query_selector('li.doc'),
            'nav_links': await page.query_selector_all('nav a'),
            'sidebar_links': await page.query_selector_all('.sidebar a, aside a'),
        }
        
        print("Найденные элементы:")
        print(f"  #w_metadata_toc: {'✓' if checks['w_metadata_toc'] else '✗'}")
        print(f"  #w_metadata_navtree: {'✓' if checks['w_metadata_navtree'] else '✗'}")
        print(f"  #w_metadata_doc_frame: {'✓' if checks['w_metadata_doc_frame'] else '✗'}")
        print(f"  .tree: {'✓' if checks['tree_class'] else '✗'}")
        print(f"  .content: {'✓' if checks['content_class'] else '✗'}")
        print(f"  .index: {'✓' if checks['index_class'] else '✗'}")
        print(f"  li.doc: {'✓' if checks['doc_list'] else '✗'}")
        print(f"  nav links: {len(checks['nav_links'])} найдено")
        print(f"  sidebar links: {len(checks['sidebar_links'])} найдено")
        
        # Извлекаем все возможные контейнеры навигации
        print("\nИзвлечение структуры навигации:")
        
        # Вариант 1: Классическое оглавление
        if checks['w_metadata_toc']:
            print("  → Тип: Classic TOC (#w_metadata_toc)")
            toc_html = await page.eval_on_selector('#w_metadata_toc', 'el => el.outerHTML')
            print(f"  → HTML длина: {len(toc_html)} символов")
            
        # Вариант 2: Дерево навигации
        if checks['w_metadata_navtree']:
            print("  → Тип: Navigation Tree (#w_metadata_navtree)")
            tree_html = await page.eval_on_selector('#w_metadata_navtree', 'el => el.outerHTML')
            print(f"  → HTML длина: {len(tree_html)} символов")
            
        # Вариант 3: Дерево с классом .tree
        if checks['tree_class']:
            print("  → Тип: Tree with class (.tree)")
            links = await page.eval_on_selector('.tree', '''el => {
                const links = Array.from(el.querySelectorAll('a'));
                return links.slice(0, 10).map(a => ({
                    text: a.textContent.trim(),
                    href: a.href
                }));
            }''')
            print(f"  → Найдено ссылок (первые 10):")
            for link in links:
                print(f"     - {link['text'][:50]}")
                
        # Вариант 4: Список индекса
        if checks['index_class']:
            print("  → Тип: Index list (.index)")
            links = await page.eval_on_selector('.index', '''el => {
                const links = Array.from(el.querySelectorAll('a'));
                return links.slice(0, 10).map(a => ({
                    text: a.textContent.trim(),
                    href: a.href
                }));
            }''')
            print(f"  → Найдено ссылок (первые 10):")
            for link in links:
                print(f"     - {link['text'][:50]}")
        
        # Проверяем JavaScript навигацию
        print("\nПроверка динамической навигации:")
        try:
            dynamic_links = await page.evaluate('''() => {
                // Ищем все возможные контейнеры
                const containers = [
                    document.querySelector('#w_metadata_toc'),
                    document.querySelector('#w_metadata_navtree'),
                    document.querySelector('.tree'),
                    document.querySelector('.navigation'),
                    document.querySelector('aside'),
                    document.querySelector('.sidebar')
                ];
                
                let allLinks = [];
                containers.forEach(container => {
                    if (container) {
                        const links = Array.from(container.querySelectorAll('a'));
                        allLinks.push(...links.map(a => ({
                            text: a.textContent.trim(),
                            href: a.href,
                            container: container.id || container.className
                        })));
                    }
                });
                
                return allLinks.slice(0, 20);
            }''')
            
            print(f"  → Всего динамических ссылок найдено (первые 20):")
            for link in dynamic_links:
                print(f"     [{link['container']}] {link['text'][:60]}")
                
        except Exception as e:
            print(f"  → Ошибка при извлечении: {e}")
        
        # Определяем рекомендуемый парсер
        print("\n" + "="*80)
        print("РЕКОМЕНДАЦИЯ:")
        if checks['w_metadata_toc']:
            print("  ✓ Использовать: parser_v1 (Classic TOC)")
        elif checks['w_metadata_navtree']:
            print("  ✓ Использовать: parser_v2 (Navigation Tree)")
        elif checks['tree_class']:
            print("  ✓ Использовать: parser_tree (Tree-based navigation)")
        elif checks['index_class']:
            print("  ✓ Использовать: parser_index (Index-based navigation)")
        else:
            print("  ⚠ Требуется создание нового парсера")
        print("="*80)
        
        await context.close()
        await browser.close()

async def main():
    urls = [
        "https://its.1c.ru/db/bsp3111doc",  # Работает
        "https://its.1c.ru/db/v8327doc",    # Не работает
        "https://its.1c.ru/section/dev/method_dev",  # Не работает
    ]
    
    for url in urls:
        await analyze_page_structure(url)
        print("\n")

if __name__ == "__main__":
    asyncio.run(main())

