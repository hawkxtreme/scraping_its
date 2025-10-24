#!/bin/bash
# Скрипт для разработки с Docker

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Проверка наличия Docker Compose
if ! command -v docker-compose &> /dev/null; then
    error "Docker Compose не установлен"
    exit 1
fi

# Создание необходимых директорий
mkdir -p out merge

# Запуск в режиме разработки
log "Запускаю контейнер в режиме разработки..."

if [ "$1" = "build" ]; then
    log "Пересобираю образ..."
    docker-compose build --no-cache
fi

# Запуск с профилем dev
docker-compose --profile dev up -d browserless
log "Ожидаю готовности browserless..."
sleep 10

# Запуск dev контейнера
docker-compose --profile dev run --rm dev

success "Режим разработки завершен"

