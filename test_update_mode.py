#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import json

# Добавляем путь к src в sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Импортируем модули напрямую
import config
import file_manager

def test_get_articles_to_scrape():
    """Тест функции get_articles_to_scrape"""
    
    # Создаем тестовые данные
    articles = [
        {"url": "https://its.1c.ru/db/cabinetdoc#bookmark:pr:art1", "title": "Статья 1"},
        {"url": "https://its.1c.ru/db/cabinetdoc#bookmark:pr:art2", "title": "Статья 2"},
        {"url": "https://its.1c.ru/db/cabinetdoc#bookmark:pr:art3", "title": "Статья 3"},
    ]
    
    existing_meta_data = [
        {"url": "https://its.1c.ru/db/cabinetdoc#bookmark:pr:art1", "title": "Статья 1", "content_hash": "12345"},
        {"url": "https://its.1c.ru/db/cabinetdoc#bookmark:pr:art2", "title": "Статья 2", "content_hash": "67890"},
    ]
    
    # Тест 1: Без режима обновления
    result = file_manager.get_articles_to_scrape(articles, existing_meta_data, update_mode=False)
    assert len(result) == 3, f"Ожидали 3 статьи, получили {len(result)}"
    print("✓ Тест 1 пройден: Без режима обновления возвращаются все статьи")
    
    # Тест 2: С режимом обновления
    result = file_manager.get_articles_to_scrape(articles, existing_meta_data, update_mode=True)
    assert len(result) == 3, f"Ожидали 3 статьи, получили {len(result)}"
    print("✓ Тест 2 пройден: С режимом обновления возвращаются все статьи для проверки")
    
    # Тест 3: Пустые существующие метаданные
    result = file_manager.get_articles_to_scrape(articles, [], update_mode=True)
    assert len(result) == 3, f"Ожидали 3 статьи, получили {len(result)}"
    print("✓ Тест 3 пройден: С пустыми метаданными возвращаются все статьи")
    
    print("\nВсе тесты для функции get_articles_to_scrape пройдены!")

def test_load_existing_meta_data():
    """Тест функции load_existing_meta_data"""
    
    # Создаем временный файл метаданных
    os.makedirs("out/test_section", exist_ok=True)
    meta_file = "out/test_section/_meta.json"
    
    test_data = [
        {"url": "https://its.1c.ru/db/test#bookmark:pr:art1", "title": "Тест 1", "content_hash": "111"},
        {"url": "https://its.1c.ru/db/test#bookmark:pr:art2", "title": "Тест 2", "content_hash": "222"},
    ]
    
    with open(meta_file, "w", encoding="utf-8") as f:
        json.dump(test_data, f, ensure_ascii=False, indent=2)
    
    # Устанавливаем выходную директорию для теста
    import config
    config.set_output_dir("test_section")
    
    # Тестируем загрузку метаданных
    result = file_manager.load_existing_meta_data()
    assert len(result) == 2, f"Ожидали 2 записи, получили {len(result)}"
    assert result[0]["url"] == test_data[0]["url"], "URL первой записи не совпадает"
    assert result[1]["content_hash"] == test_data[1]["content_hash"], "Хэш второй записи не совпадает"
    
    print("✓ Тест для функции load_existing_meta_data пройден!")
    
    # Очистка
    import shutil
    shutil.rmtree("out/test_section")

if __name__ == "__main__":
    print("Запуск тестов для режима обновления...\n")
    
    test_get_articles_to_scrape()
    print()
    test_load_existing_meta_data()
    
    print("\n✅ Все тесты успешно пройдены!")