@echo off
chcp 65001 >nul 2>&1

if "%~1"=="" (
    echo Usage: merge-simple.bat [directory] [options]
    echo Example: merge-simple.bat out/cabinetdoc/json --max-files 100
    exit /b 1
)

echo [INFO] Starting merge...
docker run -it --rm -v "%cd%\out:/app/out" -v "%cd%\merge:/app/merge" scraping-its:test --merge --merge-dir %*

echo [SUCCESS] Done!
