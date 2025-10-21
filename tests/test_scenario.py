import pytest
import asyncio
import os
import shutil
import json
from unittest.mock import patch
import main as main_app
from src import config

# Определяем базовую выходную директорию для тестов
TEST_BASE_DIR = os.path.join(os.path.dirname(__file__), '..', 'out_test')

@pytest.fixture(scope="module")
def event_loop():
    """Overrides pytest-asyncio's event_loop fixture to be module-scoped."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(autouse=True)
def test_output_dir_fixture(monkeypatch):
    """
    Фикстура для создания, очистки и перенаправления вывода в тестовую директорию.
    """
    # Очищаем и создаем базовую тестовую директорию перед запуском
    if os.path.exists(TEST_BASE_DIR):
        shutil.rmtree(TEST_BASE_DIR)
    os.makedirs(TEST_BASE_DIR)

    # Эта переменная будет содержать полный путь к динамической директории теста, например, /path/to/out_test/cabinetdoc
    dynamic_test_dir = None

    def mock_set_output_dir(name):
        nonlocal dynamic_test_dir
        dynamic_test_dir = os.path.join(TEST_BASE_DIR, name)
        # В реальном приложении здесь создается директория, но в нашем случае
        # file_manager.setup_output_directories() позаботится об этом.

    def mock_get_output_dir():
        nonlocal dynamic_test_dir
        # Эта функция будет возвращать полный путь, установленный в mock_set_output_dir
        if dynamic_test_dir:
            return dynamic_test_dir
        return TEST_BASE_DIR

    monkeypatch.setattr(config, 'set_output_dir', mock_set_output_dir)
    monkeypatch.setattr(config, 'get_output_dir', mock_get_output_dir)

    yield

    # Очистка после выполнения теста (можно закомментировать для отладки)
    # if os.path.exists(TEST_BASE_DIR):
    #     shutil.rmtree(TEST_BASE_DIR)


@pytest.mark.scenario
@pytest.mark.asyncio
async def test_cabinetdoc_scenario_all_formats():
    """
    Сценарный тест для URL https://its.1c.ru/db/cabinetdoc/ для всех форматов.
    Ожидается, что для каждого формата будет создано 9 файлов.
    """
    url = "https://its.1c.ru/db/cabinetdoc/"
    formats = ["markdown", "json", "pdf", "txt"]
    expected_files = 9 # Скорректировано на основе лога
    result_dir_name = "cabinetdoc"

    # Имитируем аргументы командной строки
    test_args = ["main.py", url, "--format"] + formats
    
    with patch('sys.argv', test_args):
        await main_app.main()

    # --- Проверяем результат для каждого формата ---
    base_result_path = os.path.join(TEST_BASE_DIR, result_dir_name)

    # Выводим лог-файл для отладки
    log_file_path = os.path.join(base_result_path, 'script_log.txt')
    if os.path.exists(log_file_path):
        with open(log_file_path, 'r', encoding='utf-8') as f:
            print("--- SCRAPING LOG ---")
            print(f.read())
            print("--- END LOG ---")

    for fmt in formats:
        format_output_path = os.path.join(base_result_path, fmt)
        print(f"\n--- Checking path: {format_output_path} ---")
        
        assert os.path.exists(format_output_path), f"Директория для формата {fmt} не была создана: {format_output_path}"
        
        dir_contents = os.listdir(format_output_path)
        print(f"Contents of '{fmt}' dir: {dir_contents}")

        files = [f for f in dir_contents if f.endswith(f'.{fmt}') or (fmt == 'markdown' and f.endswith('.md'))]
        print(f"Number of files found for format '{fmt}': {len(files)}")
        
        assert len(files) == expected_files, \
            f"Ожидалось {expected_files} файлов для формата {fmt}, но найдено {len(files)}"

    # Проверяем наличие _toc.md и _meta.json
    print(f"\n--- Checking for _toc.md and _meta.json in {base_result_path} ---")
    assert os.path.exists(os.path.join(base_result_path, "_toc.md")), "Файл _toc.md не был создан"
    assert os.path.exists(os.path.join(base_result_path, "_meta.json")), "Файл _meta.json не был создан"
    print("All checks passed!")


@pytest.mark.scenario
@pytest.mark.asyncio
async def test_cabinetdoc_scenario_limit():
    """
    Сценарный тест для URL https://its.1c.ru/db/cabinetdoc/ с ограничением количества статей.
    """
    url = "https://its.1c.ru/db/cabinetdoc/"
    formats = ["json"]
    limit = 3
    result_dir_name = "cabinetdoc"

    # Имитируем аргументы командной строки
    test_args = ["main.py", url, "--format"] + formats + ["--limit", str(limit)]
    
    with patch('sys.argv', test_args):
        await main_app.main()

    # --- Проверяем результат ---
    base_result_path = os.path.join(TEST_BASE_DIR, result_dir_name)

    # Выводим лог-файл для отладки
    log_file_path = os.path.join(base_result_path, 'script_log.txt')
    if os.path.exists(log_file_path):
        with open(log_file_path, 'r', encoding='utf-8') as f:
            print("--- SCRAPING LOG ---")
            print(f.read())
            print("--- END LOG ---")

    format_output_path = os.path.join(base_result_path, formats[0])
    print(f"\n--- Checking path: {format_output_path} ---")
    
    assert os.path.exists(format_output_path), f"Директория для формата {formats[0]} не была создана: {format_output_path}"
    
    dir_contents = os.listdir(format_output_path)
    print(f"Contents of '{formats[0]}' dir: {dir_contents}")

    files = [f for f in dir_contents if f.endswith(f'.{formats[0]}') or (formats[0] == 'markdown' and f.endswith('.md'))]
    print(f"Number of files found for format '{formats[0]}': {len(files)}")
    
    assert len(files) == limit, \
        f"Ожидалось {limit} файлов для формата {formats[0]}, но найдено {len(files)}"

    print("Limit test passed!")


@pytest.mark.scenario
@pytest.mark.asyncio
async def test_cabinetdoc_scenario_rag_mode():
    """
    Сценарный тест для URL https://its.1c.ru/db/cabinetdoc/ с RAG-режимом.
    """
    url = "https://its.1c.ru/db/cabinetdoc/"
    formats = ["markdown"]
    limit = 2
    result_dir_name = "cabinetdoc"

    # Имитируем аргументы командной строки
    test_args = ["main.py", url, "--format"] + formats + ["--rag", "--limit", str(limit)]
    
    with patch('sys.argv', test_args):
        await main_app.main()

    # --- Проверяем результат ---
    base_result_path = os.path.join(TEST_BASE_DIR, result_dir_name)

    # Выводим лог-файл для отладки
    log_file_path = os.path.join(base_result_path, 'script_log.txt')
    if os.path.exists(log_file_path):
        with open(log_file_path, 'r', encoding='utf-8') as f:
            print("--- SCRAPING LOG ---")
            print(f.read())
            print("--- END LOG ---")

    format_output_path = os.path.join(base_result_path, formats[0])
    print(f"\n--- Checking path: {format_output_path} ---")
    
    assert os.path.exists(format_output_path), f"Директория для формата {formats[0]} не была создана: {format_output_path}"
    
    dir_contents = os.listdir(format_output_path)
    print(f"Contents of '{formats[0]}' dir: {dir_contents}")

    files = [f for f in dir_contents if f.endswith(f'.{formats[0]}') or (formats[0] == 'markdown' and f.endswith('.md'))]
    print(f"Number of files found for format '{formats[0]}': {len(files)}")
    
    assert len(files) == limit, \
        f"Ожидалось {limit} файлов для формата {formats[0]}, но найдено {len(files)}"

    # Проверяем наличие YAML frontmatter в markdown файлах
    for file_name in files:
        file_path = os.path.join(format_output_path, file_name)
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # Проверяем наличие YAML frontmatter
            assert content.startswith('---'), f"Файл {file_name} не начинается с YAML frontmatter"
            assert 'breadcrumb:' in content, f"Файл {file_name} не содержит breadcrumb"
            assert 'title:' in content, f"Файл {file_name} не содержит title"
            assert 'url:' in content, f"Файл {file_name} не содержит url"

    print("RAG mode test passed!")


@pytest.mark.scenario
@pytest.mark.asyncio
async def test_cabinetdoc_scenario_no_scrape():
    """
    Сценарный тест для URL https://its.1c.ru/db/cabinetdoc/ с флагом --no-scrape.
    """
    url = "https://its.1c.ru/db/cabinetdoc/"
    result_dir_name = "cabinetdoc"

    # Имитируем аргументы командной строки
    test_args = ["main.py", url, "--no-scrape"]
    
    with patch('sys.argv', test_args):
        await main_app.main()

    # --- Проверяем результат ---
    base_result_path = os.path.join(TEST_BASE_DIR, result_dir_name)

    # Выводим лог-файл для отладки
    log_file_path = os.path.join(base_result_path, 'script_log.txt')
    if os.path.exists(log_file_path):
        with open(log_file_path, 'r', encoding='utf-8') as f:
            print("--- SCRAPING LOG ---")
            print(f.read())
            print("--- END LOG ---")

    # Проверяем, что создана базовая директория
    assert os.path.exists(base_result_path), f"Базовая директория не была создана: {base_result_path}"
    
    # Выводим содержимое директории для отладки
    print(f"\n--- Contents of {base_result_path} ---")
    if os.path.exists(base_result_path):
        dir_contents = os.listdir(base_result_path)
        print(f"Contents: {dir_contents}")
    
    # В режиме --no-scrape создаются директории для форматов, но они должны быть пустыми
    for fmt in ["json", "pdf", "txt", "markdown"]:
        format_path = os.path.join(base_result_path, fmt)
        if os.path.exists(format_path):
            # Если директория существует, она должна быть пустой
            format_contents = os.listdir(format_path)
            assert len(format_contents) == 0, f"Директория для формата {fmt} не должна содержать файлы в режиме --no-scrape"

    print("No-scrape test passed!")


@pytest.mark.scenario
@pytest.mark.asyncio
async def test_v8std_scenario_parser_v2():
    """
    Сценарный тест для URL https://its.1c.ru/db/v8std/ с использованием parser_v2.
    """
    url = "https://its.1c.ru/db/v8std/"
    formats = ["json"]
    limit = 5
    result_dir_name = "v8std"

    # Имитируем аргументы командной строки
    test_args = ["main.py", url, "--format"] + formats + ["--limit", str(limit)]
    
    with patch('sys.argv', test_args):
        await main_app.main()

    # --- Проверяем результат ---
    base_result_path = os.path.join(TEST_BASE_DIR, result_dir_name)

    # Выводим лог-файл для отладки
    log_file_path = os.path.join(base_result_path, 'script_log.txt')
    if os.path.exists(log_file_path):
        with open(log_file_path, 'r', encoding='utf-8') as f:
            print("--- SCRAPING LOG ---")
            print(f.read())
            print("--- END LOG ---")

    format_output_path = os.path.join(base_result_path, formats[0])
    print(f"\n--- Checking path: {format_output_path} ---")
    
    assert os.path.exists(format_output_path), f"Директория для формата {formats[0]} не была создана: {format_output_path}"
    
    dir_contents = os.listdir(format_output_path)
    print(f"Contents of '{formats[0]}' dir: {dir_contents}")

    files = [f for f in dir_contents if f.endswith(f'.{formats[0]}') or (formats[0] == 'markdown' and f.endswith('.md'))]
    print(f"Number of files found for format '{formats[0]}': {len(files)}")
    
    assert len(files) == limit, \
        f"Ожидалось {limit} файлов для формата {formats[0]}, но найдено {len(files)}"

    # Проверяем наличие _toc.md и _meta.json
    print(f"\n--- Checking for _toc.md and _meta.json in {base_result_path} ---")
    assert os.path.exists(os.path.join(base_result_path, "_toc.md")), "Файл _toc.md не был создан"
    assert os.path.exists(os.path.join(base_result_path, "_meta.json")), "Файл _meta.json не был создан"

    print("Parser V2 test passed!")


@pytest.mark.scenario
@pytest.mark.asyncio
async def test_cabinetdoc_scenario_parallel():
    """
    Сценарный тест для URL https://its.1c.ru/db/cabinetdoc/ с параллельной обработкой.
    """
    url = "https://its.1c.ru/db/cabinetdoc/"
    formats = ["json"]
    limit = 3
    parallel = 2
    result_dir_name = "cabinetdoc"

    # Имитируем аргументы командной строки
    test_args = ["main.py", url, "--format"] + formats + ["--limit", str(limit), "--parallel", str(parallel)]
    
    with patch('sys.argv', test_args):
        await main_app.main()

    # --- Проверяем результат ---
    base_result_path = os.path.join(TEST_BASE_DIR, result_dir_name)

    # Выводим лог-файл для отладки
    log_file_path = os.path.join(base_result_path, 'script_log.txt')
    if os.path.exists(log_file_path):
        with open(log_file_path, 'r', encoding='utf-8') as f:
            print("--- SCRAPING LOG ---")
            print(f.read())
            print("--- END LOG ---")

    format_output_path = os.path.join(base_result_path, formats[0])
    print(f"\n--- Checking path: {format_output_path} ---")
    
    assert os.path.exists(format_output_path), f"Директория для формата {formats[0]} не была создана: {format_output_path}"
    
    dir_contents = os.listdir(format_output_path)
    print(f"Contents of '{formats[0]}' dir: {dir_contents}")

    files = [f for f in dir_contents if f.endswith(f'.{formats[0]}') or (formats[0] == 'markdown' and f.endswith('.md'))]
    print(f"Number of files found for format '{formats[0]}': {len(files)}")
    
    assert len(files) == limit, \
        f"Ожидалось {limit} файлов для формата {formats[0]}, но найдено {len(files)}"

    print("Parallel processing test passed!")


@pytest.mark.scenario
@pytest.mark.asyncio
async def test_cabinetdoc_scenario_update_mode():
    """
    Сценарный тест для URL https://its.1c.ru/db/cabinetdoc/ с режимом обновления.
    """
    url = "https://its.1c.ru/db/cabinetdoc/"
    formats = ["json"]
    limit = 2
    result_dir_name = "cabinetdoc"

    # Первый запуск - создаем файлы
    test_args = ["main.py", url, "--format"] + formats + ["--limit", str(limit)]
    
    with patch('sys.argv', test_args):
        await main_app.main()

    # Проверяем, что файлы созданы
    base_result_path = os.path.join(TEST_BASE_DIR, result_dir_name)
    format_output_path = os.path.join(base_result_path, formats[0])
    
    assert os.path.exists(format_output_path), f"Директория для формата {formats[0]} не была создана: {format_output_path}"
    
    dir_contents = os.listdir(format_output_path)
    files = [f for f in dir_contents if f.endswith(f'.{formats[0]}')]
    initial_file_count = len(files)
    
    print(f"Initial run created {initial_file_count} files")

    # Второй запуск с режимом обновления
    test_args = ["main.py", url, "--format"] + formats + ["--limit", str(limit), "--update"]
    
    with patch('sys.argv', test_args):
        await main_app.main()

    # Проверяем, что файлы не были пересозданы (режим обновления)
    dir_contents_after = os.listdir(format_output_path)
    files_after = [f for f in dir_contents_after if f.endswith(f'.{formats[0]}') or (formats[0] == 'markdown' and f.endswith('.md'))]
    final_file_count = len(files_after)
    
    print(f"Update run resulted in {final_file_count} files")
    
    # Количество файлов должно остаться тем же
    assert final_file_count == initial_file_count, \
        f"Количество файлов изменилось после обновления: было {initial_file_count}, стало {final_file_count}"

    print("Update mode test passed!")


@pytest.mark.scenario
@pytest.mark.asyncio
async def test_cabinetdoc_scenario_force_reindex():
    """
    Сценарный тест для URL https://its.1c.ru/db/cabinetdoc/ с принудительным переиндексированием.
    """
    url = "https://its.1c.ru/db/cabinetdoc/"
    formats = ["json"]
    limit = 2
    result_dir_name = "cabinetdoc"

    # Первый запуск - создаем индекс
    test_args = ["main.py", url, "--format"] + formats + ["--limit", str(limit)]
    
    with patch('sys.argv', test_args):
        await main_app.main()

    # Проверяем, что файлы созданы
    base_result_path = os.path.join(TEST_BASE_DIR, result_dir_name)
    format_output_path = os.path.join(base_result_path, formats[0])
    
    assert os.path.exists(format_output_path), f"Директория для формата {formats[0]} не была создана: {format_output_path}"
    
    dir_contents = os.listdir(format_output_path)
    files = [f for f in dir_contents if f.endswith(f'.{formats[0]}') or (formats[0] == 'markdown' and f.endswith('.md'))]
    initial_file_count = len(files)
    
    print(f"Initial run created {initial_file_count} files")

    # Второй запуск с флагом принудительного переиндексирования
    test_args = ["main.py", url, "--format"] + formats + ["--limit", str(limit), "--force-reindex"]
    
    with patch('sys.argv', test_args):
        await main_app.main()

    # Проверяем, что файлы были пересозданы
    dir_contents_after = os.listdir(format_output_path)
    files_after = [f for f in dir_contents_after if f.endswith(f'.{formats[0]}')]
    final_file_count = len(files_after)
    
    print(f"Force reindex run resulted in {final_file_count} files")
    
    # Количество файлов должно остаться тем же
    assert final_file_count == initial_file_count, \
        f"Количество файлов изменилось после принудительного переиндексирования: было {initial_file_count}, стало {final_file_count}"

    print("Force reindex test passed!")


@pytest.mark.scenario
@pytest.mark.asyncio
async def test_cabinetdoc_scenario_single_format():
    """
    Сценарный тест для URL https://its.1c.ru/db/cabinetdoc/ с одним форматом вывода (PDF).
    """
    url = "https://its.1c.ru/db/cabinetdoc/"
    formats = ["pdf"]
    limit = 2
    result_dir_name = "cabinetdoc"

    # Имитируем аргументы командной строки
    test_args = ["main.py", url, "--format"] + formats + ["--limit", str(limit)]
    
    with patch('sys.argv', test_args):
        await main_app.main()

    # --- Проверяем результат ---
    base_result_path = os.path.join(TEST_BASE_DIR, result_dir_name)

    # Выводим лог-файл для отладки
    log_file_path = os.path.join(base_result_path, 'script_log.txt')
    if os.path.exists(log_file_path):
        with open(log_file_path, 'r', encoding='utf-8') as f:
            print("--- SCRAPING LOG ---")
            print(f.read())
            print("--- END LOG ---")

    format_output_path = os.path.join(base_result_path, formats[0])
    print(f"\n--- Checking path: {format_output_path} ---")
    
    assert os.path.exists(format_output_path), f"Директория для формата {formats[0]} не была создана: {format_output_path}"
    
    dir_contents = os.listdir(format_output_path)
    print(f"Contents of '{formats[0]}' dir: {dir_contents}")

    files = [f for f in dir_contents if f.endswith(f'.{formats[0]}')]
    print(f"Number of files found for format '{formats[0]}': {len(files)}")
    
    assert len(files) == limit, \
        f"Ожидалось {limit} файлов для формата {formats[0]}, но найдено {len(files)}"

    # Проверяем, что другие форматы не созданы
    for other_format in ["json", "txt", "markdown"]:
        other_format_path = os.path.join(base_result_path, other_format)
        assert not os.path.exists(other_format_path), f"Директория для формата {other_format} не должна была быть создана"

    print("Single format test passed!")


@pytest.mark.scenario
@pytest.mark.asyncio
async def test_cabinetdoc_scenario_multiple_formats():
    """
    Сценарный тест для URL https://its.1c.ru/db/cabinetdoc/ с множественными форматами вывода.
    """
    url = "https://its.1c.ru/db/cabinetdoc/"
    formats = ["json", "txt", "markdown"]
    limit = 2
    result_dir_name = "cabinetdoc"

    # Имитируем аргументы командной строки
    test_args = ["main.py", url, "--format"] + formats + ["--limit", str(limit)]
    
    with patch('sys.argv', test_args):
        await main_app.main()

    # --- Проверяем результат ---
    base_result_path = os.path.join(TEST_BASE_DIR, result_dir_name)

    # Выводим лог-файл для отладки
    log_file_path = os.path.join(base_result_path, 'script_log.txt')
    if os.path.exists(log_file_path):
        with open(log_file_path, 'r', encoding='utf-8') as f:
            print("--- SCRAPING LOG ---")
            print(f.read())
            print("--- END LOG ---")

    # Проверяем каждый формат
    for fmt in formats:
        format_output_path = os.path.join(base_result_path, fmt)
        print(f"\n--- Checking path: {format_output_path} ---")
        
        assert os.path.exists(format_output_path), f"Директория для формата {fmt} не была создана: {format_output_path}"
        
        dir_contents = os.listdir(format_output_path)
        print(f"Contents of '{fmt}' dir: {dir_contents}")

        files = [f for f in dir_contents if f.endswith(f'.{fmt}') or (fmt == 'markdown' and f.endswith('.md'))]
        print(f"Number of files found for format '{fmt}': {len(files)}")
        
        assert len(files) == limit, \
            f"Ожидалось {limit} файлов для формата {fmt}, но найдено {len(files)}"

    # Проверяем, что формат PDF не создан
    pdf_format_path = os.path.join(base_result_path, "pdf")
    assert not os.path.exists(pdf_format_path), f"Директория для формата pdf не должна была быть создана"

    print("Multiple formats test passed!")


@pytest.mark.scenario
@pytest.mark.asyncio
async def test_cabinetdoc_scenario_metadata_validation():
    """
    Сценарный тест для проверки корректности метаданных в файлах.
    """
    url = "https://its.1c.ru/db/cabinetdoc/"
    formats = ["json", "markdown"]
    limit = 1
    result_dir_name = "cabinetdoc"

    # Имитируем аргументы командной строки
    test_args = ["main.py", url, "--format"] + formats + ["--limit", str(limit), "--rag"]
    
    with patch('sys.argv', test_args):
        await main_app.main()

    # --- Проверяем результат ---
    base_result_path = os.path.join(TEST_BASE_DIR, result_dir_name)

    # Проверяем JSON файл
    json_path = os.path.join(base_result_path, "json")
    json_files = [f for f in os.listdir(json_path) if f.endswith('.json')]
    assert len(json_files) == 1, f"Ожидался 1 JSON файл, найдено {len(json_files)}"
    
    with open(os.path.join(json_path, json_files[0]), 'r', encoding='utf-8') as f:
        json_data = json.load(f)
        assert 'url' in json_data, "JSON файл не содержит поле 'url'"
        assert 'title' in json_data, "JSON файл не содержит поле 'title'"
        assert 'content' in json_data, "JSON файл не содержит поле 'content'"
        # Проверяем, что URL соответствует ожидаемому (без учета завершающего слеша)
        assert json_data['url'] == url or json_data['url'].startswith(url.rstrip('/')), f"URL в JSON не соответствует ожидаемому: {json_data['url']}"

    # Проверяем Markdown файл с RAG метаданными
    md_path = os.path.join(base_result_path, "markdown")
    md_files = [f for f in os.listdir(md_path) if f.endswith('.md')]
    assert len(md_files) == 1, f"Ожидался 1 Markdown файл, найдено {len(md_files)}"
    
    with open(os.path.join(md_path, md_files[0]), 'r', encoding='utf-8') as f:
        md_content = f.read()
        assert md_content.startswith('---'), "Markdown файл не начинается с YAML frontmatter"
        assert 'title:' in md_content, "Markdown файл не содержит поле 'title' в YAML frontmatter"
        assert 'url:' in md_content, "Markdown файл не содержит поле 'url' в YAML frontmatter"
        assert 'breadcrumb:' in md_content, "Markdown файл не содержит поле 'breadcrumb' в YAML frontmatter"
        assert 'content_hash:' in md_content, "Markdown файл не содержит поле 'content_hash' в YAML frontmatter"

    # Проверяем _meta.json файл
    with open(os.path.join(base_result_path, "_meta.json"), 'r', encoding='utf-8') as f:
        meta_data = json.load(f)
        assert isinstance(meta_data, list), "_meta.json должен содержать список"
        assert len(meta_data) == limit, f"_meta.json должен содержать {limit} записей"
        for item in meta_data:
            assert 'url' in item, "Запись в _meta.json не содержит поле 'url'"
            assert 'title' in item, "Запись в _meta.json не содержит поле 'title'"
            assert 'filename_base' in item, "Запись в _meta.json не содержит поле 'filename_base'"

    print("Metadata validation test passed!")


@pytest.mark.scenario
@pytest.mark.asyncio
async def test_cabinetdoc_scenario_toc_validation():
    """
    Сценарный тест для проверки корректности создания оглавления.
    """
    url = "https://its.1c.ru/db/cabinetdoc/"
    formats = ["markdown"]
    limit = 2
    result_dir_name = "cabinetdoc"

    # Имитируем аргументы командной строки
    test_args = ["main.py", url, "--format"] + formats + ["--limit", str(limit)]
    
    with patch('sys.argv', test_args):
        await main_app.main()

    # --- Проверяем результат ---
    base_result_path = os.path.join(TEST_BASE_DIR, result_dir_name)

    # Проверяем наличие _toc.md
    toc_path = os.path.join(base_result_path, "_toc.md")
    assert os.path.exists(toc_path), "Файл _toc.md не был создан"
    
    with open(toc_path, 'r', encoding='utf-8') as f:
        toc_content = f.read()
        assert "# Оглавление" in toc_content, "_toc.md не содержит заголовка оглавления"
        assert "MARKDOWN" in toc_content, "_toc.md не содержит ссылок на markdown файлы"
        
        # Проверяем наличие ссылок на файлы
        md_path = os.path.join(base_result_path, "markdown")
        md_files = [f for f in os.listdir(md_path) if f.endswith('.md')]
        for md_file in md_files:
            # Проверяем, что имя файла содержится в ссылке (без учета расширения)
            filename_without_ext = md_file.replace('.md', '.markdown')  # Ссылки могут использовать .markdown
            assert filename_without_ext in toc_content or md_file in toc_content, f"_toc.md не содержит ссылку на файл {md_file}"

    print("TOC validation test passed!")
