# Продвинутое использование

## Настройка таймаутов и повторных попыток

### Доступные параметры

| Параметр | Описание | По умолчанию | Диапазон |
|----------|----------|--------------|----------|
| `--timeout` | Таймаут загрузки страницы | 90 сек | 10-300 сек |
| `--network-timeout` | Таймаут сетевых операций | 60 сек | 5-180 сек |
| `--retry-count` | Количество повторных попыток | 3 | 0-10 |
| `--retry-delay` | Начальная задержка между попытками | 2.0 сек | 0.1-60 сек |
| `--delay` | Задержка между запросами | 0.5 сек | 0-10 сек |

### Примеры конфигураций

#### Стабильное подключение
```bash
python main.py https://its.1c.ru/db/cabinetdoc \
  --timeout 60 --retry-count 2 --delay 0.3
```

#### Нестабильное подключение
```bash
python main.py https://its.1c.ru/db/cabinetdoc \
  --timeout 120 --retry-count 5 --retry-delay 3 --delay 1
```

#### Очень медленное подключение
```bash
python main.py https://its.1c.ru/db/cabinetdoc \
  --timeout 180 --network-timeout 120 --retry-count 5 --retry-delay 5 --delay 2
```

#### Агрессивная обработка (максимальная скорость)
```bash
python main.py https://its.1c.ru/db/cabinetdoc \
  --timeout 45 --delay 0.1 --retry-count 2 --parallel 8
```

### Механизм повторных попыток

Проект использует **экспоненциальную задержку (exponential backoff)**:

- **Попытка 1:** Задержка = retry-delay × 2⁰ = 2 секунды
- **Попытка 2:** Задержка = retry-delay × 2¹ = 4 секунды  
- **Попытка 3:** Задержка = retry-delay × 2² = 8 секунд

## Параллельная обработка

### Оптимальные настройки

| Количество статей | Рекомендуемые потоки | Таймаут |
|-------------------|---------------------|---------|
| < 50 | 2-3 | 60 сек |
| 50-200 | 4-6 | 90 сек |
| 200-500 | 6-8 | 120 сек |
| > 500 | 8-12 | 150 сек |

### Мониторинг производительности

```bash
# С подробным логированием для анализа
python main.py https://its.1c.ru/db/cabinetdoc \
  --parallel 4 --verbose --format json
```

## Режимы работы

### Режим обновления (`--update`)

Обновляет только статьи, которые изменились с последнего запуска:

```bash
# Первый запуск - скачивает все
python main.py https://its.1c.ru/db/cabinetdoc --format json pdf

# Второй запуск - обновляет только измененные
python main.py https://its.1c.ru/db/cabinetdoc --update --format json pdf
```

### Принудительная переиндексация (`--force-reindex`)

Принудительно пересоздает индекс статей:

```bash
python main.py https://its.1c.ru/db/cabinetdoc --force-reindex
```

### Режим без скрапинга (`--no-scrape`)

Создает только индекс без скачивания контента:

```bash
python main.py https://its.1c.ru/db/cabinetdoc --no-scrape
```

## RAG-режим

### Что такое RAG-режим

RAG (Retrieval-Augmented Generation) - режим для AI-систем, который добавляет в markdown файлы YAML frontmatter с метаданными:

```yaml
---
breadcrumb:
- Главная страница
- Раздел  
- Подраздел
- Название статьи
content_hash: -5153820738866779120
title: Название статьи
url: https://its.1c.ru/db/example
---
```

### Использование RAG-режима

```bash
# Markdown с метаданными для RAG
python main.py https://its.1c.ru/db/cabinetdoc --format markdown --rag

# Все форматы + RAG метаданные в markdown
python main.py https://its.1c.ru/db/cabinetdoc \
  --format json pdf txt markdown --rag
```

## Специальные парсеры

### Parser V2 для v8std

Для разделов типа `v8std` используется специальный парсер с рекурсивным обходом:

```bash
# Автоматически обнаруживает ~333 статьи вместо 14 в оглавлении
python main.py https://its.1c.ru/db/v8std --format markdown --rag --limit 50
```

**Особенности Parser V2:**
- Рекурсивный обход статей до глубины 3 уровней
- Автоматическое обнаружение вложенных ссылок
- Значительно больше статей чем в базовом оглавлении

## Оптимизация производительности

### Рекомендации по настройке

1. **Для SSD дисков:** используйте больше параллельных потоков
2. **Для медленного интернета:** увеличьте таймауты и задержки
3. **Для больших объемов:** используйте режим `--update` для повторных запусков

### Мониторинг ресурсов

```bash
# Мониторинг в реальном времени (Linux/macOS)
watch -n 1 'ps aux | grep python'

# Проверка использования диска
du -sh out/
```

## Устранение неполадок

### Частые проблемы

#### Таймауты
```bash
# Увеличить таймауты
python main.py https://its.1c.ru/db/cabinetdoc \
  --timeout 180 --network-timeout 120 --retry-count 5
```

#### Проблемы с браузером
```bash
# Переустановить браузер Playwright
playwright install chromium --force
```

#### Ошибки аутентификации
- Проверьте файл `.env` с учетными данными
- Убедитесь, что пароль не содержит специальных символов
- Проверьте доступность сайта its.1c.ru

#### Проблемы с Docker
```bash
# Проверить статус контейнера
docker ps

# Перезапустить контейнер
docker restart $(docker ps -q --filter ancestor=browserless/chrome)
```

### Отладка

```bash
# Максимально подробное логирование
python main.py https://its.1c.ru/db/cabinetdoc \
  --verbose --retry-count 0 --limit 1
```

## Интеграция с другими системами

### Автоматизация через скрипты

#### Bash скрипт для регулярного обновления
```bash
#!/bin/bash
cd /path/to/scraping_its
source venv/bin/activate
python main.py https://its.1c.ru/db/cabinetdoc --update --format json pdf
```

#### PowerShell скрипт для Windows
```powershell
Set-Location "C:\path\to\scraping_its"
.\venv\Scripts\Activate.ps1
python main.py https://its.1c.ru/db/cabinetdoc --update --format json pdf
```

### Интеграция с CI/CD

#### GitHub Actions
```yaml
name: Update Documentation
on:
  schedule:
    - cron: '0 2 * * 1'  # Каждый понедельник в 2:00

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          playwright install chromium
      - name: Run scraper
        run: |
          python main.py https://its.1c.ru/db/cabinetdoc --update --format json pdf
        env:
          LOGIN_1C_USER: ${{ secrets.LOGIN_1C_USER }}
          LOGIN_1C_PASSWORD: ${{ secrets.LOGIN_1C_PASSWORD }}
```
