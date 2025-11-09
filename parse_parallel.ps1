# Параллельный запуск всех оставшихся разделов
# Каждый раздел получает 1-2 потока для оптимального распределения нагрузки

$urls = @(
    @{url="https://its.1c.ru/section/dev/method_dev"; name="Методики разработки"; threads=4},
    @{url="https://its.1c.ru/db/metod81#browse:13:-1:2115:2335"; name="Методология - Общие вопросы"; threads=2},
    @{url="https://its.1c.ru/db/metod81#browse:13:-1:2115:2443"; name="Методология - Механизмы платформы"; threads=2},
    @{url="https://its.1c.ru/db/metod81#browse:13:-1:2115:2525"; name="Методология - Управляемое приложение"; threads=3},
    @{url="https://its.1c.ru/db/metod81#browse:13:-1:2115:2382"; name="Методология - Разработка интерфейса"; threads=3},
    @{url="https://its.1c.ru/db/metod81#browse:13:-1:2115:2376"; name="Методология - Прочие вопросы"; threads=2}
)

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  Параллельный парсинг оставшихся 6 разделов" -ForegroundColor Green
Write-Host "  Общая нагрузка: 16 потоков (100% CPU)" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""

$jobs = @()

foreach ($section in $urls) {
    $scriptBlock = {
        param($url, $name, $threads)
        
        Set-Location "D:\My Projects\FrameWork 1C\scraping_its"
        
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Запуск: $name ($threads потока)" -ForegroundColor Cyan
        
        python main.py $url --format markdown --update --parallel $threads --rag --verbose
        
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Завершено: $name" -ForegroundColor Green
    }
    
    $job = Start-Job -ScriptBlock $scriptBlock -ArgumentList $section.url, $section.name, $section.threads
    $jobs += @{Job=$job; Name=$section.name}
    
    Write-Host "  ✓ Запущен: $($section.name) ($($section.threads) потока) [Job ID: $($job.Id)]" -ForegroundColor Cyan
    Start-Sleep -Milliseconds 500
}

Write-Host ""
Write-Host "Все разделы запущены параллельно!" -ForegroundColor Green
Write-Host ""
Write-Host "Мониторинг выполнения..." -ForegroundColor Yellow
Write-Host ""

# Мониторинг выполнения
$startTime = Get-Date
while ($true) {
    Clear-Host
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "  Статус параллельного парсинга" -ForegroundColor Green
    Write-Host "  Время работы: $(([Math]::Round(((Get-Date) - $startTime).TotalMinutes, 1))) минут" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host ""
    
    $allCompleted = $true
    foreach ($jobInfo in $jobs) {
        $job = $jobInfo.Job
        $name = $jobInfo.Name
        $state = $job.State
        
        $color = switch ($state) {
            "Running" { "Yellow"; $allCompleted = $false }
            "Completed" { "Green" }
            "Failed" { "Red" }
            default { "Gray"; $allCompleted = $false }
        }
        
        Write-Host "  [$state] $name" -ForegroundColor $color
    }
    
    Write-Host ""
    
    # Проверяем сохраненные файлы
    $sections = @('method_dev', 'metod81')
    foreach ($section in $sections) {
        $path = "out\$section\markdown"
        if (Test-Path $path) {
            $count = (Get-ChildItem $path -Filter "*.md" -ErrorAction SilentlyContinue | Measure-Object).Count
            if ($count -gt 0) {
                Write-Host "  $section`: $count статей" -ForegroundColor Cyan
            }
        }
    }
    
    if ($allCompleted) {
        Write-Host ""
        Write-Host "ВСЕ РАЗДЕЛЫ ЗАВЕРШЕНЫ!" -ForegroundColor Green
        break
    }
    
    Start-Sleep -Seconds 30
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  Получение результатов..." -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green

foreach ($jobInfo in $jobs) {
    Write-Host ""
    Write-Host "--- $($jobInfo.Name) ---" -ForegroundColor Cyan
    Receive-Job -Job $jobInfo.Job | Select-Object -Last 20
    Remove-Job -Job $jobInfo.Job
}

Write-Host ""
Write-Host "Готово!" -ForegroundColor Green

