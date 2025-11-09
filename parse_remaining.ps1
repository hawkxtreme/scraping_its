# Параллельный парсинг оставшихся разделов 1С ИТС
# Распределение 16 потоков между 6 задачами

$sections = @(
    @{name = "method_dev"; url = "https://its.1c.ru/section/dev/method_dev"; threads = 4},
    @{name = "metod81_2335"; url = "https://its.1c.ru/db/metod81#browse:13:-1:2115:2335"; threads = 2},
    @{name = "metod81_2443"; url = "https://its.1c.ru/db/metod81#browse:13:-1:2115:2443"; threads = 3},
    @{name = "metod81_2525"; url = "https://its.1c.ru/db/metod81#browse:13:-1:2115:2525"; threads = 3},
    @{name = "metod81_2382"; url = "https://its.1c.ru/db/metod81#browse:13:-1:2115:2382"; threads = 2},
    @{name = "metod81_2376"; url = "https://its.1c.ru/db/metod81#browse:13:-1:2115:2376"; threads = 2}
)

Write-Host "=== ЗАПУСК ПАРАЛЛЕЛЬНОГО ПАРСИНГА ===" -ForegroundColor Green
Write-Host "Всего разделов: $($sections.Count)" -ForegroundColor Cyan
Write-Host "Всего потоков: 16" -ForegroundColor Cyan
Write-Host ""

$jobs = @()

foreach ($section in $sections) {
    Write-Host "Запуск: $($section.name) | Потоки: $($section.threads)" -ForegroundColor Yellow
    
    $job = Start-Job -ScriptBlock {
        param($url, $threads, $name)
        Set-Location "D:\My Projects\FrameWork 1C\scraping_its"
        python main.py $url --format markdown --update --rag --parallel $threads --verbose 2>&1
    } -ArgumentList $section.url, $section.threads, $section.name
    
    $jobs += @{Job = $job; Name = $section.name; Threads = $section.threads}
    Start-Sleep -Milliseconds 500
}

Write-Host ""
Write-Host "=== ВСЕ ЗАДАЧИ ЗАПУЩЕНЫ ===" -ForegroundColor Green
Write-Host ""

# Мониторинг
$startTime = Get-Date

while (($jobs | Where-Object { $_.Job.State -eq 'Running' }).Count -gt 0) {
    Clear-Host
    Write-Host "=== СТАТУС ПАРСИНГА ===" -ForegroundColor Cyan
    $elapsed = [math]::Round((New-TimeSpan -Start $startTime -End (Get-Date)).TotalMinutes, 1)
    Write-Host "Время работы: $elapsed мин" -ForegroundColor White
    Write-Host ""
    
    foreach ($jobInfo in $jobs) {
        $state = $jobInfo.Job.State
        $color = if ($state -eq 'Running') { "Cyan" } elseif ($state -eq 'Completed') { "Green" } else { "Red" }
        Write-Host "  [$($jobInfo.Threads)п] $($jobInfo.Name): $state" -ForegroundColor $color
        
        $outPath = "D:\My Projects\FrameWork 1C\scraping_its\out\$($jobInfo.Name)\markdown"
        if (Test-Path $outPath) {
            $fileCount = (Get-ChildItem $outPath -Filter *.md -ErrorAction SilentlyContinue | Measure-Object).Count
            if ($fileCount -gt 0) {
                Write-Host "      -> Сохранено: $fileCount статей" -ForegroundColor DarkGray
            }
        }
    }
    
    Write-Host ""
    Write-Host "Обновление через 30 сек..." -ForegroundColor DarkGray
    Start-Sleep -Seconds 30
}

Write-Host ""
Write-Host "=== ПАРСИНГ ЗАВЕРШЕН ===" -ForegroundColor Green
Write-Host ""

# Итоги
foreach ($jobInfo in $jobs) {
    $null = Receive-Job -Job $jobInfo.Job
    Write-Host "=== $($jobInfo.Name) ===" -ForegroundColor Cyan
    $statusColor = "Green"
    if ($jobInfo.Job.State -ne 'Completed') { $statusColor = "Red" }
    Write-Host "Статус: $($jobInfo.Job.State)" -ForegroundColor $statusColor
    
    $outPath = "D:\My Projects\FrameWork 1C\scraping_its\out\$($jobInfo.Name)\markdown"
    if (Test-Path $outPath) {
        $fileCount = (Get-ChildItem $outPath -Filter *.md -ErrorAction SilentlyContinue | Measure-Object).Count
        Write-Host "Сохранено статей: $fileCount" -ForegroundColor White
    }
    Write-Host ""
    Remove-Job -Job $jobInfo.Job -Force
}

$totalTime = [math]::Round((New-TimeSpan -Start $startTime -End (Get-Date)).TotalMinutes, 1)
Write-Host "Все задачи завершены. Общее время: $totalTime мин" -ForegroundColor Green
