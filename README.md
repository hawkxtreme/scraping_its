# Скраппер статей 1С ИТС

Этот скрипт предназначен для скрапинга статей с сайта its.1c.ru и сохранения их в различных форматах.

## Системные требования

* Python 3.8 или выше
* Docker 20.10 или выше (для browserless)
* Playwright (устанавливается через pip) + chromium browser (устанавливается отдельно через `playwright install`)
* Операционные системы:
  * Windows 10/11
  * Linux (Ubuntu 20.04+)
  * macOS 11+

## Условия использования

Вы можете использовать продукт только при соблюдении следующих условий:

* Материалы на ИТС, которые вы хотите скачать, являются бесплатными;
* Либо у вас оплачена подписка на ИТС на данный материал или продукт;
* На странице статей, которые вы скачиваете, активна кнопка "Печать".

## Установка

1. **Запустите Docker контейнер `browserless/chrome`:**
   Убедитесь, что у вас установлен Docker. Выполните команду:
   ```powershell
   docker run -p 3000:3000 browserless/chrome
   ```
   **Проверка работы контейнера:**
   После запуска откройте в браузере адрес [http://localhost:3000](http://localhost:3000). Должна открыться страница browserless с надписью "browserless is running". Если страница недоступна — проверьте, что контейнер запущен и порт 3000 открыт.
   Если вы используете другой адрес для `browserless`, укажите его в файле `.env`:
   ```
   BROWSERLESS_URL="http://ваш_адрес:порт"
   ```

2. **Клонируйте репозиторий (если необходимо):**
   ```powershell
   git clone https://github.com/hawkxtreme/scraping_its
   cd <папка репозитория>
   ```

3. **Создайте и активируйте виртуальное окружение:**
   ```powershell
   python -m venv venv
   venv\Scripts\activate      # Для Windows
   # Для Linux/macOS:
   # source venv/bin/activate
   pip install -r requirements.txt
   ```

4. **Создайте файл .env на основе примера:**
   ```powershell
   copy .env-example .env
   ```
   (В Linux/macOS используйте: `cp .env-example .env`)

5. **Настройте файл окружения:**
   *   Создайте файл `.env` в корневой папке проекта.
   *   Добавьте в него ваши учетные данные для входа на сайт 1С:
       ```
       LOGIN_1C_USER="ваш_логин"
       LOGIN_1C_PASSWORD="ваш_пароль"
       ```
       > **Важно:** Использование специальных символов в пароле может вызвать проблемы. Рекомендуется использовать пароли без специальных символов или экранировать их в файле .env, если это необходимо.

6. **Установите браузер для Playwright (требуется один раз):**
   ```powershell
   playwright install chromium
   ```


## Аргументы командной строки

Для получения справки по всем доступным командам используйте:

```bash
python main.py --help
# или
python main.py -h
```

Будет отображен список всех доступных аргументов и их описание.

Все доступные команды

```
usage: main.py [-h] [-f {json,pdf,txt,markdown} [{json,pdf,txt,markdown} ...]]
               [--no-scrape] [--force-reindex] [--update] 
               [-p PARALLEL] [--rag] [--limit LIMIT] [-v]
               [--timeout TIMEOUT] [--network-timeout NETWORK_TIMEOUT]
               [--retry-count RETRY_COUNT] [--retry-delay RETRY_DELAY]
               [--delay DELAY]
               url

Скраппинг статей с its.1c.ru.

positional arguments:
  url                   URL для скрапинга

options:
  -h, --help            показать это сообщение и выйти
  -f, --format {json,pdf,txt,markdown} [{json,pdf,txt,markdown} ...]
                        Форматы выходных файлов
  --no-scrape           Создать индекс без скрапинга статей
  --force-reindex       Принудительно обновить индекс статей
  --update              Обновить только изменённые статьи
  -p, --parallel PARALLEL
                        Количество параллельных потоков для скачивания
  --rag                 Добавить YAML frontmatter с breadcrumbs в markdown файлы
                        для RAG-систем
  --limit LIMIT         Ограничить количество скачиваемых статей (для тестирования)
  -v, --verbose         Включить подробное логирование (режим DEBUG)
  
  --timeout TIMEOUT     Таймаут загрузки страницы в секундах (по умолчанию: 90)
  --network-timeout NETWORK_TIMEOUT
                        Таймаут сетевых операций в секундах (по умолчанию: 60)
  --retry-count RETRY_COUNT
                        Количество повторных попыток при ошибках (по умолчанию: 3)
  --retry-delay RETRY_DELAY
                        Начальная задержка между повторными попытками в секундах (по умолчанию: 2.0)
  --delay DELAY         Задержка между запросами в секундах (по умолчанию: 0.5)
```

## Логирование

Проект использует продвинутую систему логирования с несколькими уровнями и возможностями:

### Файлы логов

В каждой выходной директории создаются следующие файлы логов:

*   **`script_log.txt`:** Основной лог файл со всеми событиями (INFO, WARNING, ERROR, CRITICAL)
    *   Ротация при достижении 10 МБ
    *   Сохраняется до 5 резервных копий
*   **`errors.log`:** Отдельный лог только для ошибок (ERROR и CRITICAL)
    *   Ротация при достижении 5 МБ
    *   Сохраняется до 3 резервных копий

### Уровни логирования

*   **DEBUG:** Подробная отладочная информация (доступна с флагом `--verbose`)
*   **INFO:** Общая информация о процессе
*   **WARNING:** Предупреждения (не критичные проблемы)
*   **ERROR:** Ошибки, не приводящие к остановке процесса
*   **CRITICAL:** Критические ошибки

### Verbose режим

Используйте флаг `-v` или `--verbose` для включения подробного логирования:

```bash
python main.py https://its.1c.ru/db/cabinetdoc --format json -v
```

В verbose режиме вы получите:
*   Подробную информацию о каждом шаге
*   URL-адреса загружаемых страниц
*   Информацию о парсерах
*   Время выполнения операций
*   Детали обработки каждой статьи

### Контекстное логирование ошибок

Система автоматически добавляет контекст к ошибкам:
*   URL проблемной страницы
*   Название статьи
*   Тип операции
*   Stack trace
*   Предложения по исправлению типичных проблем

### Статистика

В конце выполнения логируется статистика:
*   Количество ошибок
*   Количество предупреждений
*   Количество успешно обработанных статей

## Настройка таймаутов и повторных попыток

Проект поддерживает гибкую настройку таймаутов и механизма повторных попыток для адаптации к различным сетевым условиям.

### Доступные параметры

*   **`--timeout SECONDS`** - Таймаут загрузки страницы (по умолчанию: 90 секунд)
    *   Диапазон: 10-300 секунд
    *   Рекомендуется увеличить при медленном соединении
    
*   **`--network-timeout SECONDS`** - Таймаут сетевых операций (по умолчанию: 60 секунд)
    *   Диапазон: 5-180 секунд
    *   Используется для wait_for_load_state и подобных операций
    
*   **`--retry-count COUNT`** - Количество повторных попыток (по умолчанию: 3)
    *   Диапазон: 0-10
    *   0 = без повторных попыток
    *   Рекомендуется 3-5 для нестабильных соединений
    
*   **`--retry-delay SECONDS`** - Начальная задержка между попытками (по умолчанию: 2.0 секунды)
    *   Диапазон: 0.1-60 секунд
    *   Используется экспоненциальная задержка (backoff)
    
*   **`--delay SECONDS`** - Задержка между запросами (по умолчанию: 0.5 секунды)
    *   Диапазон: 0-10 секунд
    *   Помогает избежать перегрузки сервера

### Примеры использования

**Для медленного соединения:**
```bash
python main.py https://its.1c.ru/db/cabinetdoc --format json \
  --timeout 180 --network-timeout 120 --retry-count 5
```

**Для быстрого соединения:**
```bash
python main.py https://its.1c.ru/db/cabinetdoc --format json \
  --timeout 30 --network-timeout 20 --retry-count 2 --delay 0.2
```

**Без повторных попыток (для отладки):**
```bash
python main.py https://its.1c.ru/db/cabinetdoc --format json --retry-count 0
```

**Агрессивная обработка (максимальная скорость):**
```bash
python main.py https://its.1c.ru/db/cabinetdoc --format json \
  --timeout 45 --delay 0.1 --retry-count 2 -p 8
```

### Механизм повторных попыток

Проект использует **экспоненциальную задержку (exponential backoff)** для повторных попыток:

*   **Попытка 1:** Задержка = retry-delay × 2⁰ = 2 секунды
*   **Попытка 2:** Задержка = retry-delay × 2¹ = 4 секунды
*   **Попытка 3:** Задержка = retry-delay × 2² = 8 секунд

Это помогает избежать перегрузки сервера и увеличивает шансы на успех при временных сбоях.

### Рекомендации

**Стабильное подключение:**
```bash
--timeout 60 --retry-count 2 --delay 0.3
```

**Нестабильное подключение:**
```bash
--timeout 120 --retry-count 5 --retry-delay 3 --delay 1
```

**Очень медленное подключение:**
```bash
--timeout 180 --network-timeout 120 --retry-count 5 --retry-delay 5 --delay 2
```

## Выходные файлы

Помимо папок с файлами статей, в корневой директории `out` создаются два файла оглавления:

*   **`_toc.md`:** Иерархическое оглавление в формате Markdown для удобной навигации по скачанным статьям. Структура оглавления повторяет структуру сайта.
*   **`_meta.json`:** Файл с метаданными всех статей в формате JSON. Содержит информацию о заголовках, URL, "хлебных крошках" (breadcrumb - иерархическая навигация), хешах содержимого и именах файлов. Этот файл предназначен для использования в других системах, например, для загрузки в RAG-модели.

### RAG-режим для Markdown файлов

При использовании флага `--rag` каждый markdown файл будет содержать YAML frontmatter в начале с метаданными:

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

Это позволяет RAG-системам (Retrieval-Augmented Generation) лучше понимать контекст документа и его положение в иерархии документации, что значительно улучшает качество ответов AI-систем при работе с документацией.

## Поддерживаемые форматы

* **JSON** (.json)
  * Полные метаданные статьи
  * Структурированный контент
  * Сохранение ссылок и связей

* **PDF** (.pdf)
  * Точное отображение как на сайте
  * Сохранение форматирования
  * Поддержка изображений и таблиц

* **TXT** (.txt)
  * Чистый текст без форматирования
  * Компактный размер
  * Легко индексируется

* **Markdown** (.md)
  * Сохранение базового форматирования
  * Поддержка заголовков и списков
  * Удобно для просмотра на GitHub
  * **RAG-режим** (флаг `--rag`): добавляет YAML frontmatter с метаданными:
    * `breadcrumb` - иерархическая навигация ("хлебные крошки")
    * `content_hash` - хеш содержимого для отслеживания изменений
    * `title` - заголовок статьи
    * `url` - исходный URL статьи

## Примеры использования

* Скрапинг всего раздела в форматах JSON, PDF, TXT, MARKDOWN:
```bash
python main.py https://its.1c.ru/db/erp25ltsdoc --format json pdf txt markdown
```

* Скрапинг первых 5 статей для тестирования:
```bash
python main.py https://its.1c.ru/db/erp25ltsdoc --limit 5
```

* Скрапинг всего раздела в формате PDF с использованием 8 потоков:
```bash
python main.py https://its.1c.ru/db/erp25ltsdoc --format pdf -p 8
```

* Создание индекса без скрапинга:
```bash
python main.py https://its.1c.ru/db/erp25ltsdoc --no-scrape
```

* Принудительное обновление индекса:
```bash
python main.py https://its.1c.ru/db/erp25ltsdoc --force-reindex
```

* Обновление только изменённых статей:
```bash
python main.py https://its.1c.ru/db/erp25ltsdoc --update
```

* Обновление статей из раздела cabinetdoc:
```bash
python main.py https://its.1c.ru/db/cabinetdoc --update --format json pdf txt markdown
```

* Скрапинг в формате Markdown с метаданными для RAG-систем:
```bash
python main.py https://its.1c.ru/db/erp25ltsdoc --format markdown --rag
```

* Скрапинг во всех форматах с RAG-метаданными в Markdown:
```bash
python main.py https://its.1c.ru/db/cabinetdoc --format json pdf txt markdown --rag
```

* Тестовый запуск: скрапинг первых 3 статей в markdown с RAG-метаданными:
```bash
python main.py https://its.1c.ru/db/erp25ltsdoc --format markdown --rag --limit 3
```

* Скрапинг с подробным логированием (verbose режим):
```bash
python main.py https://its.1c.ru/db/cabinetdoc --format pdf -v
```

* Скрапинг с параллельной обработкой и подробным логированием:
```bash
python main.py https://its.1c.ru/db/erp25ltsdoc --format json markdown -p 4 -v
```

* Скрапинг с увеличенными таймаутами для медленного соединения:
```bash
python main.py https://its.1c.ru/db/cabinetdoc --format pdf --timeout 180 --retry-count 5
```

* Быстрый скрапинг с минимальными задержками:
```bash
python main.py https://its.1c.ru/db/cabinetdoc --format json --timeout 45 --delay 0.1 -p 8
```

* Отладка без повторных попыток:
```bash
python main.py https://its.1c.ru/db/cabinetdoc --format json --retry-count 0 -v
```

## Тестирование

### Запуск всех тестов

```bash
python -m pytest
```

### Запуск сценарных тестов

```bash
# Запуск всех сценарных тестов
python -m pytest tests/test_scenario.py -v

# Запуск с выводом команды в терминале (как при обычном режиме работы)
python -m pytest tests/test_scenario.py -v -s

# Запуск только сценарных тестов с маркером
python -m pytest -m scenario -v -s

# Запуск конкретного сценарного теста
python -m pytest tests/test_scenario.py::test_cabinetdoc_scenario_all_formats -v -s

# Запуск с коротким traceback
python -m pytest tests/test_scenario.py -v -s --tb=short
```

### Доступные сценарные тесты

1. `test_cabinetdoc_scenario_all_formats` - тестирование всех форматов вывода
2. `test_cabinetdoc_scenario_limit` - тестирование ограничения количества статей
3. `test_cabinetdoc_scenario_rag_mode` - проверка RAG-режима с YAML frontmatter
4. `test_cabinetdoc_scenario_no_scrape` - тест режима без скрапинга (только индекс)
5. `test_v8std_scenario_parser_v2` - тестирование parser_v2 для v8std
6. `test_cabinetdoc_scenario_parallel` - проверка параллельной обработки
7. `test_cabinetdoc_scenario_update_mode` - тест режима обновления
8. `test_cabinetdoc_scenario_force_reindex` - проверка принудительного переиндексирования
9. `test_cabinetdoc_scenario_single_format` - тест одного формата вывода (PDF)
10. `test_cabinetdoc_scenario_multiple_formats` - тест множественных форматов
11. `test_cabinetdoc_scenario_metadata_validation` - проверка корректности метаданных
12. `test_cabinetdoc_scenario_toc_validation` - проверка корректности создания оглавления

## Структура проекта

Проект организован в модульной архитектуре:

* `main.py` - точка входа в приложение
* `src/` - основной код приложения:
  * `scraper.py` - логика скрапинга с использованием Playwright
  * `parser.py`, `parser_v1.py`, `parser_v2.py` - модули парсинга контента (выбор парсера зависит от URL)
  * `config.py` - конфигурация, управление зависимостями и таймаутами
  * `file_manager.py` - работа с файлами и создание оглавления
  * `logger.py` - продвинутая система логирования
  * `utils.py` - утилиты (retry декораторы, exponential backoff)
  * `ui.py` - пользовательский интерфейс (вывод в консоль)
* `out/` - папка с результатами скрапинга
* `tests/` - тесты

### Особенности Parser V2 (для v8std и подобных)

Parser V2 использует **рекурсивный обход статей**:
- Получает начальное оглавление
- Посещает каждую статью и извлекает вложенные ссылки
- Рекурсивно обходит найденные ссылки до глубины 3 уровней
- Для v8std это позволяет обнаружить ~333 статьи вместо 14 в оглавлении

Пример: `python main.py https://its.1c.ru/db/v8std --format markdown --rag --limit 50 -p 4`

## Roadmap

### ✅ Выполнено

* ✅ **Улучшение логирования и информативности ошибок** (v1.1.0)
  * Стандартный модуль logging с уровнями DEBUG/INFO/WARNING/ERROR/CRITICAL
  * Ротация логов и отдельный файл ошибок
  * Verbose режим (`--verbose` / `-v`)
  * Контекстное логирование с автоматическими подсказками
  * Цветной вывод в консоль

* ✅ **Поддержка консольных аргументов для настройки таймаутов и ограничений** (v1.2.0)
  * Настраиваемые таймауты (`--timeout`, `--network-timeout`)
  * Механизм повторных попыток (`--retry-count`, `--retry-delay`)
  * Настраиваемая задержка между запросами (`--delay`)
  * Exponential backoff при retry
  * Валидация параметров

* ✅ **Добавление режима обновления существующих файлов** (v1.0.0)
  * Флаг `--update` для обновления только измененных статей
  * Проверка хешей контента

### 🔄 В процессе разработки

* 🔄 **Система кэширования для ускорения повторной загрузки**
  * Приоритет: Высокий

* 🔄 **Дальнейшая оптимизация параллельной индексации**
  * Приоритет: Высокий

### 📋 Запланировано

* 📋 **Расширение возможностей фильтрации и выбора статей для выгрузки**
  * Фильтры по заголовкам, URL, глубине вложенности
  * Режим preview (`--dry-run`)
  * Экспорт индекса в JSON/CSV

* 📋 **Поддержка формата DOCX**
  * Конвертация в формат Microsoft Word
  * Сохранение форматирования, таблиц, изображений
  * Библиотека python-docx
---

## Лицензия

Данный проект распространяется под лицензией MIT.

**MIT License**

Copyright (c) 2025

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
