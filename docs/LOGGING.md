# Система логирования

## Обзор

Проект использует продвинутую систему логирования с несколькими уровнями и возможностями для эффективной диагностики проблем.

## Файлы логов

В каждой выходной директории создаются следующие файлы логов:

### `script_log.txt` - Основной лог
- **Содержит:** Все события (INFO, WARNING, ERROR, CRITICAL)
- **Ротация:** При достижении 10 МБ
- **Резервные копии:** До 5 файлов
- **Формат:** `[2025-01-21 10:30:45] [INFO] [scraper] Starting article scraping...`

### `errors.log` - Лог ошибок
- **Содержит:** Только ошибки (ERROR и CRITICAL)
- **Ротация:** При достижении 5 МБ  
- **Резервные копии:** До 3 файлов
- **Назначение:** Быстрый поиск проблем

## Уровни логирования

| Уровень | Описание | Когда используется |
|---------|----------|-------------------|
| **DEBUG** | Подробная отладочная информация | С флагом `--verbose` |
| **INFO** | Общая информация о процессе | Обычная работа |
| **WARNING** | Предупреждения (не критичные) | Потенциальные проблемы |
| **ERROR** | Ошибки, не останавливающие процесс | Проблемы с отдельными статьями |
| **CRITICAL** | Критические ошибки | Остановка всего процесса |

## Verbose режим

### Включение подробного логирования

```bash
python main.py https://its.1c.ru/db/cabinetdoc --format json --verbose
```

### Что показывает verbose режим

- **Подробную информацию о каждом шаге**
- **URL-адреса загружаемых страниц**
- **Информацию о парсерах**
- **Время выполнения операций**
- **Детали обработки каждой статьи**
- **Статистику использования ресурсов**

### Пример verbose вывода

```
[2025-01-21 10:30:45] [DEBUG] [scraper] Connecting to browserless...
[2025-01-21 10:30:46] [DEBUG] [scraper] Browser connected successfully
[2025-01-21 10:30:47] [DEBUG] [scraper] Navigating to: https://its.1c.ru/db/cabinetdoc
[2025-01-21 10:30:48] [DEBUG] [scraper] Page loaded in 1.2 seconds
[2025-01-21 10:30:49] [DEBUG] [parser] Parsing article: "Руководство пользователя"
[2025-01-21 10:30:50] [DEBUG] [parser] Found 15 sections in article
[2025-01-21 10:30:51] [INFO] [scraper] Article processed successfully
```

## Контекстное логирование ошибок

Система автоматически добавляет контекст к ошибкам:

### Информация в логах ошибок

- **URL проблемной страницы**
- **Название статьи**
- **Тип операции**
- **Stack trace**
- **Предложения по исправлению**

### Пример контекстной ошибки

```
[2025-01-21 10:30:45] [ERROR] [scraper] Failed to load article
URL: https://its.1c.ru/db/cabinetdoc/article123
Title: "Руководство пользователя"
Operation: page_load
Error: TimeoutError: Page load timeout after 90 seconds
Suggestion: Try increasing --timeout parameter or check network connection
Stack trace:
  File "src/scraper.py", line 245, in load_article
    await page.goto(url, timeout=90000)
```

## Статистика выполнения

### В конце выполнения логируется статистика

```
[2025-01-21 10:35:00] [INFO] [scraper] Scraping completed
Articles processed: 150
Successful: 147
Failed: 3
Warnings: 12
Total time: 4 minutes 32 seconds
Average time per article: 1.8 seconds
```

### Детальная статистика в verbose режиме

```
[2025-01-21 10:35:00] [DEBUG] [scraper] Detailed statistics:
- Cache hits: 23
- Cache misses: 127
- Network requests: 150
- Retry attempts: 8
- Memory usage peak: 245 MB
- Disk usage: 89 MB
```

## Настройка логирования

### Переменные окружения

```bash
# Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
LOG_LEVEL=INFO

# Максимальный размер файла лога (в байтах)
LOG_MAX_SIZE=10485760  # 10 MB

# Количество резервных копий
LOG_BACKUP_COUNT=5

# Включить цветной вывод в консоль
LOG_COLORED_OUTPUT=true
```

### Программная настройка

```python
from src.logger import setup_logger

# Настройка логгера
log_func = setup_logger(
    output_dir="out/cabinetdoc",
    verbose=True,
    console_output=True,
    log_level="DEBUG"
)

# Использование
log_func.info("Starting process...")
log_func.error("Something went wrong", extra={"url": "https://example.com"})
```

## Анализ логов

### Поиск ошибок

```bash
# Найти все ошибки
grep "ERROR" out/cabinetdoc/script_log.txt

# Найти ошибки конкретного типа
grep "TimeoutError" out/cabinetdoc/errors.log

# Статистика ошибок
grep -c "ERROR" out/cabinetdoc/script_log.txt
```

### Анализ производительности

```bash
# Время выполнения операций
grep "completed in" out/cabinetdoc/script_log.txt

# Статистика по статьям
grep "Article processed" out/cabinetdoc/script_log.txt | wc -l
```

### Мониторинг в реальном времени

```bash
# Следить за логами в реальном времени
tail -f out/cabinetdoc/script_log.txt

# Только ошибки
tail -f out/cabinetdoc/errors.log
```

## Типичные проблемы и решения

### Проблема: Слишком много DEBUG сообщений

**Решение:** Отключить verbose режим или изменить уровень логирования

```bash
# Обычный режим
python main.py https://its.1c.ru/db/cabinetdoc --format json

# Только ошибки
LOG_LEVEL=ERROR python main.py https://its.1c.ru/db/cabinetdoc --format json
```

### Проблема: Логи занимают много места

**Решение:** Настроить ротацию логов

```bash
# Уменьшить размер файла
LOG_MAX_SIZE=5242880  # 5 MB

# Уменьшить количество резервных копий
LOG_BACKUP_COUNT=3
```

### Проблема: Нет информации об ошибках

**Решение:** Проверить файл errors.log

```bash
# Проверить последние ошибки
tail -20 out/cabinetdoc/errors.log

# Найти критические ошибки
grep "CRITICAL" out/cabinetdoc/script_log.txt
```

## Интеграция с внешними системами

### Отправка логов в внешние системы

```python
import logging
from logging.handlers import SMTPHandler

# Настройка отправки ошибок по email
smtp_handler = SMTPHandler(
    mailhost='smtp.gmail.com',
    fromaddr='logger@example.com',
    toaddrs=['admin@example.com'],
    subject='Scraper Error'
)
smtp_handler.setLevel(logging.ERROR)

logger.addHandler(smtp_handler)
```

### Интеграция с системами мониторинга

```python
# Отправка метрик в Prometheus
from prometheus_client import Counter, Histogram

scraped_articles = Counter('scraped_articles_total', 'Total scraped articles')
scrape_duration = Histogram('scrape_duration_seconds', 'Time spent scraping')

# В коде скрапера
scraped_articles.inc()
scrape_duration.observe(time_taken)
```

## Лучшие практики

### 1. Используйте подходящий уровень логирования

```python
# Хорошо
log_func.info("Processing article: %s", article_title)
log_func.error("Failed to load page: %s", url, extra={"retry_count": retry_count})

# Плохо
log_func.debug("Processing article: %s", article_title)  # Слишком подробно
log_func.info("Failed to load page: %s", url)  # Должно быть ERROR
```

### 2. Добавляйте контекст к ошибкам

```python
# Хорошо
log_func.error(
    "Failed to parse article",
    extra={
        "url": url,
        "title": title,
        "parser": parser_name,
        "attempt": attempt_number
    }
)
```

### 3. Группируйте связанные операции

```python
# Начало операции
log_func.info("Starting batch processing of %d articles", len(articles))

# Прогресс
for i, article in enumerate(articles):
    log_func.debug("Processing article %d/%d: %s", i+1, len(articles), article.title)

# Завершение
log_func.info("Batch processing completed: %d successful, %d failed", success_count, fail_count)
```

### 4. Используйте структурированное логирование

```python
# JSON формат для машинного анализа
log_func.info(
    "Article processed",
    extra={
        "article_id": article.id,
        "processing_time": processing_time,
        "file_size": file_size,
        "format": output_format
    }
)
```
