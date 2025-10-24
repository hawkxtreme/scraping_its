# Простой скрипт для запуска скрапинга (PowerShell)

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
    Write-Host "Использование: .\scrape.ps1 [URL] [опции]"
    Write-Host "Примеры:"
    Write-Host "  .\scrape.ps1 https://its.1c.ru/db/cabinetdoc"
    Write-Host "  .\scrape.ps1 https://its.1c.ru/db/cabinetdoc --format json markdown"
    Write-Host "  .\scrape.ps1 https://its.1c.ru/db/cabinetdoc --limit 10"
    exit 1
}

# Запуск browserless в фоне
Write-Info "Запускаю browserless..."
docker-compose up -d browserless | Out-Null

# Ожидание готовности browserless
Write-Info "Ожидаю готовности browserless..."
Start-Sleep -Seconds 5

# Запуск скрапинга
Write-Info "Запускаю скрапинг..."
$argString = $Arguments -join " "
docker run -it --rm `
  -v "${PWD}/out:/app/out" `
  -v "${PWD}/.env:/app/.env:ro" `
  --network scraping-network `
  -e BROWSERLESS_URL=http://browserless:3000 `
  scraping-its:test $argString

# Остановка browserless
Write-Info "Останавливаю browserless..."
docker-compose down | Out-Null

Write-Success "Готово!"
