# Механизм объединения файлов

## Обзор

Модуль для объединения множества файлов в группы с учетом ограничений по количеству файлов и размеру.

## Основные функции

### 1. Объединение по количеству файлов
```python
# Объединить максимум 100 файлов в один
merge_files_by_count(input_dir, output_dir, max_files=100)
```

### 2. Объединение по размеру
```python
# Объединить файлы до достижения размера 50MB
merge_files_by_size(input_dir, output_dir, max_size_mb=50)
```

### 3. Комбинированное объединение
```python
# Объединить максимум 100 файлов ИЛИ до размера 50MB
merge_files_combined(input_dir, output_dir, max_files=100, max_size_mb=50)
```

## Поддерживаемые форматы

- **JSON** - объединение в массив объектов
- **TXT** - объединение с разделителями
- **Markdown** - объединение с заголовками

## Настройки

### Базовые параметры
- `max_files` - максимальное количество файлов в группе
- `max_size_mb` - максимальный размер группы в МБ
- `output_format` - формат выходных файлов
- `separator` - разделитель между файлами
- `include_headers` - включать заголовки файлов

### Дополнительные опции
- `sort_by` - сортировка файлов (name, size, date)
- `filter_pattern` - фильтр файлов по имени
- `preserve_structure` - сохранить структуру папок
- `compress_output` - сжать выходные файлы

## Примеры использования

### Объединение файлов (автоматическое определение формата)
```python
from src.file_merger import FileMerger

merger = FileMerger()
merger.merge_files(
    input_dir="out/cabinetdoc/json",
    max_files=100,
    max_size_mb=50
)
# Результат: merge/cabinetdoc/json/merged_group_*.json
```

### Объединение Markdown файлов
```python
merger.merge_files(
    input_dir="out/cabinetdoc/markdown",
    max_files=50
)
# Результат: merge/cabinetdoc/markdown/merged_group_*.md
```

### Объединение с явным указанием формата
```python
from src.file_merger import MergeConfig

config = MergeConfig(output_format="markdown", max_files=100)
merger = FileMerger(config)
merger.merge_files("out/cabinetdoc/json")
# Результат: merge/cabinetdoc/json/merged_group_*.md (принудительно Markdown)
```

## Командная строка

### Базовые команды
```bash
# Объединить JSON файлы (автоматически определит формат)
python main.py --merge --merge-dir out/cabinetdoc/json --max-files 100 --max-size 50

# Объединить Markdown файлы (автоматически определит формат)
python main.py --merge --merge-dir out/cabinetdoc/markdown --max-files 50

# Объединить с фильтрацией
python main.py --merge --merge-dir out/cabinetdoc --merge-filter "*.md" --max-files 50
```

### Продвинутые опции
```bash
# Объединить с сортировкой и сжатием
python main.py --merge --merge-dir out/cabinetdoc/json \
  --max-files 100 --max-size 50 \
  --sort-by size --compress

# Принудительно указать формат вывода
python main.py --merge --merge-dir out/cabinetdoc/json \
  --merge-format markdown --max-files 100
```

## Структура выходных файлов

### Организация папок

Объединенные файлы создаются в папке `merge` с сохранением структуры из папки `out`:

```
out/cabinetdoc/json/*.json → merge/cabinetdoc/json/merged_group_*.json
out/erp25ltsdoc/markdown/*.md → merge/erp25ltsdoc/markdown/merged_group_*.md
out/v8std/txt/*.txt → merge/v8std/txt/merged_group_*.txt
```

**Метаданные файлы** (`_toc.md`, `_meta.json`) автоматически копируются из родительской директории в родительскую выходную директорию (например, `merge/cabinetdoc/`) для сохранения контекста и структуры документации.

### Примеры структуры

```
merge/
├── cabinetdoc/
│   ├── _toc.md
│   ├── _meta.json
│   ├── json/
│   │   ├── merged_group_001.json
│   │   ├── merged_group_002.json
│   │   └── merged_group_003.json
│   ├── markdown/
│   │   ├── merged_group_001.md
│   │   └── merged_group_002.md
│   └── pdf/
│       └── merged_group_001.pdf
├── erp25ltsdoc/
│   ├── json/
│   │   └── merged_group_001.json
│   └── markdown/
│       └── merged_group_001.md
└── v8std/
    └── json/
        ├── merged_group_001.json
        └── merged_group_002.json
```

### JSON объединение
```json
{
  "metadata": {
    "total_files": 100,
    "total_size": "45.2 MB",
    "created_at": "2025-01-21T10:30:00Z",
    "source_dir": "out/cabinetdoc/json"
  },
  "files": [
    {
      "original_name": "0001_article.json",
      "title": "Руководство пользователя",
      "url": "https://its.1c.ru/db/cabinetdoc/article1",
      "content": "..."
    }
  ]
}
```

### Markdown объединение
```markdown
# Объединенная документация

## Метаданные
- Всего файлов: 100
- Размер: 45.2 MB
- Создано: 2025-01-21 10:30:00

---

# 0001. Руководство пользователя

Содержимое статьи...

---

# 0002. Термины и определения

Содержимое статьи...
```

## Обработка ошибок

### Типичные проблемы
- Недостаточно места на диске
- Ошибки чтения файлов
- Превышение лимитов памяти
- Конфликты имен файлов

### Решения
- Проверка доступного места перед объединением
- Обработка поврежденных файлов
- Потоковая обработка для больших файлов
- Автоматическое переименование конфликтующих файлов

## Производительность

### Оптимизации
- Потоковое чтение файлов
- Пакетная обработка
- Кэширование метаданных
- Параллельная обработка групп

### Мониторинг
- Прогресс-бар объединения
- Статистика по группам
- Время выполнения
- Использование памяти
