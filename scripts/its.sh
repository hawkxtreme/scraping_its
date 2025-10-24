#!/bin/bash
# Универсальный скрипт для работы с 1С ИТС

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
    echo "1С ИТС Scraper - Универсальный скрипт"
    echo
    echo "Использование:"
    echo "  $0 scrape [URL] [опции]     - Скачать документацию"
    echo "  $0 merge [директория] [опции] - Объединить файлы"
    echo "  $0 help                     - Показать справку"
    echo
    echo "Примеры:"
    echo "  $0 scrape https://its.1c.ru/db/cabinetdoc"
    echo "  $0 scrape https://its.1c.ru/db/cabinetdoc --format json markdown --limit 10"
    echo "  $0 merge out/cabinetdoc/json --max-files 100"
    echo "  $0 merge out/cabinetdoc/markdown --merge-stats"
    exit 1
fi

if [ "$1" = "help" ]; then
    echo "1С ИТС Scraper - Справка"
    echo
    echo "СКРАПИНГ:"
    echo "  $0 scrape [URL] [опции]"
    echo
    echo "  Опции скрапинга:"
    echo "    --format json|markdown|txt|pdf  - Форматы вывода"
    echo "    --limit N                       - Ограничить количество статей"
    echo "    --verbose                       - Подробный вывод"
    echo "    --timeout N                     - Таймаут загрузки страниц"
    echo
    echo "ОБЪЕДИНЕНИЕ:"
    echo "  $0 merge [директория] [опции]"
    echo
    echo "  Опции объединения:"
    echo "    --max-files N                   - Максимум файлов в группе"
    echo "    --max-size N                    - Максимальный размер группы (MB)"
    echo "    --merge-stats                   - Показать статистику"
    echo "    --compress                      - Сжать результат"
    echo
    exit 0
fi

if [ "$1" = "scrape" ]; then
    shift
    exec "$0" scrape "$@"
fi

if [ "$1" = "merge" ]; then
    shift
    exec "$0" merge "$@"
fi

error "Неизвестная команда: $1"
echo "Используйте: $0 help"
exit 1
