# Скраппер статей 1С ИТС

Этот скрипт предназначен для скрапинга статей с сайта its.1c.ru и сохранения их в различных форматах.

## 🚀 Быстрый старт

### Установка

1. **Запустите Docker контейнер:**
   ```bash
   docker run -p 3000:3000 browserless/chrome
   ```

2. **Установите зависимости:**
   ```bash
   git clone https://github.com/hawkxtreme/scraping_its
   cd scraping_its
   python -m venv venv
   venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   playwright install chromium
   ```

3. **Настройте учетные данные:**
   ```bash
   copy .env-example .env
   # Отредактируйте .env файл с вашими данными для входа на 1С
   ```

### Базовое использование

```bash
# Скачать все статьи раздела в JSON формате
python main.py https://its.1c.ru/db/cabinetdoc --format json

# Скачать в нескольких форматах
python main.py https://its.1c.ru/db/cabinetdoc --format json pdf markdown

# Тестовый запуск (первые 5 статей)
python main.py https://its.1c.ru/db/cabinetdoc --limit 5
```

## 📋 Системные требования

- **Python:** 3.8+
- **Docker:** 20.10+ (для browserless)
- **Playwright:** устанавливается автоматически
- **ОС:** Windows 10/11, Linux (Ubuntu 20.04+), macOS 11+


## ⚙️ Основные команды

| Аргумент | Описание | Пример |
|----------|----------|---------|
| `url` | URL для скрапинга | `https://its.1c.ru/db/cabinetdoc` |
| `--format` | Форматы вывода | `json`, `pdf`, `txt`, `markdown` |
| `--limit` | Ограничить количество статей | `--limit 10` |
| `--parallel` | Количество потоков | `--parallel 4` |
| `--update` | Обновить только измененные | `--update` |
| `--rag` | Добавить метаданные для RAG | `--rag` |
| `--verbose` | Подробное логирование | `--verbose` |

### Полный список команд

```bash
python main.py --help
```

## 📁 Поддерживаемые форматы

| Формат | Описание | Особенности |
|--------|----------|-------------|
| **JSON** | Структурированные данные | Полные метаданные, ссылки |
| **PDF** | Документы для печати | Точное форматирование, изображения |
| **TXT** | Простой текст | Компактный размер, индексация |
| **Markdown** | Форматированный текст | GitHub-совместимый, RAG-метаданные |

## 🔧 Продвинутые настройки

### Таймауты и повторные попытки

```bash
# Для медленного соединения
python main.py https://its.1c.ru/db/cabinetdoc \
  --timeout 180 --retry-count 5 --delay 2

# Для быстрого соединения  
python main.py https://its.1c.ru/db/cabinetdoc \
  --timeout 30 --retry-count 2 --delay 0.2
```

### Параллельная обработка

```bash
# Использовать 8 потоков для ускорения
python main.py https://its.1c.ru/db/cabinetdoc --parallel 8
```

### Объединение файлов

```bash
# Объединить JSON файлы (автоматически определит формат)
python main.py --merge --merge-dir out/cabinetdoc/json --max-files 100 --max-size 50

# Объединить Markdown файлы (автоматически определит формат)
python main.py --merge --merge-dir out/cabinetdoc/markdown --max-files 50

# Принудительно указать формат вывода
python main.py --merge --merge-dir out/cabinetdoc/json --merge-format markdown --max-files 100

# Показать статистику объединения
python main.py --merge --merge-dir out/cabinetdoc/json --merge-stats
```

**Результат:** 
- JSON файлы → `merge/cabinetdoc/json/merged_group_*.json` + метаданные в `merge/cabinetdoc/`
- Markdown файлы → `merge/cabinetdoc/markdown/merged_group_*.md` + метаданные в `merge/cabinetdoc/`

> 📖 **Подробная документация:** [ADVANCED_USAGE.md](docs/ADVANCED_USAGE.md)  
> 📖 **Объединение файлов:** [FILE_MERGING.md](docs/FILE_MERGING.md)

## 📊 Логирование

Проект использует многоуровневую систему логирования:

- **`script_log.txt`** - основной лог (ротация при 10 МБ)
- **`errors.log`** - только ошибки (ротация при 5 МБ)
- **Verbose режим** - детальная отладка с флагом `--verbose`

> 📖 **Подробно о логировании:** [LOGGING.md](docs/LOGGING.md)

## 🧪 Тестирование

```bash
# Запуск всех тестов
python -m pytest

# Сценарные тесты
python -m pytest tests/test_scenario.py -v -s

# Конкретный тест
python -m pytest tests/test_scenario.py::test_cabinetdoc_scenario_all_formats -v
```

## 📂 Структура проекта

```
scraping_its/
├── main.py              # Точка входа
├── src/                 # Основной код
│   ├── scraper.py       # Логика скрапинга
│   ├── parser*.py       # Парсеры контента
│   ├── config.py        # Конфигурация
│   ├── file_manager.py  # Работа с файлами
│   ├── logger.py        # Система логирования
│   └── utils.py         # Утилиты
├── tests/               # Тесты
├── out/                 # Результаты скрапинга
└── docs/                # Документация
```

## 📝 Примеры использования

### Базовые сценарии

```bash
# Скачать весь раздел документации
python main.py https://its.1c.ru/db/erp25ltsdoc --format json pdf txt markdown

# Обновить только измененные статьи
python main.py https://its.1c.ru/db/cabinetdoc --update --format json pdf

# Создать индекс без скачивания контента
python main.py https://its.1c.ru/db/cabinetdoc --no-scrape
```

### RAG-режим для AI систем

```bash
# Markdown с метаданными для RAG
python main.py https://its.1c.ru/db/cabinetdoc --format markdown --rag
```

### Отладка и диагностика

```bash
# Подробное логирование
python main.py https://its.1c.ru/db/cabinetdoc --verbose

# Без повторных попыток (для отладки)
python main.py https://its.1c.ru/db/cabinetdoc --retry-count 0
```

### Объединение файлов

```bash
# Объединить JSON файлы (автоматически определит формат)
python main.py --merge --merge-dir out/cabinetdoc/json --max-files 100
# → merge/cabinetdoc/json/merged_group_*.json

# Объединить Markdown файлы (автоматически определит формат)
python main.py --merge --merge-dir out/cabinetdoc/markdown --max-files 50
# → merge/cabinetdoc/markdown/merged_group_*.md

# Принудительно указать формат вывода
python main.py --merge --merge-dir out/cabinetdoc/json --merge-format markdown --max-files 100
# → merge/cabinetdoc/json/merged_group_*.md

# Сжать объединенные файлы
python main.py --merge --merge-dir out/cabinetdoc/json --compress
# → merge/cabinetdoc/json/merged_group_*.json.gz
```

> 📖 **Больше примеров:** [EXAMPLES.md](docs/EXAMPLES.md)

## ⚖️ Условия использования

Используйте продукт только при соблюдении условий:
- Материалы на ИТС бесплатные ИЛИ у вас оплачена подписка
- На странице статей активна кнопка "Печать"

## 🛣️ Roadmap

Текущие планы развития проекта:

- ✅ Улучшенное логирование и обработка ошибок
- ✅ Настраиваемые таймауты и повторные попытки  
- 🔄 Система кэширования для ускорения
- 📋 Расширенная фильтрация статей
- 📋 Поддержка формата DOCX

> 📖 **Подробный roadmap:** [ROADMAP_ANALYSIS.md](ROADMAP_ANALYSIS.md)

## 📄 Лицензия

MIT License - см. [LICENSE](LICENSE) файл.

---

**Версия:** 1.0.0  
**Поддержка:** [GitHub Issues](https://github.com/hawkxtreme/scraping_its/issues)
