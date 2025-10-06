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
usage: main.py [-h] [-c CHAPTER]
               [-f {json,pdf,txt,markdown,docx} [{json,pdf,txt,markdown,docx} ...]]
               [--no-scrape] [--force-reindex] [-p PARALLEL]
               [--use-cache] [--clear-cache] [--cache-stats]
               [--page-timeout PAGE_TIMEOUT] [--login-timeout LOGIN_TIMEOUT]
               [--network-idle-timeout NETWORK_IDLE_TIMEOUT] [--worker-timeout WORKER_TIMEOUT]
               [--request-delay REQUEST_DELAY] [--max-retries MAX_RETRIES] [--retry-delay RETRY_DELAY]
               [--filter-by-title FILTER_BY_TITLE] [--exclude-by-title EXCLUDE_BY_TITLE]
               [--max-articles MAX_ARTICLES] [--skip-first SKIP_FIRST] [--random-sample RANDOM_SAMPLE]
               url

Скраппинг статей с its.1c.ru.

positional arguments:
  url                   URL для скрапинга

options:
  -h, --help            показать это сообщение и выйти
  -c, --chapter CHAPTER
                        Название главы для выборочного скрапинга
  -f, --format {json,pdf,txt,markdown,docx} [{json,pdf,txt,markdown,docx} ...]
                         Форматы выходных файлов
  --no-scrape           Создать индекс без скрапинга статей
  --force-reindex       Принудительно обновить индекс статей
  -p, --parallel PARALLEL
                         Количество параллельных потоков для скачивания
  --use-cache            Использовать кэширование для ускорения повторных загрузок
  --clear-cache          Очистить кэш перед началом работы
  --cache-stats          Показать статистику кэша и выйти
  --page-timeout PAGE_TIMEOUT
                        Таймаут загрузки страницы в миллисекундах (по умолчанию: 90000)
  --login-timeout LOGIN_TIMEOUT
                        Таймаут входа в миллисекундах (по умолчанию: 60000)
  --network-idle-timeout NETWORK_IDLE_TIMEOUT
                        Таймаут ожидания сети в миллисекундах (по умолчанию: 30000)
  --worker-timeout WORKER_TIMEOUT
                        Таймаут операции воркера в секундах (по умолчанию: 300)
  --request-delay REQUEST_DELAY
                        Задержка между запросами в секундах (по умолчанию: 0.5)
  --max-retries MAX_RETRIES
                        Максимальное количество попыток для неудачных запросов (по умолчанию: 3)
  --retry-delay RETRY_DELAY
                        Задержка между повторными попытками в секундах (по умолчанию: 2.0)
  --filter-by-title FILTER_BY_TITLE
                        Фильтровать статьи по заголовку (содержит эту строку)
  --exclude-by-title EXCLUDE_BY_TITLE
                        Исключить статьи по заголовку (содержит эту строку)
  --max-articles MAX_ARTICLES
                        Максимальное количество статей для выгрузки
  --skip-first SKIP_FIRST
                        Пропустить первые N статей (по умолчанию: 0)
  --random-sample RANDOM_SAMPLE
                        Случайно выбрать N статей
```

## Выходные файлы

Помимо папок с файлами статей, в корневой директории `out` создаются два файла оглавления:

*   **`_toc.md`:** Иерархическое оглавление в формате Markdown для удобной навигации по скачанным статьям. Структура оглавления повторяет структуру сайта.
*   **`_meta.json`:** Файл с метаданными всех статей в формате JSON. Содержит информацию о заголовках, URL, "хлебных крошках" (иерархия) и именах файлов. Этот файл предназначен для использования в других системах, например, для загрузки в RAG-модели.

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

* **DOCX** (.docx)
  * Форматированный документ Microsoft Word
  * Сохранение структуры документа
  * Поддержка таблиц, списков и заголовков
  * Требует установки библиотеки python-docx

## Примеры использования

* Скрапинг всего раздела в форматах JSON, PDF, TXT, MARKDOWN, DOCX:
```bash
python main.py https://its.1c.ru/db/erp25ltsdoc --format json pdf txt markdown docx
```

* Скрапинг только одной главы во всех форматах:
```bash
python main.py https://its.1c.ru/db/erp25ltsdoc --chapter "Описание отдельных учетных задач"
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
python main.py https://its.1c.ru/db/cabinetdoc --update --format json pdf txt markdown docx
```

* Использование кэширования для ускорения повторных загрузок:
```bash
python main.py https://its.1c.ru/db/erp25ltsdoc --format json pdf txt markdown docx --use-cache
```

* Очистка кэша:
```bash
python main.py https://its.1c.ru/db/erp25ltsdoc --clear-cache
```

* Просмотр статистики кэша:
```bash
python main.py --cache-stats
```

* Настройка таймаутов для медленного соединения:
```bash
python main.py https://its.1c.ru/db/erp25ltsdoc --page-timeout 120000 --login-timeout 90000
```

* Увеличение задержки между запросами для снижения нагрузки на сервер:
```bash
python main.py https://its.1c.ru/db/erp25ltsdoc --request-delay 1.0 --max-retries 5
```

* Фильтрация статей по заголовку:
```bash
python main.py https://its.1c.ru/db/erp25ltsdoc --filter-by-title "Отчеты" --format json pdf txt
```

* Исключение статей по заголовку и ограничение количества:
```bash
python main.py https://its.1c.ru/db/erp25ltsdoc --exclude-by-title "Архив" --max-articles 50
```

* Случайная выборка статей для тестирования:
```bash
python main.py https://its.1c.ru/db/erp25ltsdoc --random-sample 10 --format json
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

## Кэширование

Скрапер поддерживает систему кэширования для ускорения повторных загрузок:

* Кэширование содержимого статей в указанных форматах
* Автоматическая проверка изменений контента по хэшу
* Управление размером кэша с автоматической очисткой старых записей
* Статистика использования кэша

Кэш хранится в папке `.cache` внутри выходной директории и автоматически очищается при превышении лимита размера (по умолчанию 500MB) или при устаревании записей (по умолчанию 7 дней).

## Настройка производительности

Скрапер предоставляет различные параметры для настройки производительности:

* **Таймауты**: Настраиваемые таймауты для загрузки страниц, входа и операций воркеров
* **Ограничение скорости**: Задержки между запросами и управление повторными попытками
* **Параллельная обработка**: Настройка количества параллельных потоков
* **Кэширование**: Управление кэшированием для ускорения повторных загрузок

Эти параметры особенно полезны при работе с медленными соединениями или при необходимости снизить нагрузку на сервер.

## Roadmap

* ~~Улучшение логирования и информативности ошибок~~ ✅
* ~~Поддержка формата DOCX~~ ✅
* ~~Дальнейшая оптимизация параллельной индексации~~ ✅
* ~~Система кэширования для ускорения повторной загрузки~~ ✅
* ~~Поддержка консольных аргументов для настройки таймаутов и ограничений~~ ✅
* ~~Добавление режима обновления существующих файлов~~ ✅
* ~~Расширение возможностей фильтрации и выбора статей для выгрузки~~ ✅

## Тестирование улучшений

Для проверки всех внесенных улучшений создан специальный тестовый скрипт `test_improvements.py`.

### Запуск тестов

Для запуска всех тестов выполните команду:

```bash
python test_improvements.py
```

### Что проверяют тесты

Тестовый скрипт проверяет следующие улучшения:

1. **Улучшенное логирование и информативность ошибок**
   - Проверка работы логирования в отладочном режиме
   - Проверка создания лог-файла

2. **Поддержка формата DOCX**
   - Проверка сохранения статей в формате DOCX
   - Проверка наличия созданных DOCX файлов

3. **Оптимизация параллельной индексации**
   - Проверка работы с несколькими параллельными потоками
   - Проверка корректности распределения задач

4. **Система кэширования**
   - Проверка сохранения в кэш
   - Проверка статистики кэша
   - Проверка извлечения из кэша при повторном запуске

5. **Консольные аргументы для настройки таймаутов и ограничений**
   - Проверка настройки таймаутов
   - Проверка настройки задержек между запросами
   - Проверка настройки количества повторных попыток

6. **Режим обновления существующих файлов**
   - Проверка создания индекса
   - Проверка обновления только измененных статей

7. **Расширение возможностей фильтрации и выбора статей**
   - Проверка фильтрации по заголовку
   - Проверка исключения по заголовку
   - Проверка случайной выборки статей

### Ожидаемые результаты

При успешном прохождении всех тестов вы должны увидеть сообщение:

```
🎉 ВСЕ ТЕСТЫ УСПЕШНО ПРОЙДЕНЫ!
Все улучшения работают корректно.
```

Если некоторые тесты не пройдут, будет выведено сообщение с количеством неудачных тестов.

### Примечания

* Для запуска тестов требуется, чтобы сервис browserless был запущен и доступен
* Учетные данные для входа на сайт должны быть указаны в файле `.env`
* Тесты выполняются с URL `https://its.1c.ru/db/cabinetdoc` (указан в system_prompt.md)
* Некоторые тесты могут занимать несколько минут в зависимости от скорости соединения

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
