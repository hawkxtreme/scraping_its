@echo off
REM Простой скрипт для запуска скрапинга

REM Установка кодировки UTF-8
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

REM Проверка аргументов
if "%~1"=="" (
    echo Использование: scrape.bat [URL] [опции]
    echo Примеры:
    echo   scrape.bat https://its.1c.ru/db/cabinetdoc
    echo   scrape.bat https://its.1c.ru/db/cabinetdoc --format json markdown
    echo   scrape.bat https://its.1c.ru/db/cabinetdoc --limit 10
    exit /b 1
)

REM Запуск browserless в фоне
echo [INFO] Запускаю browserless...
docker-compose up -d browserless >nul 2>&1

REM Ожидание готовности browserless
echo [INFO] Ожидаю готовности browserless...
timeout /t 5 /nobreak >nul

REM Запуск скрапинга
echo [INFO] Запускаю скрапинг...
docker run -it --rm ^
  -v "%cd%\out:/app/out" ^
  -v "%cd%\.env:/app/.env:ro" ^
  --network scraping-network ^
  -e BROWSERLESS_URL=http://browserless:3000 ^
  scraping-its:test %*

REM Остановка browserless
echo [INFO] Останавливаю browserless...
docker-compose down >nul 2>&1

echo [SUCCESS] Готово!
