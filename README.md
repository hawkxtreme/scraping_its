# Скраппер статей 1С ИТС

Этот скрипт предназначен для скрапинга статей с сайта its.1c.ru и сохранения их в различных форматах.

## Системные требования

* Python 3.8 или выше
* Docker 20.10 или выше (для browserless)
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

6. **Создайте файл .env на основе примера:**
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


## Аргументы командной строки

Для получения справки по всем доступным командам используйте:

```bash
python main.py --help
# или
python main.py -h
```

Будет отображен список всех доступных аргументов и их описание.

Все доступные команды

```bash
usage: main.py [-h] [-c CHAPTER] [-f {json,pdf,txt,markdown} [{json,pdf,txt,markdown} ...]] 
              [--no-scrape] [--force-reindex] [-p PARALLEL] url

Аргументы:
  url                  URL раздела для скрапинга
  -h, --help           Вывести справку о командах
  -c, --chapter        Название главы для выборочного скрапинга
  -f, --format         Форматы выходных файлов json, pdf, txt, markdown (можно указать несколько)
  --no-scrape          Только создать индекс без скрапинга статей
  --force-reindex      Принудительно обновить индекс статей
  -p, --parallel       Количество параллельных потоков для скачивания (по умолчанию 1)
```

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

## Примеры использования

* Скрапинг всего раздела в форматах JSON, PDF, TXT, MARKDOWN:
```bash
python main.py https://its.1c.ru/db/erp25ltsdoc --format json pdf txt markdown
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

## Roadmap

* Автоматическое создание файла оглавления с ссылками на выгруженные статьи
* Улучшение логирования и информативности ошибок
* Поддержка формата DOCX
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
