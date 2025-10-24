#!/bin/bash
# Скрипт для сборки Docker образа

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

# Параметры по умолчанию
IMAGE_NAME="scraping-its"
TAG="latest"
NO_CACHE=""

# Обработка аргументов
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--tag)
            TAG="$2"
            shift 2
            ;;
        -n|--name)
            IMAGE_NAME="$2"
            shift 2
            ;;
        --no-cache)
            NO_CACHE="--no-cache"
            shift
            ;;
        -h|--help)
            echo "Использование: $0 [OPTIONS]"
            echo "Опции:"
            echo "  -t, --tag TAG       Тег образа (по умолчанию: latest)"
            echo "  -n, --name NAME     Имя образа (по умолчанию: scraping-its)"
            echo "  --no-cache          Сборка без кэша"
            echo "  -h, --help          Показать эту справку"
            exit 0
            ;;
        *)
            error "Неизвестный параметр: $1"
            exit 1
            ;;
    esac
done

FULL_IMAGE_NAME="${IMAGE_NAME}:${TAG}"

log "Собираю Docker образ: $FULL_IMAGE_NAME"

# Проверка наличия Dockerfile
if [ ! -f "Dockerfile" ]; then
    error "Dockerfile не найден в текущей директории"
    exit 1
fi

# Сборка образа
docker build $NO_CACHE -t "$FULL_IMAGE_NAME" .

# Проверка успешности сборки
if [ $? -eq 0 ]; then
    success "Образ $FULL_IMAGE_NAME собран успешно"
    
    # Показать информацию об образе
    log "Информация об образе:"
    docker images "$FULL_IMAGE_NAME" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"
    
    # Тест запуска
    log "Тестирую запуск контейнера..."
    if docker run --rm "$FULL_IMAGE_NAME" --help > /dev/null 2>&1; then
        success "Тест запуска прошел успешно"
    else
        error "Тест запуска не прошел"
        exit 1
    fi
else
    error "Ошибка при сборке образа"
    exit 1
fi

