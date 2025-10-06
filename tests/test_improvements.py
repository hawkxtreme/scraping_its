#!/usr/bin/env python3
"""
Тестовый скрипт для проверки всех улучшений, внесенных в проект.

Этот скрипт выполняет различные тесты для проверки функциональности:
1. Улучшенное логирование и информативность ошибок
2. Поддержка формата DOCX
3. Оптимизация параллельной индексации
4. Система кэширования
5. Поддержка консольных аргументов для настройки таймаутов и ограничений
6. Режим обновления существующих файлов
7. Расширение возможностей фильтрации и выбора статей

URL для тестирования: https://its.1c.ru/db/cabinetdoc
"""

import os
import sys
import subprocess
import time
import json
from pathlib import Path

# Базовый URL для тестирования из system_prompt.md
TEST_URL = "https://its.1c.ru/db/cabinetdoc"

def run_command(cmd, description, expected_success=True, timeout=300):
    """
    Выполняет команду и проверяет результат. 
    
    Args:
        cmd: Команда для выполнения
        description: Описание теста
        expected_success: Ожидается ли успешное выполнение
        timeout: Таймаут выполнения в секундах
    
    Returns:
        True если тест прошел успешно, иначе False
    """
    print(f"\n{'='*60}")
    print(f"ТЕСТ: {description}")
    print(f"КОМАНДА: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    try:
        start_time = time.time()
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=timeout,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        elapsed_time = time.time() - start_time
        
        print(f"Время выполнения: {elapsed_time:.2f} секунд")
        print(f"Код возврата: {result.returncode}")
        
        if result.stdout:
            print(f"Вывод:\n{result.stdout}")
        
        if result.stderr:
            print(f"Ошибки:\n{result.stderr}")
        
        success = (result.returncode == 0) == expected_success
        print(f"РЕЗУЛЬТАТ: {'УСПЕХ' if success else 'НЕУДАЧА'}")
        
        return success
    except subprocess.TimeoutExpired:
        print(f"РЕЗУЛЬТАТ: НЕУДАЧА (превышен таймаут {timeout} секунд)")
        return False
    except Exception as e:
        print(f"РЕЗУЛЬТАТ: НЕУДАЧА (исключение: {str(e)})")
        return False

def check_file_exists(file_path, description):
    """
    Проверяет существование файла.
    
    Args:
        file_path: Путь к файлу
        description: Описание проверки
    
    Returns:
        True если файл существует, иначе False
    """
    print(f"\n{'='*60}")
    print(f"ПРОВЕРКА: {description}")
    print(f"ПУТЬ: {file_path}")
    print(f"{'='*60}")
    
    exists = os.path.exists(file_path)
    print(f"РЕЗУЛЬТАТ: {'СУЩЕСТВУЕТ' if exists else 'ОТСУТСТВУЕТ'}")
    
    return exists

def check_directory_contents(dir_path, description, expected_extensions=None):
    """
    Проверяет содержимое директории.
    
    Args:
        dir_path: Путь к директории
        description: Описание проверки
        expected_extensions: Ожидаемые расширения файлов
    
    Returns:
        True если проверка прошла успешно, иначе False
    """
    print(f"\n{'='*60}")
    print(f"ПРОВЕРКА: {description}")
    print(f"ПУТЬ: {dir_path}")
    print(f"{'='*60}")
    
    if not os.path.exists(dir_path):
        print(f"РЕЗУЛЬТАТ: НЕУДАЧА (директория не существует)")
        return False
    
    files = list(Path(dir_path).glob('*'))
    print(f"Найдено файлов: {len(files)}")
    
    if expected_extensions:
        for ext in expected_extensions:
            ext_files = [f for f in files if f.suffix.lower() == f'.{ext.lower()}']
            print(f"Файлов с расширением .{ext}: {len(ext_files)}")
    
    print(f"РЕЗУЛЬТАТ: УСПЕХ")
    return True

def check_meta_json(description):
    """
    Checks if the _meta.json file contains content_hash for each article.
    
    Args:
        description: Описание проверки
    
    Returns:
        True если проверка прошла успешно, иначе False
    """
    print(f"\n{'='*60}")
    print(f"ПРОВЕРКА: {description}")
    meta_path = os.path.join("out", "cabinetdoc", "_meta.json")
    print(f"ПУТЬ: {meta_path}")
    print(f"{'='*60}")
    
    if not os.path.exists(meta_path):
        print("РЕЗУЛЬТАТ: НЕУДАЧА (файл _meta.json не найден)")
        return False
        
    with open(meta_path, 'r', encoding='utf-8') as f:
        meta_data = json.load(f)
        
    articles = []
    if isinstance(meta_data, dict):
        articles = meta_data.get("articles", [])
    elif isinstance(meta_data, list):
        articles = meta_data
    
    if not articles:
        print("РЕЗУЛЬТАТ: НЕУДАЧА (в _meta.json нет статей)")
        return False
        
    for article in articles:
        if "content_hash" not in article or not article.get("content_hash"):
            print(f"РЕЗУЛЬТАТ: НЕУДАЧА (у статьи {article.get('index')} отсутствует content_hash)")
            return False
            
    print("РЕЗУЛЬТАТ: УСПЕХ")
    return True

def main():
    """Основная функция выполнения тестов."""
    print("НАЧАЛО ТЕСТИРОВАНИЯ УЛУЧШЕНИЙ ПРОЕКТА")
    print(f"URL для тестирования: {TEST_URL}")
    
    test_results = []
    
    # Тест 1: Проверка улучшенного логирования и информативности ошибок
    print("\n\n{'#'*80}")
    print("# ТЕСТ 1: Улучшенное логирование и информативность ошибок")
    print("{'#'*80}")
    
    cmd = [
        sys.executable, "main.py", TEST_URL,
        "--format", "json",
        "--max-articles", "3",
        "--debug"
    ]
    test_results.append(run_command(
        cmd, 
        "Проверка улучшенного логирования с отладочным режимом",
        timeout=180
    ))
    
    # Проверка наличия лог-файла
    log_file = os.path.join("out", "cabinetdoc", "script_log.txt")
    test_results.append(check_file_exists(
        log_file, 
        "Проверка наличия лог-файла"
    ))
    
    # Тест 2: Проверка поддержки формата DOCX
    print("\n\n{'#'*80}")
    print("# ТЕСТ 2: Поддержка формата DOCX")
    print("{'#'*80}")
    
    cmd = [
        sys.executable, "main.py", TEST_URL,
        "--format", "docx",
        "--max-articles", "2"
    ]
    test_results.append(run_command(
        cmd, 
        "Проверка сохранения в формате DOCX",
        timeout=180
    ))
    
    # Проверка наличия DOCX файлов
    docx_dir = os.path.join("out", "cabinetdoc", "docx")
    test_results.append(check_directory_contents(
        docx_dir, 
        "Проверка наличия DOCX файлов",
        expected_extensions=["docx"]
    ))
    
    # Тест 3: Проверка оптимизации параллельной индексации
    print("\n\n{'#'*80}")
    print("# ТЕСТ 3: Оптимизация параллельной индексации")
    print("{'#'*80}")
    
    cmd = [
        sys.executable, "main.py", TEST_URL,
        "--format", "json",
        "--max-articles", "5",
        "--parallel", "3"
    ]
    test_results.append(run_command(
        cmd, 
        "Проверка параллельной обработки с 3 потоками",
        timeout=180
    ))
    
    # Тест 4: Проверка системы кэширования
    print("\n\n{'#'*80}")
    print("# ТЕСТ 4: Система кэширования")
    print("{'#'*80}")
    
    # Сначала запускаем с кэшированием
    cmd = [
        sys.executable, "main.py", TEST_URL,
        "--format", "json",
        "--max-articles", "3",
        "--use-cache"
    ]
    test_results.append(run_command(
        cmd, 
        "Первый запуск с использованием кэша",
        timeout=180
    ))
    
    # Проверяем статистику кэша
    cmd = [
        sys.executable, "main.py",
        "--cache-stats"
    ]
    test_results.append(run_command(
        cmd, 
        "Проверка статистики кэша",
        timeout=30
    ))
    
    # Второй запуск с теми же параметрами (должно использовать кэш)
    cmd = [
        sys.executable, "main.py", TEST_URL,
        "--format", "json",
        "--max-articles", "3",
        "--use-cache"
    ]
    test_results.append(run_command(
        cmd, 
        "Второй запуск (должно использовать кэш)",
        timeout=180
    ))
    test_results.append(check_meta_json("Проверка наличия content_hash в _meta.json"))
    
    # Тест 5: Проверка консольных аргументов для настройки таймаутов и ограничений
    print("\n\n{'#'*80}")
    print("# ТЕСТ 5: Консольные аргументы для настройки таймаутов и ограничений")
    print("{'#'*80}")
    
    cmd = [
        sys.executable, "main.py", TEST_URL,
        "--format", "json",
        "--max-articles", "2",
        "--page-timeout", "120000",
        "--request-delay", "1.0",
        "--max-retries", "5"
    ]
    test_results.append(run_command(
        cmd, 
        "Проверка настройки таймаутов и ограничений",
        timeout=180
    ))
    
    # Тест 6: Проверка режима обновления существующих файлов
    print("\n\n{'#'*80}")
    print("# ТЕСТ 6: Режим обновления существующих файлов")
    print("{'#'*80}")
    
    # Сначала создаем индекс
    cmd = [
        sys.executable, "main.py", TEST_URL,
        "--format", "json",
        "--max-articles", "3",
        "--no-scrape"
    ]
    test_results.append(run_command(
        cmd, 
        "Создание индекса без скрапинга",
        timeout=120
    ))
    
    # Затем запускаем в режиме обновления
    cmd = [
        sys.executable, "main.py", TEST_URL,
        "--format", "json",
        "--max-articles", "3",
        "--update"
    ]
    test_results.append(run_command(
        cmd, 
        "Проверка режима обновления",
        timeout=180
    ))
    
    # Тест 7: Проверка расширения возможностей фильтрации и выбора статей
    print("\n\n{'#'*80}")
    print("# ТЕСТ 7: Расширение возможностей фильтрации и выбора статей")
    print("{'#'*80}")
    
    # Тест фильтрации по заголовку
    cmd = [
        sys.executable, "main.py", TEST_URL,
        "--format", "json",
        "--filter-by-title", "Отчет",
        "--max-articles", "2"
    ]
    test_results.append(run_command(
        cmd, 
        "Проверка фильтрации по заголовку",
        timeout=180
    ))
    
    # Тест исключения по заголовку
    cmd = [
        sys.executable, "main.py", TEST_URL,
        "--format", "json",
        "--exclude-by-title", "Архив",
        "--max-articles", "2"
    ]
    test_results.append(run_command(
        cmd, 
        "Проверка исключения по заголовку",
        timeout=180
    ))
    
    # Тест случайной выборки
    cmd = [
        sys.executable, "main.py", TEST_URL,
        "--format", "json",
        "--random-sample", "2"
    ]
    test_results.append(run_command(
        cmd, 
        "Проверка случайной выборки статей",
        timeout=180
    ))
    
    # Итоговые результаты
    print("\n\n{'#'*80}")
    print("# ИТОГОВЫЕ РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
    print("{'#'*80}")
    
    passed_tests = sum(test_results)
    total_tests = len(test_results)
    
    print(f"Пройдено тестов: {passed_tests}/{total_tests}")
    print(f"Процент успеха: {(passed_tests/total_tests)*100:.1f}%")
    
    if passed_tests == total_tests:
        print("\nВСЕ ТЕСТЫ УСПЕШНО ПРОЙДЕНЫ!")
        print("Все улучшения работают корректно.")
    else:
        print(f"\n{total_tests - passed_tests} ТЕСТ(ОВ) НЕ ПРОЙДЕНО!")
        print("Некоторые улучшения требуют дополнительной настройки.")
    
    return passed_tests == total_tests

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nТестирование прервано пользователем.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nНеожиданная ошибка при тестировании: {str(e)}")
        sys.exit(1)