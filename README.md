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

3. **Создайте файл `.env`** в корне проекта:
   ```bash
   # Windows
   copy .env-example .env
   
   # Linux/macOS
   cp .env-example .env
   ```

4. **Откройте файл `.env`** и укажите ваши учетные данные:
   ```env
   LOGIN_1C_USER="ваш_логин"
   LOGIN_1C_PASSWORD="ваш_пароль"
   
   # Опционально: если browserless запущен на другом адресе
   # BROWSERLESS_URL=http://localhost:3000
   ```

5. **Как работает авторизация:**
   - Скрипт автоматически открывает страницу входа: `https://login.1c.ru/login`
   - Заполняет поля логина и пароля из файла `.env`
   - Нажимает кнопку входа
   - Проверяет успешность авторизации (перенаправление на страницу профиля)
   - После успешной авторизации начинается процесс скрапинга

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

## 📊 Логирование

Проект использует многоуровневую систему логирования:

- **`script_log.txt`** - основной лог (ротация при 10 МБ)
- **`errors.log`** - только ошибки (ротация при 5 МБ)
- **Verbose режим** - детальная отладка с флагом `--verbose`

> 📖 **Подробно о логировании:** [LOGGING.md](docs/LOGGING.md)

## 📂 Структура проекта

```text
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

## 📝 Примеры использования и настройки

### Базовое использование

```bash
# Скачать все статьи раздела в JSON формате
python main.py https://its.1c.ru/db/cabinetdoc --format json

# Скачать в нескольких форматах одновременно
python main.py https://its.1c.ru/db/cabinetdoc --format json pdf markdown

# Тестовый запуск (первые 5 статей)
python main.py https://its.1c.ru/db/cabinetdoc --limit 5
```

### Работа с форматами

```bash
# Скачать весь раздел документации во всех форматах
python main.py https://its.1c.ru/db/erp25ltsdoc --format json pdf txt markdown

# RAG-режим для AI систем (Markdown с метаданными)
python main.py https://its.1c.ru/db/cabinetdoc --format markdown --rag --parallel 8
```

### Обновление и индексация

```bash
# Обновить только измененные статьи
python main.py https://its.1c.ru/db/cabinetdoc --update --format json pdf

# Создать индекс без скачивания контента
python main.py https://its.1c.ru/db/cabinetdoc --no-scrape
```

### Производительность и оптимизация

```bash
# Использовать параллельную обработку (8 потоков)
python main.py https://its.1c.ru/db/cabinetdoc --parallel 8

# Настройки для медленного соединения
python main.py https://its.1c.ru/db/cabinetdoc \
  --timeout 180 --retry-count 5 --delay 2

# Настройки для быстрого соединения
python main.py https://its.1c.ru/db/cabinetdoc \
  --timeout 30 --retry-count 2 --delay 0.2
```

### Объединение файлов

```bash
# Объединить JSON файлы (автоматически определит формат)
python main.py --merge --merge-dir out/cabinetdoc/json --max-files 100 --max-size 50
# → merge/cabinetdoc/json/merged_group_*.json

# Объединить Markdown файлы
python main.py --merge --merge-dir out/cabinetdoc/markdown --max-files 50
# → merge/cabinetdoc/markdown/merged_group_*.md

# Принудительно указать формат вывода
python main.py --merge --merge-dir out/cabinetdoc/json --merge-format markdown --max-files 100
# → merge/cabinetdoc/json/merged_group_*.md

# Показать статистику объединения без выполнения
python main.py --merge --merge-dir out/cabinetdoc/json --merge-stats

# Сжать объединенные файлы
python main.py --merge --merge-dir out/cabinetdoc/json --compress
# → merge/cabinetdoc/json/merged_group_*.json.gz
```

**Результат объединения:**

- JSON файлы → `merge/cabinetdoc/json/merged_group_*.json` + метаданные в `merge/cabinetdoc/`
- Markdown файлы → `merge/cabinetdoc/markdown/merged_group_*.md` + метаданные в `merge/cabinetdoc/`

### Отладка и диагностика

```bash
# Подробное логирование для отладки
python main.py https://its.1c.ru/db/cabinetdoc --verbose

# Без повторных попыток (для быстрой отладки)
python main.py https://its.1c.ru/db/cabinetdoc --retry-count 0
```

> 📖 **Подробная документация:** [ADVANCED_USAGE.md](docs/ADVANCED_USAGE.md)  
> 📖 **Объединение файлов:** [FILE_MERGING.md](docs/FILE_MERGING.md)  
> 📖 **Больше примеров:** [EXAMPLES.md](docs/EXAMPLES.md)

## 🧪 Тестирование

```bash
# Запуск всех тестов
python -m pytest

# Сценарные тесты
python -m pytest tests/test_scenario.py -v -s

# Конкретный тест
python -m pytest tests/test_scenario.py::test_cabinetdoc_scenario_all_formats -v
```

## ⚖️ Условия использования

Используйте продукт только при соблюдении условий:

- Материалы на ИТС бесплатные ИЛИ у вас оплачена подписка
- На странице статей активна кнопка "Печать"

## 📄 Лицензия

MIT License - см. [LICENSE](LICENSE) файл.

---

**Версия:** 1.0.0  
**Поддержка:** [GitHub Issues](https://github.com/hawkxtreme/scraping_its/issues)
