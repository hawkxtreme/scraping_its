# 🐳 **Подробный план внедрения Docker контейнеризации**

## 📋 **Этап 1: Анализ и подготовка (1-2 дня)**

### 1.1 Анализ текущей архитектуры
- [x] Изучить зависимости проекта (`requirements.txt`)
- [x] Проанализировать использование browserless
- [x] Определить системные требования
- [x] Выявить проблемы текущего подхода

### 1.2 Планирование архитектуры Docker
- [ ] Выбрать базовый образ (Python 3.11+)
- [ ] Определить стратегию многоэтапной сборки
- [ ] Спланировать структуру volumes
- [ ] Определить переменные окружения

## 📋 **Этап 2: Создание Dockerfile (2-3 дня)**

### 2.1 Базовый Dockerfile
```dockerfile
# Многоэтапная сборка для оптимизации размера
FROM python:3.11-slim as builder

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Установка Playwright и браузеров
RUN pip install playwright
RUN playwright install chromium

# Копирование и установка зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Финальный образ
FROM python:3.11-slim

# Копирование установленных пакетов
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /root/.cache/ms-playwright /root/.cache/ms-playwright

# Установка runtime зависимостей
RUN apt-get update && apt-get install -y \
    libnss3 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libgbm1 \
    libxss1 \
    libasound2 \
    && rm -rf /var/lib/apt/lists/*

# Создание пользователя для безопасности
RUN useradd -m -u 1000 scraper
USER scraper
WORKDIR /app

# Копирование кода приложения
COPY --chown=scraper:scraper . .

# Настройка переменных окружения
ENV PYTHONPATH=/app
ENV BROWSERLESS_URL=http://localhost:3000

# Точка входа
ENTRYPOINT ["python", "main.py"]
```

### 2.2 Оптимизация Dockerfile
- [ ] Добавить .dockerignore
- [ ] Оптимизировать слои кэширования
- [ ] Настроить healthcheck
- [ ] Добавить метаданные образа

## 📋 **Этап 3: Docker Compose (1 день)**

### 3.1 Создание docker-compose.yml
```yaml
version: '3.8'

services:
  browserless:
    image: browserless/chrome:latest
    ports:
      - "3000:3000"
    environment:
      - PREBOOT_CHROME=true
      - KEEP_ALIVE=true
    restart: unless-stopped

  scraper:
    build: .
    depends_on:
      - browserless
    volumes:
      - ./out:/app/out
      - ./merge:/app/merge
      - ./.env:/app/.env:ro
    environment:
      - BROWSERLESS_URL=http://browserless:3000
    command: ["https://its.1c.ru/db/cabinetdoc", "--format", "json"]
    restart: "no"

  # Сервис для объединения файлов
  merger:
    build: .
    volumes:
      - ./out:/app/out
      - ./merge:/app/merge
    command: ["--merge", "--merge-dir", "out/cabinetdoc/json"]
    profiles:
      - merge
```

### 3.2 Дополнительные конфигурации
- [ ] Создать docker-compose.override.yml для разработки
- [ ] Добавить профили для разных сценариев
- [ ] Настроить логирование

## 📋 **Этап 4: Вспомогательные скрипты (1 день)**

### 4.1 Скрипты для упрощения использования
```bash
# scripts/docker-run.sh
#!/bin/bash
docker run -it --rm \
  -v "$(pwd)/out:/app/out" \
  -v "$(pwd)/merge:/app/merge" \
  -v "$(pwd)/.env:/app/.env:ro" \
  scraping-its:latest "$@"
```

### 4.2 Скрипты для разработки
- [ ] `scripts/docker-dev.sh` - для разработки
- [ ] `scripts/docker-build.sh` - для сборки
- [ ] `scripts/docker-test.sh` - для тестирования

## 📋 **Этап 5: Обновление документации (2 дня)**

### 5.1 Обновление README.md
- [ ] Добавить раздел "Docker Quick Start"
- [ ] Сравнить Docker vs локальная установка
- [ ] Добавить примеры использования
- [ ] Troubleshooting для Docker

### 5.2 Создание Docker-specific документации
- [ ] `docs/DOCKER.md` - подробная документация по Docker
- [ ] `docs/DOCKER_EXAMPLES.md` - примеры использования
- [ ] `docs/DOCKER_TROUBLESHOOTING.md` - решение проблем

## 📋 **Этап 6: Тестирование Docker (2-3 дня)**

### 6.1 Создание тестов для Docker
```python
# tests/test_docker.py
import subprocess
import pytest

def test_docker_build():
    """Тест сборки Docker образа."""
    result = subprocess.run(
        ["docker", "build", "-t", "scraping-its:test", "."],
        capture_output=True, text=True
    )
    assert result.returncode == 0

def test_docker_run():
    """Тест запуска Docker контейнера."""
    result = subprocess.run([
        "docker", "run", "--rm",
        "-v", f"{os.getcwd()}/out:/app/out",
        "scraping-its:test",
        "--help"
    ], capture_output=True, text=True)
    assert result.returncode == 0
```

### 6.2 Интеграционные тесты
- [ ] Тест полного цикла скрапинга
- [ ] Тест объединения файлов
- [ ] Тест с разными форматами
- [ ] Тест обработки ошибок

## 📋 **Этап 7: CI/CD интеграция (1-2 дня)**

### 7.1 GitHub Actions
```yaml
# .github/workflows/docker.yml
name: Docker Build and Push

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

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

### 7.2 Docker Hub интеграция
- [ ] Настроить автоматическую сборку
- [ ] Создать теги для версий
- [ ] Настроить multi-arch сборки

## 📋 **Этап 8: Оптимизация и финализация (1-2 дня)**

### 8.1 Оптимизация размера образа
- [ ] Анализ размера слоев
- [ ] Удаление ненужных файлов
- [ ] Использование distroless образов
- [ ] Multi-stage сборка

### 8.2 Безопасность
- [ ] Сканирование уязвимостей
- [ ] Настройка non-root пользователя
- [ ] Ограничение ресурсов
- [ ] Secrets management

## 📋 **Этап 9: Тестирование и валидация (2-3 дня)**

### 9.1 Тестирование на разных платформах
- [ ] Windows (Docker Desktop)
- [ ] macOS (Docker Desktop)
- [ ] Linux (Ubuntu, CentOS)
- [ ] CI/CD окружения

### 9.2 Производительность
- [ ] Бенчмарки запуска
- [ ] Использование памяти
- [ ] Время сборки образа
- [ ] Время выполнения

## 📋 **Этап 10: Документация и релиз (1 день)**

### 10.1 Финальная документация
- [ ] Обновить все README файлы
- [ ] Создать CHANGELOG
- [ ] Обновить примеры
- [ ] Создать видео-туториалы

### 10.2 Релиз
- [ ] Создать GitHub Release
- [ ] Опубликовать в Docker Hub
- [ ] Уведомить пользователей
- [ ] Собрать обратную связь

## 🎯 **Итоговая структура файлов:**

```
project/
├── Dockerfile
├── docker-compose.yml
├── docker-compose.override.yml
├── .dockerignore
├── scripts/
│   ├── docker-run.sh
│   ├── docker-dev.sh
│   ├── docker-build.sh
│   └── docker-test.sh
├── docs/
│   ├── DOCKER.md
│   ├── DOCKER_EXAMPLES.md
│   └── DOCKER_TROUBLESHOOTING.md
├── .github/workflows/
│   └── docker.yml
└── tests/
    └── test_docker.py
```

## ⏱️ **Общее время выполнения: 15-20 дней**

## 🚀 **Приоритеты:**
1. **Высокий:** Dockerfile, docker-compose.yml, обновление README
2. **Средний:** Тестирование, вспомогательные скрипты
3. **Низкий:** CI/CD, продвинутая оптимизация

Этот план обеспечит плавное внедрение Docker контейнеризации с минимальными рисками и максимальной пользой для пользователей.

