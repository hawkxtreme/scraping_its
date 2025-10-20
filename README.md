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
               [-p PARALLEL] [--rag] [--limit LIMIT]
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

## Структура проекта

Проект организован в модульной архитектуре:

* `main.py` - точка входа в приложение
* `src/` - основной код приложения:
  * `scraper.py` - логика скрапинга с использованием Playwright
  * `parser.py`, `parser_v1.py`, `parser_v2.py` - модули парсинга контента (выбор парсера зависит от URL)
  * `config.py` - конфигурация и управление зависимостями
  * `file_manager.py` - работа с файлами и создание оглавления
  * `logger.py` - логирование
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

* Улучшение логирования и информативности ошибок
* Поддержка формата DOCX
* Дальнейшая оптимизация параллельной индексации
* Система кэширования для ускорения повторной загрузки
* Поддержка консольных аргументов для настройки таймаутов и ограничений
* Добавление режима обновления существующих файлов
* Расширение возможностей фильтрации и выбора статей для выгрузки
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
