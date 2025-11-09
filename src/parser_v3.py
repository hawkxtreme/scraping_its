"""
Parser V3 - Универсальный парсер на основе .tree навигации
Поддерживает v8327doc, method_dev и другие страницы с динамическим деревом
"""

from bs4 import BeautifulSoup
from . import config

def extract_toc_links(html_content):
    """
    Парсит древовидную навигацию с классом .tree
    Используется для v8327doc, method_dev и подобных
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Ищем контейнер с деревом навигации
    tree_div = soup.find(class_='tree')
    if not tree_div:
        # Пробуем альтернативные селекторы
        tree_div = soup.find('div', id='w_metadata_tree')
        if not tree_div:
            tree_div = soup.find('aside')  # Боковая панель навигации
    
    if not tree_div:
        raise ValueError("Could not find navigation tree with class 'tree' or alternatives.")

    def parse_ul(ul_element, depth=0):
        """Рекурсивно парсит UL элементы дерева"""
        children = []
        for li in ul_element.find_all('li', recursive=False):
            link = li.find('a', recursive=False)
            if link:
                href = link.get('href')
                text = link.get_text(strip=True)
                if href and text:
                    full_url = f"{config.BASE_URL}{href}" if href.startswith('/') else href
                    node = {"title": text, "url": full_url, "children": []}
                    
                    # Ищем вложенный UL
                    nested_ul = li.find('ul', recursive=False)
                    if nested_ul:
                        node["children"] = parse_ul(nested_ul, depth + 1)
                    
                    children.append(node)
        return children

    # Начинаем с первого UL в дереве
    top_ul = tree_div.find('ul')
    if not top_ul:
        # Если UL нет, пробуем собрать все ссылки напрямую
        links = tree_div.find_all('a')
        return [{"title": link.get_text(strip=True), "url": f"{config.BASE_URL}{link.get('href')}" if link.get('href', '').startswith('/') else link.get('href', ''), "children": []} 
                for link in links if link.get('href') and link.get_text(strip=True)]
    
    return parse_ul(top_ul)


def parse_article_page(html_content, url=None):
    """
    Парсит содержимое статьи
    Универсальный парсер для различных структур
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Пробуем различные контейнеры контента по приоритету
    content_div = None
    
    # Вариант 1: iframe контент
    content_div = soup.find('body')
    
    # Вариант 2: основной контент
    if not content_div or len(content_div.get_text(strip=True)) < 100:
        content_div = soup.find('div', class_='content')
    
    # Вариант 3: статья
    if not content_div:
        content_div = soup.find('article')
    
    # Вариант 4: main контент
    if not content_div:
        content_div = soup.find('main')
    
    # Вариант 5: div с ID содержащим "content"
    if not content_div:
        content_divs = soup.find_all('div', id=lambda x: x and 'content' in x.lower())
        if content_divs:
            content_div = content_divs[0]
    
    # Fallback: body без nav/header/footer
    if not content_div:
        body = soup.find('body')
        if body:
            # Удаляем навигацию и лишние элементы
            for elem in body.find_all(['nav', 'header', 'footer', 'aside']):
                elem.decompose()
            for elem in body.find_all(class_=['tree', 'navigation', 'sidebar']):
                elem.decompose()
            for script in body.find_all('script'):
                script.decompose()
            for style in body.find_all('style'):
                style.decompose()
            content_div = body
        else:
            raise ValueError("Could not find content in the page.")

    # Вычисляем hash с учетом URL
    article_text = content_div.get_text(separator='\n', strip=True)
    if article_text.strip():
        url_part = url if url else ""
        content_hash = hash(f"{url_part}|{article_text}|{len(article_text)}")
    else:
        content_hash = 0

    # Извлекаем вложенные ссылки
    nested_links = []
    for link in content_div.find_all('a'):
        href = link.get('href')
        text = link.get_text(strip=True)
        if href and text:
            # Фильтруем только ссылки на документацию
            if href.startswith('/db/') or href.startswith('/section/'):
                full_url = f"{config.BASE_URL}{href}"
                nested_links.append({"title": text, "url": full_url})
    
    return soup, nested_links, content_hash

