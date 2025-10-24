# 🐳 **Docker контейнеризация**

## 📋 **Обзор**

Проект полностью поддерживает Docker контейнеризацию, что обеспечивает:
- **Простую установку** - один `docker run` вместо множества шагов
- **Изоляцию** - не конфликтует с локальными зависимостями
- **Консистентность** - работает одинаково на всех ОС
- **CI/CD готовность** - легко интегрируется в автоматизацию

## 🚀 **Быстрый старт**

### 1. Сборка образа
```bash
# Сборка образа
docker build -t scraping-its:latest .

# Или используйте готовый скрипт
./scripts/docker-build.sh
```

### 2. Запуск скрапинга
```bash
# Простой запуск
docker run -it --rm \
  -v "$(pwd)/out:/app/out" \
  -v "$(pwd)/merge:/app/merge" \
  -v "$(pwd)/.env:/app/.env:ro" \
  scraping-its:latest \
  https://its.1c.ru/db/cabinetdoc --format json

# Или используйте скрипт
./scripts/docker-run.sh https://its.1c.ru/db/cabinetdoc --format json
```

### 3. Объединение файлов
```bash
# Объединение файлов
docker run -it --rm \
  -v "$(pwd)/out:/app/out" \
  -v "$(pwd)/merge:/app/merge" \
  scraping-its:latest \
  --merge --merge-dir out/cabinetdoc/json --max-files 100
```

## 🐳 **Docker Compose**

### Базовое использование
```bash
# Запуск browserless + скрапинг
docker-compose --profile scrape up

# Запуск только объединения файлов
docker-compose --profile merge up

# Полный цикл: скрапинг + объединение
docker-compose --profile full up
```

### Режим разработки
```bash
# Интерактивный режим для разработки
docker-compose --profile dev up

# Пересборка образа
docker-compose build --no-cache
```

## 📁 **Структура volumes**

```
host/                    container/
├── out/            →    /app/out/          # Результаты скрапинга
├── merge/          →    /app/merge/        # Объединенные файлы
└── .env            →    /app/.env:ro       # Переменные окружения
```

## 🔧 **Конфигурация**

### Переменные окружения
```bash
# Основные настройки
BROWSERLESS_URL=http://localhost:3000    # URL browserless сервиса
PYTHONUNBUFFERED=1                       # Небуферизованный вывод Python

# Учетные данные (в .env файле)
LOGIN_1C_USER=your_username
LOGIN_1C_PASSWORD=your_password
```

### Настройка .env файла
```bash
# Скопируйте пример
cp .env-example .env

# Отредактируйте с вашими данными
nano .env
```

## 🛠️ **Вспомогательные скрипты**

### Linux/macOS
```bash
# Сборка образа
./scripts/docker-build.sh

# Запуск контейнера
./scripts/docker-run.sh [аргументы]

# Режим разработки
./scripts/docker-dev.sh

# Тестирование
./scripts/docker-test.sh
```

### Windows
```cmd
REM Сборка образа
scripts\docker-build.bat

REM Запуск контейнера
scripts\docker-run.bat [аргументы]
```

## 📊 **Профили Docker Compose**

### `scrape` - Скрапинг
```yaml
services:
  browserless:  # Browserless Chrome
  scraper:      # Основной скрапинг
```

### `merge` - Объединение файлов
```yaml
services:
  merger:       # Объединение файлов
```

### `full` - Полный цикл
```yaml
services:
  browserless:  # Browserless Chrome
  full-cycle:   # Скрапинг + объединение
```

### `dev` - Разработка
```yaml
services:
  browserless:  # Browserless Chrome
  dev:          # Интерактивный контейнер
```

## 🔍 **Мониторинг и отладка**

### Логи контейнера
```bash
# Просмотр логов
docker logs scraping-its

# Следить за логами в реальном времени
docker logs -f scraping-its
```

### Вход в контейнер
```bash
# Интерактивный режим
docker run -it --rm scraping-its:latest /bin/bash

# Через docker-compose
docker-compose --profile dev run dev
```

### Healthcheck
```bash
# Проверка состояния
docker inspect --format='{{.State.Health.Status}}' scraping-its

# Детальная информация
docker inspect scraping-its
```

## 🚀 **CI/CD интеграция**

### GitHub Actions
```yaml
name: Docker Build and Test
on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Build Docker image
        run: docker build -t scraping-its:${{ github.sha }} .
      - name: Test Docker image
        run: docker run --rm scraping-its:${{ github.sha }} --help
```

### GitLab CI
```yaml
build:
  stage: build
  script:
    - docker build -t scraping-its:$CI_COMMIT_SHA .
    - docker run --rm scraping-its:$CI_COMMIT_SHA --help
```

## 🔒 **Безопасность**

### Пользователь
- Контейнер запускается от пользователя `scraper` (UID 1000)
- Не использует root права

### Сеть
- По умолчанию изолированная сеть
- Доступ к browserless через внутреннюю сеть

### Secrets
- Учетные данные через .env файл
- Файл монтируется в режиме read-only

## 📈 **Производительность**

### Оптимизация образа
- Многоэтапная сборка
- Минимальный базовый образ (python:3.11-slim)
- Кэширование слоев

### Ресурсы
```bash
# Ограничение ресурсов
docker run --memory=2g --cpus=2 scraping-its:latest

# Через docker-compose
services:
  scraper:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '2'
```

## 🐛 **Troubleshooting**

### Проблемы с браузером
```bash
# Проверка browserless
curl http://localhost:3000

# Перезапуск browserless
docker-compose restart browserless
```

### Проблемы с правами
```bash
# Исправление прав на volumes
sudo chown -R 1000:1000 out merge
```

### Проблемы с памятью
```bash
# Очистка Docker
docker system prune -a

# Проверка использования места
docker system df
```

## 📚 **Примеры использования**

### Полный цикл работы
```bash
# 1. Сборка образа
docker build -t scraping-its:latest .

# 2. Запуск browserless
docker-compose up -d browserless

# 3. Скрапинг
docker run -it --rm \
  -v "$(pwd)/out:/app/out" \
  -v "$(pwd)/.env:/app/.env:ro" \
  scraping-its:latest \
  https://its.1c.ru/db/cabinetdoc --format json markdown txt

# 4. Объединение файлов
docker run -it --rm \
  -v "$(pwd)/out:/app/out" \
  -v "$(pwd)/merge:/app/merge" \
  scraping-its:latest \
  --merge --merge-dir out/cabinetdoc/json --max-files 100

# 5. Остановка browserless
docker-compose down
```

### Автоматизация
```bash
# Создание alias для удобства
alias its-scraper='docker run -it --rm -v "$(pwd)/out:/app/out" -v "$(pwd)/merge:/app/merge" -v "$(pwd)/.env:/app/.env:ro" scraping-its:latest'

# Использование
its-scraper https://its.1c.ru/db/cabinetdoc --format json
its-scraper --merge --merge-dir out/cabinetdoc/json --max-files 100
```

