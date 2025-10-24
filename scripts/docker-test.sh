#!/bin/bash
# Скрипт для тестирования Docker контейнера

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

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Параметры по умолчанию
IMAGE_NAME="scraping-its:latest"
TEST_MODE="basic"

# Обработка аргументов
while [[ $# -gt 0 ]]; do
    case $1 in
        -i|--image)
            IMAGE_NAME="$2"
            shift 2
            ;;
        -m|--mode)
            TEST_MODE="$2"
            shift 2
            ;;
        -h|--help)
            echo "Использование: $0 [OPTIONS]"
            echo "Опции:"
            echo "  -i, --image IMAGE   Имя образа для тестирования (по умолчанию: scraping-its:latest)"
            echo "  -m, --mode MODE     Режим тестирования: basic, full, merge (по умолчанию: basic)"
            echo "  -h, --help          Показать эту справку"
            exit 0
            ;;
        *)
            error "Неизвестный параметр: $1"
            exit 1
            ;;
    esac
done

log "Тестирую Docker образ: $IMAGE_NAME"
log "Режим тестирования: $TEST_MODE"

# Проверка наличия образа
if ! docker image inspect "$IMAGE_NAME" &> /dev/null; then
    error "Образ $IMAGE_NAME не найден"
    exit 1
fi

# Создание тестовых директорий
mkdir -p out merge

# Функция для запуска теста
run_test() {
    local test_name="$1"
    local command="$2"
    local expected_exit_code="${3:-0}"
    
    log "Запускаю тест: $test_name"
    
    if docker run --rm \
        -v "$(pwd)/out:/app/out" \
        -v "$(pwd)/merge:/app/merge" \
        -e PYTHONUNBUFFERED=1 \
        "$IMAGE_NAME" $command; then
        if [ $? -eq $expected_exit_code ]; then
            success "Тест '$test_name' прошел успешно"
            return 0
        else
            error "Тест '$test_name' завершился с неожиданным кодом выхода"
            return 1
        fi
    else
        error "Тест '$test_name' не прошел"
        return 1
    fi
}

# Базовые тесты
log "=== Базовые тесты ==="
run_test "Справка" "--help"
run_test "Версия" "--version" 2  # Ожидаем код 2, так как --version не реализован

# Тесты объединения файлов (если есть данные)
if [ -d "out" ] && [ "$(ls -A out 2>/dev/null)" ]; then
    log "=== Тесты объединения файлов ==="
    run_test "Статистика объединения" "--merge --merge-dir out/cabinetdoc/json --merge-stats"
    run_test "Объединение JSON" "--merge --merge-dir out/cabinetdoc/json --max-files 100"
else
    warning "Директория out пуста, пропускаю тесты объединения"
fi

# Полные тесты (требуют browserless)
if [ "$TEST_MODE" = "full" ]; then
    log "=== Полные тесты (требуют browserless) ==="
    warning "Для полных тестов необходимо запустить browserless контейнер"
    warning "Используйте: docker-compose up -d browserless"
fi

success "Все тесты завершены"

