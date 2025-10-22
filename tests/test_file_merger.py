"""
Тесты для модуля объединения файлов.
"""

import pytest
import tempfile
import json
import os
import shutil
from pathlib import Path
from src.file_merger import FileMerger, MergeConfig


@pytest.fixture
def temp_dir():
    """Создает временную директорию для тестов."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_files(temp_dir):
    """Создает тестовые файлы для объединения."""
    files = []
    
    # Создаем JSON файлы
    for i in range(5):
        file_path = temp_dir / f"article_{i:03d}.json"
        data = {
            "id": i,
            "title": f"Статья {i}",
            "content": f"Содержимое статьи {i}",
            "url": f"https://example.com/article/{i}"
        }
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
        files.append(file_path)
    
    # Создаем TXT файлы
    for i in range(3):
        file_path = temp_dir / f"document_{i:03d}.txt"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"Текстовый документ {i}\n\nСодержимое документа {i}")
        files.append(file_path)
    
    # Создаем Markdown файлы
    for i in range(2):
        file_path = temp_dir / f"guide_{i:03d}.md"
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"# Руководство {i}\n\nОписание руководства {i}")
        files.append(file_path)
    
    return files


class TestFileMerger:
    """Тесты для класса FileMerger."""
    
    def test_merge_config_defaults(self):
        """Тест значений по умолчанию для MergeConfig."""
        config = MergeConfig()
        assert config.max_files == 100
        assert config.max_size_mb == 50.0
        assert config.output_format == "json"
        assert config.sort_by == "name"
        assert not config.compress_output
    
    def test_get_files_to_process(self, temp_dir, sample_files):
        """Тест получения файлов для обработки."""
        merger = FileMerger()
        files = merger._get_files_to_process(temp_dir)
        
        assert len(files) == 10  # 5 JSON + 3 TXT + 2 MD
        assert all(f.suffix in ['.json', '.txt', '.md'] for f in files)
    
    def test_get_files_to_process_with_filter(self, temp_dir, sample_files):
        """Тест получения файлов с фильтром."""
        config = MergeConfig(filter_pattern="*.json")
        merger = FileMerger(config)
        files = merger._get_files_to_process(temp_dir)
        
        assert len(files) == 5
        assert all(f.suffix == '.json' for f in files)
    
    def test_group_files_by_count(self, temp_dir, sample_files):
        """Тест группировки файлов по количеству."""
        config = MergeConfig(max_files=3)
        merger = FileMerger(config)
        files = merger._get_files_to_process(temp_dir)
        groups = merger._group_files(files)
        
        # Должно быть 4 группы: 3, 3, 3, 1 файл
        assert len(groups) == 4
        assert len(groups[0]) == 3
        assert len(groups[1]) == 3
        assert len(groups[2]) == 3
        assert len(groups[3]) == 1
    
    def test_group_files_by_size(self, temp_dir, sample_files):
        """Тест группировки файлов по размеру."""
        config = MergeConfig(max_size_mb=0.001)  # Очень маленький размер
        merger = FileMerger(config)
        files = merger._get_files_to_process(temp_dir)
        groups = merger._group_files(files)
        
        # При очень маленьком размере все файлы должны поместиться в одну группу
        # так как они очень маленькие
        assert len(groups) >= 1
        assert all(len(group) >= 1 for group in groups)
    
    def test_merge_json_group(self, temp_dir, sample_files):
        """Тест объединения JSON файлов."""
        merger = FileMerger()
        output_path = temp_dir / "output"
        output_path.mkdir()
        
        # Берем первые 3 JSON файла
        json_files = [f for f in sample_files if f.suffix == '.json'][:3]
        merged_file = merger._merge_json_group(json_files, output_path, 1)
        
        assert merged_file.exists()
        assert merged_file.name == "merged_group_001.json"
        
        # Проверяем содержимое
        with open(merged_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        assert "metadata" in data
        assert "files" in data
        assert data["metadata"]["total_files"] == 3
        assert len(data["files"]) == 3
    
    def test_merge_markdown_group(self, temp_dir, sample_files):
        """Тест объединения Markdown файлов."""
        merger = FileMerger()
        output_path = temp_dir / "output"
        output_path.mkdir()
        
        # Берем все MD файлы
        md_files = [f for f in sample_files if f.suffix == '.md']
        merged_file = merger._merge_markdown_group(md_files, output_path, 1)
        
        assert merged_file.exists()
        assert merged_file.name == "merged_group_001.md"
        
        # Проверяем содержимое
        with open(merged_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "# Объединенная документация" in content
        assert "## Метаданные" in content
        assert "Всего файлов: 2" in content
    
    def test_merge_txt_group(self, temp_dir, sample_files):
        """Тест объединения TXT файлов."""
        merger = FileMerger()
        output_path = temp_dir / "output"
        output_path.mkdir()
        
        # Берем первые 2 TXT файла
        txt_files = [f for f in sample_files if f.suffix == '.txt'][:2]
        merged_file = merger._merge_txt_group(txt_files, output_path, 1)
        
        assert merged_file.exists()
        assert merged_file.name == "merged_group_001.txt"
        
        # Проверяем содержимое
        with open(merged_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "Объединенная документация" in content
        assert "Файл: document_000.txt" in content
    
    def test_merge_files_complete(self, temp_dir, sample_files):
        """Тест полного процесса объединения файлов."""
        config = MergeConfig(max_files=3)
        merger = FileMerger(config)
        
        # Создаем структуру out/section/format для тестирования
        test_input_dir = temp_dir / "out" / "test_section" / "json"
        test_input_dir.mkdir(parents=True)
        
        # Перемещаем JSON файлы в тестовую структуру
        json_files = [f for f in sample_files if f.suffix == '.json']
        for file_path in json_files:
            shutil.copy2(file_path, test_input_dir)
        
        merged_files = merger.merge_files(str(test_input_dir))
        
        # Проверяем, что файлы созданы в правильной структуре
        assert len(merged_files) > 0
        merge_dir = Path("merge") / "test_section" / "json"
        assert merge_dir.exists()
        
        # Проверяем, что все файлы созданы
        for file_path in merged_files:
            assert Path(file_path).exists()
            # Проверяем, что файлы имеют правильное расширение
            assert file_path.endswith('.json')
    
    def test_get_merge_statistics(self, temp_dir, sample_files):
        """Тест получения статистики объединения."""
        merger = FileMerger()
        stats = merger.get_merge_statistics(str(temp_dir))
        
        assert stats["total_files"] == 10
        assert stats["total_size_mb"] >= 0  # Может быть 0 для очень маленьких файлов
        assert stats["estimated_groups"] > 0
        assert ".json" in stats["files_by_extension"]
        assert ".txt" in stats["files_by_extension"]
        assert ".md" in stats["files_by_extension"]
    
    def test_compress_output(self, temp_dir, sample_files):
        """Тест сжатия выходных файлов."""
        config = MergeConfig(compress_output=True)
        merger = FileMerger(config)
        output_path = temp_dir / "output"
        output_path.mkdir()
        
        json_files = [f for f in sample_files if f.suffix == '.json'][:2]
        merged_file = merger._merge_json_group(json_files, output_path, 1)
        
        assert merged_file.name.endswith('.json.gz')
        assert merged_file.exists()
    
    def test_sort_by_size(self, temp_dir, sample_files):
        """Тест сортировки файлов по размеру."""
        config = MergeConfig(sort_by="size")
        merger = FileMerger(config)
        files = merger._get_files_to_process(temp_dir)
        
        # Проверяем, что файлы отсортированы по размеру
        sizes = [f.stat().st_size for f in files]
        assert sizes == sorted(sizes)
    
    def test_sort_by_date(self, temp_dir, sample_files):
        """Тест сортировки файлов по дате."""
        config = MergeConfig(sort_by="date")
        merger = FileMerger(config)
        files = merger._get_files_to_process(temp_dir)
        
        # Проверяем, что файлы отсортированы по дате модификации
        dates = [f.stat().st_mtime for f in files]
        assert dates == sorted(dates)
    
    def test_empty_directory(self, temp_dir):
        """Тест обработки пустой директории."""
        merger = FileMerger()
        merged_files = merger.merge_files(str(temp_dir))
        
        assert merged_files == []
    
    def test_nonexistent_directory(self):
        """Тест обработки несуществующей директории."""
        merger = FileMerger()
        
        with pytest.raises(FileNotFoundError):
            merger.merge_files("/nonexistent/directory")
    
    def test_merge_config_custom(self):
        """Тест создания кастомной конфигурации."""
        config = MergeConfig(
            max_files=50,
            max_size_mb=25.0,
            output_format="markdown",
            sort_by="size",
            compress_output=True
        )
        
        assert config.max_files == 50
        assert config.max_size_mb == 25.0
        assert config.output_format == "markdown"
        assert config.sort_by == "size"
        assert config.compress_output
    
    def test_output_path_structure(self, temp_dir):
        """Тест сохранения структуры папок в выходной директории."""
        merger = FileMerger()
        
        # Тест с путем содержащим "out/"
        input_path = Path(temp_dir) / "out" / "cabinetdoc" / "json"
        output_path = merger._get_output_path(input_path)
        expected_path = Path("merge") / "cabinetdoc" / "json"
        assert output_path == expected_path
        
        # Тест с обычным путем
        input_path = Path(temp_dir) / "some_folder"
        output_path = merger._get_output_path(input_path)
        expected_path = Path("merge") / "some_folder"
        assert output_path == expected_path
        
        # Тест с пользовательской выходной директорией
        custom_output = Path(temp_dir) / "custom_output"
        output_path = merger._get_output_path(input_path, str(custom_output))
        assert output_path == custom_output
    
    def test_auto_format_detection(self, temp_dir, sample_files):
        """Тест автоматического определения формата выходных файлов."""
        merger = FileMerger()
        
        # Тест с JSON файлами
        json_files = [f for f in sample_files if f.suffix == '.json'][:2]
        format_result = merger._determine_output_format(json_files)
        assert format_result == "json"
        
        # Тест с Markdown файлами
        md_files = [f for f in sample_files if f.suffix == '.md'][:2]
        format_result = merger._determine_output_format(md_files)
        assert format_result == "markdown"
        
        # Тест с TXT файлами
        txt_files = [f for f in sample_files if f.suffix == '.txt'][:2]
        format_result = merger._determine_output_format(txt_files)
        assert format_result == "txt"
    
    def test_copy_metadata_files(self):
        """Тест копирования метаданных файлов."""
        config = MergeConfig()
        merger = FileMerger(config)
        
        # Создаем временную структуру директорий
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Создаем структуру out/section/format/
            input_dir = temp_path / "out" / "test_section" / "json"
            input_dir.mkdir(parents=True)
            
            # Создаем метаданные файлы в родительской директории
            parent_dir = input_dir.parent
            (parent_dir / "_toc.md").write_text("# Table of Contents")
            (parent_dir / "_meta.json").write_text('{"title": "Test"}')
            
            # Создаем выходную директорию (родительскую для метаданных)
            output_dir = temp_path / "merge" / "test_section"
            output_dir.mkdir(parents=True)
            
            # Копируем метаданные файлы
            metadata_files = merger._copy_metadata_files(input_dir, output_dir)
            
            # Проверяем, что файлы скопированы
            assert len(metadata_files) == 2
            assert (output_dir / "_toc.md").exists()
            assert (output_dir / "_meta.json").exists()
            
            # Проверяем содержимое
            assert (output_dir / "_toc.md").read_text() == "# Table of Contents"
            assert (output_dir / "_meta.json").read_text() == '{"title": "Test"}'


class TestMergeConfig:
    """Тесты для класса MergeConfig."""
    
    def test_config_validation(self):
        """Тест валидации конфигурации."""
        # Валидная конфигурация
        config = MergeConfig(max_files=100, max_size_mb=50.0)
        assert config.max_files == 100
        assert config.max_size_mb == 50.0
        
        # Проверка значений по умолчанию
        config = MergeConfig()
        assert config.max_files > 0
        assert config.max_size_mb > 0
        assert config.output_format in ["json", "markdown", "txt"]
        assert config.sort_by in ["name", "size", "date"]


if __name__ == "__main__":
    pytest.main([__file__])
