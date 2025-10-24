#!/bin/bash
# Простой скрипт для объединения файлов

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
    echo "Использование: $0 [директория] [опции]"
    echo "Примеры:"
    echo "  $0 out/cabinetdoc/json"
    echo "  $0 out/cabinetdoc/markdown --max-files 100"
    echo "  $0 out/cabinetdoc/json --merge-stats"
    exit 1
fi

# Запуск объединения
log "Запускаю объединение файлов..."
docker run -it --rm \
  -v "$(pwd)/out:/app/out" \
  -v "$(pwd)/merge:/app/merge" \
  scraping-its:latest --merge "$@"

success "Готово!"
