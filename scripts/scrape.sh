#!/bin/bash
# Простой скрипт для запуска скрапинга

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

# Проверка аргументов
if [ $# -eq 0 ]; then
    echo "Использование: $0 [URL] [опции]"
    echo "Примеры:"
    echo "  $0 https://its.1c.ru/db/cabinetdoc"
    echo "  $0 https://its.1c.ru/db/cabinetdoc --format json markdown"
    echo "  $0 https://its.1c.ru/db/cabinetdoc --limit 10"
    exit 1
fi

# Запуск browserless в фоне
log "Запускаю browserless..."
docker-compose up -d browserless >/dev/null 2>&1

# Ожидание готовности browserless
log "Ожидаю готовности browserless..."
sleep 5

# Запуск скрапинга
log "Запускаю скрапинг..."
docker run -it --rm \
  -v "$(pwd)/out:/app/out" \
  -v "$(pwd)/.env:/app/.env:ro" \
  --network scraping-network \
  -e BROWSERLESS_URL=http://browserless:3000 \
  scraping-its:latest "$@"

# Остановка browserless
log "Останавливаю browserless..."
docker-compose down >/dev/null 2>&1

success "Готово!"
