"""
Модуль для объединения файлов с учетом ограничений по количеству и размеру.
"""

import os
import json
import gzip
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional, Generator
from dataclasses import dataclass
from datetime import datetime
import logging


@dataclass
class MergeConfig:
    """Конфигурация для объединения файлов."""
    max_files: int = 100
    max_size_mb: float = 50.0
    output_format: str = "json"
    separator: str = "\n---\n"
    include_headers: bool = True
    sort_by: str = "name"  # name, size, date
    filter_pattern: Optional[str] = None
    preserve_structure: bool = False
    compress_output: bool = False
    output_dir: Optional[str] = None


class FileMerger:
    """Класс для объединения файлов."""
    
    def __init__(self, config: MergeConfig = None):
        self.config = config or MergeConfig()
        self.logger = logging.getLogger(__name__)
        
    def merge_files(self, input_dir: str, output_dir: str = None, 
                   config: MergeConfig = None) -> List[str]:
        """
        Основной метод объединения файлов.
        
        Args:
            input_dir: Директория с исходными файлами
            output_dir: Директория для выходных файлов
            config: Конфигурация объединения
            
        Returns:
            Список путей к созданным объединенным файлам
        """
        if config:
            self.config = config
            
        input_path = Path(input_dir)
        if not input_path.exists():
            raise FileNotFoundError(f"Директория {input_dir} не найдена")
            
        # Получаем список файлов для обработки
        files = self._get_files_to_process(input_path)
        if not files:
            self.logger.warning(f"Файлы для объединения не найдены в {input_dir}")
            return []
            
        # Группируем файлы по ограничениям
        groups = self._group_files(files)
        
        # Определяем выходную директорию с сохранением структуры
        output_path = self._get_output_path(input_path, output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Объединяем группы
        merged_files = []
        for i, group in enumerate(groups):
            merged_file = self._merge_group(group, output_path, i + 1)
            if merged_file:
                merged_files.append(str(merged_file))
        
        # Копируем метаданные файлы (_toc.md, _meta.json) в родительскую директорию
        parent_output_path = output_path.parent
        metadata_files = self._copy_metadata_files(input_path, parent_output_path)
        merged_files.extend(metadata_files)
                
        self.logger.info(f"Объединено {len(files)} файлов в {len(groups)} групп")
        if metadata_files:
            self.logger.info(f"Скопировано {len(metadata_files)} метаданных файлов")
        return merged_files
        
    def _get_files_to_process(self, input_path: Path) -> List[Path]:
        """Получает список файлов для обработки."""
        files = []
        
        if self.config.filter_pattern:
            pattern = self.config.filter_pattern.replace("*", "")
            files = list(input_path.rglob(f"*{pattern}"))
        else:
            # Поддерживаемые расширения
            extensions = [".json", ".txt", ".md", ".csv"]
            for ext in extensions:
                files.extend(input_path.rglob(f"*{ext}"))
                
        # Сортируем файлы
        if self.config.sort_by == "size":
            files.sort(key=lambda f: f.stat().st_size)
        elif self.config.sort_by == "date":
            files.sort(key=lambda f: f.stat().st_mtime)
        else:  # name
            files.sort(key=lambda f: f.name)
            
        return files
        
    def _group_files(self, files: List[Path]) -> List[List[Path]]:
        """Группирует файлы по ограничениям."""
        groups = []
        current_group = []
        current_size = 0
        
        for file_path in files:
            file_size = file_path.stat().st_size
            
            # Проверяем ограничения
            size_exceeded = (current_size + file_size) > (self.config.max_size_mb * 1024 * 1024)
            count_exceeded = len(current_group) >= self.config.max_files
            
            if (size_exceeded or count_exceeded) and current_group:
                groups.append(current_group)
                current_group = []
                current_size = 0
                
            current_group.append(file_path)
            current_size += file_size
            
        if current_group:
            groups.append(current_group)
            
        return groups
        
    def _copy_metadata_files(self, input_path: Path, output_path: Path) -> List[str]:
        """
        Копирует метаданные файлы (_toc.md, _meta.json) в выходную директорию.
        
        Args:
            input_path: Путь к входной директории
            output_path: Путь к выходной директории
            
        Returns:
            Список путей к скопированным файлам
        """
        metadata_files = []
        metadata_names = ['_toc.md', '_meta.json']
        
        # Ищем метаданные файлы в родительской директории (например, out/cabinetdoc/)
        # если мы находимся в поддиректории (например, out/cabinetdoc/json/)
        search_paths = [input_path]
        
        # Если мы в поддиректории типа out/section/format/, ищем в out/section/
        if "out" in str(input_path):
            parent_path = input_path.parent
            if parent_path.name != "out":  # Не в корне out/
                search_paths.append(parent_path)
        
        for search_path in search_paths:
            for metadata_name in metadata_names:
                source_file = search_path / metadata_name
                if source_file.exists():
                    try:
                        # Копируем файл в выходную директорию
                        destination_file = output_path / metadata_name
                        
                        # Проверяем, не существует ли уже файл в целевой директории
                        if destination_file.exists():
                            self.logger.debug(f"Метаданный файл уже существует: {metadata_name}")
                            continue
                            
                        shutil.copy2(source_file, destination_file)
                        metadata_files.append(str(destination_file))
                        self.logger.debug(f"Скопирован метаданный файл: {metadata_name} из {search_path}")
                    except Exception as e:
                        self.logger.error(f"Ошибка копирования {metadata_name}: {e}")
            else:
                continue  # Не нашли файлы в этом пути, пробуем следующий
            break  # Нашли файлы, выходим из цикла поиска
                
        return metadata_files
        
    def _get_output_path(self, input_path: Path, output_dir: str = None) -> Path:
        """
        Определяет выходную директорию с сохранением структуры папок.
        
        Args:
            input_path: Путь к входной директории
            output_dir: Пользовательская выходная директория
            
        Returns:
            Путь к выходной директории
        """
        if output_dir:
            return Path(output_dir)
            
        # Определяем базовую директорию для merge
        base_path = Path("merge")
        
        # Если входной путь содержит "out/", сохраняем структуру после "out/"
        input_str = str(input_path)
        if "out" in input_str:
            # Находим позицию "out/" и берем все после неё
            out_pos = input_str.find("out")
            if out_pos != -1:
                relative_path = input_str[out_pos + 3:]  # Убираем "out"
                if relative_path.startswith("/") or relative_path.startswith("\\"):
                    relative_path = relative_path[1:]  # Убираем ведущий слеш
                if relative_path:
                    return base_path / relative_path
        
        # Если не нашли "out/", используем имя входной директории
        return base_path / input_path.name
        
    def _merge_group(self, files: List[Path], output_path: Path, group_num: int) -> Optional[Path]:
        """Объединяет группу файлов в один файл."""
        if not files:
            return None
            
        # Определяем формат выходного файла на основе входных файлов
        output_format = self._determine_output_format(files)
            
        if output_format == "json":
            return self._merge_json_group(files, output_path, group_num)
        elif output_format == "markdown":
            return self._merge_markdown_group(files, output_path, group_num)
        elif output_format == "txt":
            return self._merge_txt_group(files, output_path, group_num)
        else:
            return self._merge_generic_group(files, output_path, group_num)
            
    def _determine_output_format(self, files: List[Path]) -> str:
        """Определяет формат выходного файла на основе входных файлов."""
        # Если пользователь явно указал формат, используем его
        if self.config.output_format != "json":
            return self.config.output_format
            
        # Определяем формат по расширениям входных файлов
        extensions = [f.suffix.lower() for f in files]
        
        if all(ext == '.md' for ext in extensions):
            return "markdown"
        elif all(ext == '.txt' for ext in extensions):
            return "txt"
        elif all(ext == '.json' for ext in extensions):
            return "json"
        else:
            # Смешанные форматы - используем JSON как универсальный
            return "json"
            
    def _merge_json_group(self, files: List[Path], output_path: Path, group_num: int) -> Path:
        """Объединяет группу файлов в JSON формат."""
        merged_data = {
            "metadata": {
                "total_files": len(files),
                "total_size_mb": sum(f.stat().st_size for f in files) / (1024 * 1024),
                "created_at": datetime.now().isoformat(),
                "group_number": group_num,
                "source_files": [f.name for f in files]
            },
            "files": []
        }
        
        for file_path in files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    if file_path.suffix == '.json':
                        data = json.load(f)
                        merged_data["files"].append({
                            "original_name": file_path.name,
                            "data": data
                        })
                    else:
                        merged_data["files"].append({
                            "original_name": file_path.name,
                            "content": f.read()
                        })
            except Exception as e:
                self.logger.error(f"Ошибка чтения файла {file_path}: {e}")
                
        # Сохраняем объединенный файл
        output_file = output_path / f"merged_group_{group_num:03d}.json"
        if self.config.compress_output:
            output_file = output_path / f"merged_group_{group_num:03d}.json.gz"
            with gzip.open(output_file, 'wt', encoding='utf-8') as f:
                json.dump(merged_data, f, ensure_ascii=False, indent=2)
        else:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(merged_data, f, ensure_ascii=False, indent=2)
                
        return output_file
        
    def _merge_markdown_group(self, files: List[Path], output_path: Path, group_num: int) -> Path:
        """Объединяет группу файлов в Markdown формат."""
        output_file = output_path / f"merged_group_{group_num:03d}.md"
        
        with open(output_file, 'w', encoding='utf-8') as out_f:
            # Заголовок документа
            out_f.write(f"# Объединенная документация - Группа {group_num}\n\n")
            
            # Метаданные
            total_size = sum(f.stat().st_size for f in files) / (1024 * 1024)
            out_f.write(f"## Метаданные\n\n")
            out_f.write(f"- Всего файлов: {len(files)}\n")
            out_f.write(f"- Размер: {total_size:.2f} MB\n")
            out_f.write(f"- Создано: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            # Содержимое файлов
            for i, file_path in enumerate(files):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Добавляем разделитель
                    if i > 0:
                        out_f.write(self.config.separator)
                        
                    # Добавляем заголовок файла
                    if self.config.include_headers:
                        out_f.write(f"\n# {file_path.stem}\n\n")
                        
                    out_f.write(content)
                    
                except Exception as e:
                    self.logger.error(f"Ошибка чтения файла {file_path}: {e}")
                    out_f.write(f"\n<!-- Ошибка чтения файла {file_path.name}: {e} -->\n")
                    
        return output_file
        
    def _merge_txt_group(self, files: List[Path], output_path: Path, group_num: int) -> Path:
        """Объединяет группу файлов в текстовый формат."""
        output_file = output_path / f"merged_group_{group_num:03d}.txt"
        
        with open(output_file, 'w', encoding='utf-8') as out_f:
            # Заголовок
            out_f.write(f"Объединенная документация - Группа {group_num}\n")
            out_f.write("=" * 50 + "\n\n")
            
            for i, file_path in enumerate(files):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    # Добавляем разделитель
                    if i > 0:
                        out_f.write(self.config.separator)
                        
                    # Добавляем заголовок файла
                    if self.config.include_headers:
                        out_f.write(f"\nФайл: {file_path.name}\n")
                        out_f.write("-" * 30 + "\n")
                        
                    out_f.write(content)
                    
                except Exception as e:
                    self.logger.error(f"Ошибка чтения файла {file_path}: {e}")
                    out_f.write(f"\n[Ошибка чтения файла {file_path.name}: {e}]\n")
                    
        return output_file
        
    def _merge_generic_group(self, files: List[Path], output_path: Path, group_num: int) -> Path:
        """Универсальное объединение файлов."""
        output_file = output_path / f"merged_group_{group_num:03d}.txt"
        
        with open(output_file, 'w', encoding='utf-8') as out_f:
            for i, file_path in enumerate(files):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    if i > 0:
                        out_f.write(self.config.separator)
                        
                    if self.config.include_headers:
                        out_f.write(f"\n=== {file_path.name} ===\n")
                        
                    out_f.write(content)
                    
                except Exception as e:
                    self.logger.error(f"Ошибка чтения файла {file_path}: {e}")
                    
        return output_file
        
    def get_merge_statistics(self, input_dir: str) -> Dict[str, Any]:
        """Получает статистику по файлам для объединения."""
        input_path = Path(input_dir)
        files = self._get_files_to_process(input_path)
        
        if not files:
            return {"total_files": 0, "total_size_mb": 0, "estimated_groups": 0}
            
        total_size = sum(f.stat().st_size for f in files)
        total_size_mb = total_size / (1024 * 1024)
        
        # Оцениваем количество групп
        groups_by_count = len(files) // self.config.max_files + (1 if len(files) % self.config.max_files else 0)
        groups_by_size = int(total_size_mb // self.config.max_size_mb) + (1 if total_size_mb % self.config.max_size_mb else 0)
        estimated_groups = max(groups_by_count, groups_by_size)
        
        return {
            "total_files": len(files),
            "total_size_mb": round(total_size_mb, 2),
            "estimated_groups": estimated_groups,
            "avg_file_size_mb": round(total_size_mb / len(files), 2),
            "files_by_extension": self._count_files_by_extension(files)
        }
        
    def _count_files_by_extension(self, files: List[Path]) -> Dict[str, int]:
        """Подсчитывает файлы по расширениям."""
        extensions = {}
        for file_path in files:
            ext = file_path.suffix.lower()
            extensions[ext] = extensions.get(ext, 0) + 1
        return extensions


def merge_files_cli(input_dir: str, output_dir: str = None, **kwargs) -> List[str]:
    """
    Удобная функция для объединения файлов из командной строки.
    
    Args:
        input_dir: Директория с исходными файлами
        output_dir: Директория для выходных файлов
        **kwargs: Параметры конфигурации
        
    Returns:
        Список путей к созданным объединенным файлам
    """
    config = MergeConfig(**kwargs)
    merger = FileMerger(config)
    return merger.merge_files(input_dir, output_dir)
