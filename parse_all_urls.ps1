# Скрипт для последовательного парсинга всех URL-ов документации 1C ITS
# Создан: 08.11.2024

$urls = @(
    "https://its.1c.ru/db/bsp3111doc",
    "https://its.1c.ru/section/dev/method_dev",
    "https://its.1c.ru/db/metod81#browse:13:-1:2115:2335",
    "https://its.1c.ru/db/metod81#browse:13:-1:2115:2443",
    "https://its.1c.ru/db/metod81#browse:13:-1:2115:2525",
    "https://its.1c.ru/db/metod81#browse:13:-1:2115:2382",
    "https://its.1c.ru/db/metod81#browse:13:-1:2115:2376"
)

$names = @(
    "БСП 3.1.11",
    "Методики разработки",
    "Методология - Общие вопросы",
    "Методология - Механизмы платформы",
    "Методология - Управляемое приложение",
    "Методология - Разработка интерфейса",
    "Методология - Прочие вопросы"
)

# Определяем оптимальное количество потоков - 8 потоков (50% CPU)
$cpu = Get-WmiObject -Class Win32_Processor
$threads = $cpu.NumberOfLogicalProcessors
$parallelThreads = 8  # Фиксированное значение для максимальной производительности

$totalUrls = $urls.Count
$currentUrl = 1

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  Автоматический парсинг документации 1С ИТС" -ForegroundColor Green
Write-Host "  Всего разделов: $totalUrls" -ForegroundColor Green
Write-Host "  CPU потоков: $threads | Используем: $parallelThreads (~30%)" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""

foreach ($i in 0..($urls.Count - 1)) {
    $url = $urls[$i]
    $name = $names[$i]
    
    Write-Host ""
    Write-Host "------------------------------------------------------------" -ForegroundColor Cyan
    Write-Host "  [$currentUrl/$totalUrls] $name" -ForegroundColor Cyan
    Write-Host "  URL: $url" -ForegroundColor Gray
    Write-Host "------------------------------------------------------------" -ForegroundColor Cyan
    Write-Host ""
    
    $startTime = Get-Date
    
    # Запускаем парсинг с обновлением, параллельными потоками и RAG-метаданными
    python main.py $url --format markdown --update --parallel $parallelThreads --rag --verbose
    
    $endTime = Get-Date
    $duration = $endTime - $startTime
    $durationStr = "{0:hh\:mm\:ss}" -f $duration
    
    Write-Host ""
    Write-Host "  ✓ Раздел '$name' завершен" -ForegroundColor Green
    Write-Host "  Время выполнения: $durationStr" -ForegroundColor Gray
    Write-Host ""
    
    $currentUrl++
    
    # Пауза между разделами (5 секунд)
    if ($i -lt ($urls.Count - 1)) {
        Write-Host "  Пауза перед следующим разделом (5 сек)..." -ForegroundColor Yellow
        Start-Sleep -Seconds 5
    }
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  ВСЕ РАЗДЕЛЫ ЗАВЕРШЕНЫ!" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Результаты сохранены в: .\out\" -ForegroundColor Cyan
Write-Host ""

