@echo off
chcp 65001 >nul 2>&1

if "%~1"=="" (
    echo Usage: scrape-simple.bat [URL] [options]
    echo Example: scrape-simple.bat https://its.1c.ru/db/cabinetdoc --format json
    exit /b 1
)

echo [INFO] Starting browserless...
docker-compose up -d browserless >nul 2>&1

echo [INFO] Waiting for browserless...
timeout /t 5 /nobreak >nul

echo [INFO] Starting scrape...
docker run -it --rm -v "%cd%\out:/app/out" -v "%cd%\.env:/app/.env:ro" --network scraping-network -e BROWSERLESS_URL=http://browserless:3000 scraping-its:test %*

echo [INFO] Stopping browserless...
docker-compose down >nul 2>&1

echo [SUCCESS] Done!
