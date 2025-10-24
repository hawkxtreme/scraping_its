# Простой скрипт для объединения файлов (PowerShell)

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
    Write-Host "Использование: .\merge.ps1 [директория] [опции]"
    Write-Host "Примеры:"
    Write-Host "  .\merge.ps1 out/cabinetdoc/json"
    Write-Host "  .\merge.ps1 out/cabinetdoc/markdown --max-files 100"
    Write-Host "  .\merge.ps1 out/cabinetdoc/json --merge-stats"
    exit 1
}

# Запуск объединения
Write-Info "Запускаю объединение файлов..."
$argString = $Arguments -join " "
docker run -it --rm `
  -v "${PWD}/out:/app/out" `
  -v "${PWD}/merge:/app/merge" `
  scraping-its:test --merge --merge-dir $argString

Write-Success "Готово!"
