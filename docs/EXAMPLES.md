# Примеры использования

## Базовые сценарии

### Скачивание всего раздела

```bash
# Все форматы
python main.py https://its.1c.ru/db/cabinetdoc --format json pdf txt markdown

# Только JSON для быстрого тестирования
python main.py https://its.1c.ru/db/cabinetdoc --format json

# Только PDF для печати
python main.py https://its.1c.ru/db/cabinetdoc --format pdf
```

### Тестовые запуски

```bash
# Первые 5 статей для проверки
python main.py https://its.1c.ru/db/cabinetdoc --limit 5

# Первые 10 статей в markdown
python main.py https://its.1c.ru/db/cabinetdoc --format markdown --limit 10

# Тест с подробным логированием
python main.py https://its.1c.ru/db/cabinetdoc --limit 3 --verbose
```

## Режимы работы

### Режим обновления

```bash
# Первый запуск - скачивает все
python main.py https://its.1c.ru/db/cabinetdoc --format json pdf

# Последующие запуски - только измененные
python main.py https://its.1c.ru/db/cabinetdoc --update --format json pdf

# Принудительное обновление всех статей
python main.py https://its.1c.ru/db/cabinetdoc --update --force-reindex
```

### Создание индекса без скачивания

```bash
# Только создать индекс статей
python main.py https://its.1c.ru/db/cabinetdoc --no-scrape

# Проверить что будет скачано
python main.py https://its.1c.ru/db/cabinetdoc --no-scrape --verbose
```

## Параллельная обработка

### Оптимальные настройки по объему

```bash
# Небольшой раздел (< 50 статей)
python main.py https://its.1c.ru/db/cabinetdoc --parallel 2 --format json

# Средний раздел (50-200 статей)
python main.py https://its.1c.ru/db/cabinetdoc --parallel 4 --format json pdf

# Большой раздел (200+ статей)
python main.py https://its.1c.ru/db/cabinetdoc --parallel 8 --format json pdf markdown
```

### Агрессивная обработка

```bash
# Максимальная скорость (осторожно с сервером!)
python main.py https://its.1c.ru/db/cabinetdoc \
  --parallel 8 --timeout 45 --delay 0.1 --retry-count 2
```

## RAG-режим для AI систем

### Базовое использование

```bash
# Markdown с метаданными для RAG
python main.py https://its.1c.ru/db/cabinetdoc --format markdown --rag

# Все форматы + RAG метаданные в markdown
python main.py https://its.1c.ru/db/cabinetdoc \
  --format json pdf txt markdown --rag
```

### Тестирование RAG-режима

```bash
# Тест RAG с ограничением
python main.py https://its.1c.ru/db/cabinetdoc \
  --format markdown --rag --limit 5 --verbose
```

## Настройка таймаутов

### Стабильное соединение

```bash
# Быстрая обработка
python main.py https://its.1c.ru/db/cabinetdoc \
  --timeout 60 --retry-count 2 --delay 0.3 --format json
```

### Медленное соединение

```bash
# Увеличенные таймауты
python main.py https://its.1c.ru/db/cabinetdoc \
  --timeout 180 --network-timeout 120 --retry-count 5 --delay 2 --format json
```

### Очень нестабильное соединение

```bash
# Максимальные таймауты
python main.py https://its.1c.ru/db/cabinetdoc \
  --timeout 300 --network-timeout 180 --retry-count 8 --retry-delay 5 --delay 3
```

## Отладка и диагностика

### Подробное логирование

```bash
# Максимально подробный вывод
python main.py https://its.1c.ru/db/cabinetdoc \
  --verbose --limit 1 --format json
```

### Отладка без повторных попыток

```bash
# Быстрая диагностика проблем
python main.py https://its.1c.ru/db/cabinetdoc \
  --retry-count 0 --verbose --limit 1
```

### Проверка конкретной статьи

```bash
# Если знаете URL конкретной статьи
python main.py https://its.1c.ru/db/cabinetdoc/specific-article \
  --format json --verbose
```

## Специальные разделы

### Parser V2 для v8std

```bash
# Автоматический рекурсивный обход
python main.py https://its.1c.ru/db/v8std --format markdown --rag --limit 50

# Полный обход с параллельной обработкой
python main.py https://its.1c.ru/db/v8std \
  --format json pdf markdown --rag --parallel 4
```

### ERP документация

```bash
# Большой раздел ERP
python main.py https://its.1c.ru/db/erp25ltsdoc \
  --format json pdf txt markdown --parallel 6

# Обновление ERP документации
python main.py https://its.1c.ru/db/erp25ltsdoc \
  --update --format json pdf --parallel 4
```

## Автоматизация

### Bash скрипт для регулярного обновления

```bash
#!/bin/bash
# update_docs.sh

cd /path/to/scraping_its
source venv/bin/activate

echo "Updating cabinetdoc..."
python main.py https://its.1c.ru/db/cabinetdoc --update --format json pdf

echo "Updating erp25ltsdoc..."
python main.py https://its.1c.ru/db/erp25ltsdoc --update --format json pdf

echo "Update completed!"
```

### PowerShell скрипт для Windows

```powershell
# update_docs.ps1

Set-Location "C:\path\to\scraping_its"
.\venv\Scripts\Activate.ps1

Write-Host "Updating cabinetdoc..."
python main.py https://its.1c.ru/db/cabinetdoc --update --format json pdf

Write-Host "Updating erp25ltsdoc..."
python main.py https://its.1c.ru/db/erp25ltsdoc --update --format json pdf

Write-Host "Update completed!"
```

### Cron задача (Linux/macOS)

```bash
# Добавить в crontab (crontab -e)
# Обновление каждый понедельник в 2:00
0 2 * * 1 cd /path/to/scraping_its && ./update_docs.sh
```

## Интеграция с CI/CD

### GitHub Actions

```yaml
name: Update Documentation
on:
  schedule:
    - cron: '0 2 * * 1'  # Каждый понедельник в 2:00
  workflow_dispatch:  # Ручной запуск

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
          
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          playwright install chromium
          
      - name: Update cabinetdoc
        run: |
          python main.py https://its.1c.ru/db/cabinetdoc \
            --update --format json pdf --parallel 4
        env:
          LOGIN_1C_USER: ${{ secrets.LOGIN_1C_USER }}
          LOGIN_1C_PASSWORD: ${{ secrets.LOGIN_1C_PASSWORD }}
          
      - name: Commit changes
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add out/
          git commit -m "Update documentation" || exit 0
          git push
```

## Мониторинг и алерты

### Скрипт проверки статуса

```bash
#!/bin/bash
# check_status.sh

LOG_FILE="out/cabinetdoc/errors.log"
ERROR_COUNT=$(grep -c "ERROR" "$LOG_FILE" 2>/dev/null || echo "0")

if [ "$ERROR_COUNT" -gt 10 ]; then
    echo "ALERT: Too many errors ($ERROR_COUNT) in last run"
    # Отправить уведомление
    mail -s "Scraper Alert" admin@example.com < "$LOG_FILE"
fi
```

### Мониторинг размера результатов

```bash
#!/bin/bash
# monitor_size.sh

OUTPUT_DIR="out/cabinetdoc"
SIZE_MB=$(du -sm "$OUTPUT_DIR" | cut -f1)

if [ "$SIZE_MB" -gt 1000 ]; then
    echo "WARNING: Output directory is large ($SIZE_MB MB)"
fi
```

## Устранение неполадок

### Проблема: Таймауты

```bash
# Диагностика
python main.py https://its.1c.ru/db/cabinetdoc \
  --timeout 30 --retry-count 0 --limit 1 --verbose

# Решение
python main.py https://its.1c.ru/db/cabinetdoc \
  --timeout 180 --retry-count 5 --delay 2
```

### Проблема: Ошибки аутентификации

```bash
# Проверка учетных данных
python main.py https://its.1c.ru/db/cabinetdoc \
  --no-scrape --verbose

# Если проблема в пароле с спецсимволами
# Попробуйте изменить пароль или экранировать символы в .env
```

### Проблема: Нехватка памяти

```bash
# Уменьшить параллелизм
python main.py https://its.1c.ru/db/cabinetdoc \
  --parallel 2 --format json

# Обработать по частям
python main.py https://its.1c.ru/db/cabinetdoc \
  --limit 50 --format json
```

## Экспорт и интеграция

### Экспорт индекса

```bash
# Создать только индекс
python main.py https://its.1c.ru/db/cabinetdoc --no-scrape

# Использовать индекс для других целей
cat out/cabinetdoc/_meta.json | jq '.articles[] | {title, url}'
```

### Интеграция с поисковыми системами

```bash
# Подготовить данные для Elasticsearch
python main.py https://its.1c.ru/db/cabinetdoc \
  --format json --rag

# Конвертировать в формат для поиска
jq -r '.articles[] | {title, content, url, breadcrumb}' \
  out/cabinetdoc/json/*.json > search_index.json
```

### Интеграция с системами документации

```bash
# Markdown для GitBook/GitLab Pages
python main.py https://its.1c.ru/db/cabinetdoc \
  --format markdown --rag

# PDF для печати и архивации
python main.py https://its.1c.ru/db/cabinetdoc \
  --format pdf
```
