# Универсальный скрипт для работы с 1С ИТС (PowerShell)

param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Arguments
)

# Установка кодировки UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# Функции для цветного вывода
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Проверка аргументов
if ($Arguments.Count -eq 0) {
    Write-Host "1С ИТС Scraper - Универсальный скрипт"
    Write-Host ""
    Write-Host "Использование:"
    Write-Host "  .\its.ps1 scrape [URL] [опции]     - Скачать документацию"
    Write-Host "  .\its.ps1 merge [директория] [опции] - Объединить файлы"
    Write-Host "  .\its.ps1 help                     - Показать справку"
    Write-Host ""
    Write-Host "Примеры:"
    Write-Host "  .\its.ps1 scrape https://its.1c.ru/db/cabinetdoc"
    Write-Host "  .\its.ps1 scrape https://its.1c.ru/db/cabinetdoc --format json markdown --limit 10"
    Write-Host "  .\its.ps1 merge out/cabinetdoc/json --max-files 100"
    Write-Host "  .\its.ps1 merge out/cabinetdoc/markdown --merge-stats"
    exit 1
}

if ($Arguments[0] -eq "help") {
    Write-Host "1С ИТС Scraper - Справка"
    Write-Host ""
    Write-Host "СКРАПИНГ:"
    Write-Host "  .\its.ps1 scrape [URL] [опции]"
    Write-Host ""
    Write-Host "  Опции скрапинга:"
    Write-Host "    --format json|markdown|txt|pdf  - Форматы вывода"
    Write-Host "    --limit N                       - Ограничить количество статей"
    Write-Host "    --verbose                       - Подробный вывод"
    Write-Host "    --timeout N                     - Таймаут загрузки страниц"
    Write-Host ""
    Write-Host "ОБЪЕДИНЕНИЕ:"
    Write-Host "  .\its.ps1 merge [директория] [опции]"
    Write-Host ""
    Write-Host "  Опции объединения:"
    Write-Host "    --max-files N                   - Максимум файлов в группе"
    Write-Host "    --max-size N                    - Максимальный размер группы (MB)"
    Write-Host "    --merge-stats                   - Показать статистику"
    Write-Host "    --compress                      - Сжать результат"
    Write-Host ""
    exit 0
}

if ($Arguments[0] -eq "scrape") {
    $scrapeArgs = $Arguments[1..($Arguments.Count-1)]
    & ".\scrape.ps1" @scrapeArgs
    exit $LASTEXITCODE
}

if ($Arguments[0] -eq "merge") {
    $mergeArgs = $Arguments[1..($Arguments.Count-1)]
    & ".\merge.ps1" @mergeArgs
    exit $LASTEXITCODE
}

Write-Error "Неизвестная команда: $($Arguments[0])"
Write-Host "Используйте: .\its.ps1 help"
exit 1
