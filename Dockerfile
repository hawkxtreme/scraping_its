# Многоэтапная сборка для оптимизации размера
FROM python:3.11-slim AS builder

# Установка системных зависимостей для сборки
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Установка Playwright и браузеров
RUN pip install --no-cache-dir playwright
RUN playwright install chromium

# Копирование и установка зависимостей Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Финальный образ
FROM python:3.11-slim

# Метаданные образа
LABEL maintainer="hawkxtreme"
LABEL description="1C ITS Article Scraper with file merging capabilities"
LABEL version="1.0.0"

# Установка runtime зависимостей для Playwright
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
    libx11-xcb1 \
    libxcb-dri3-0 \
    libxfixes3 \
    libx11-6 \
    libxext6 \
    libxtst6 \
    libpangocairo-1.0-0 \
    libatk1.0-0 \
    libcairo-gobject2 \
    libgtk-3-0 \
    libgdk-pixbuf-2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Копирование установленных пакетов из builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /root/.cache/ms-playwright /root/.cache/ms-playwright

# Создание пользователя для безопасности
RUN useradd -m -u 1000 scraper && \
    mkdir -p /app/out /app/merge && \
    chown -R scraper:scraper /app

USER scraper
WORKDIR /app

# Копирование кода приложения
COPY --chown=scraper:scraper . .

# Настройка переменных окружения
ENV PYTHONPATH=/app
ENV BROWSERLESS_URL=http://localhost:3000
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Создание директорий для данных
RUN mkdir -p /app/out /app/merge

# Healthcheck для мониторинга
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:3000', timeout=5)" || exit 1

# Точка входа
ENTRYPOINT ["python", "main.py"]

# Аргументы по умолчанию (можно переопределить)
CMD ["--help"]
