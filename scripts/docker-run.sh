#!/bin/bash
# Скрипт для запуска Docker контейнера с удобными параметрами

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для вывода сообщений
log() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Проверка наличия Docker
if ! command -v docker &> /dev/null; then
    error "Docker не установлен или не найден в PATH"
    exit 1
fi

# Проверка наличия .env файла
if [ ! -f ".env" ]; then
    warning ".env файл не найден. Создайте его на основе .env-example"
    if [ -f ".env-example" ]; then
        log "Копирую .env-example в .env..."
        cp .env-example .env
        warning "Отредактируйте .env файл с вашими учетными данными"
    fi
fi

# Создание необходимых директорий
mkdir -p out merge

# Определение образа
IMAGE_NAME="scraping-its:latest"

# Проверка существования образа
if ! docker image inspect "$IMAGE_NAME" &> /dev/null; then
    log "Образ $IMAGE_NAME не найден. Собираю..."
    docker build -t "$IMAGE_NAME" .
    success "Образ собран успешно"
fi

# Запуск контейнера
log "Запускаю контейнер с аргументами: $*"

docker run -it --rm \
    --name scraping-its-run \
    -v "$(pwd)/out:/app/out" \
    -v "$(pwd)/merge:/app/merge" \
    -v "$(pwd)/.env:/app/.env:ro" \
    -e PYTHONUNBUFFERED=1 \
    "$IMAGE_NAME" "$@"

success "Контейнер завершил работу"

