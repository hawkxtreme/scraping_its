@echo off
REM Простой скрипт для объединения файлов

REM Установка кодировки UTF-8
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

REM Проверка аргументов
if "%~1"=="" (
    echo Использование: merge.bat [директория] [опции]
    echo Примеры:
    echo   merge.bat out/cabinetdoc/json
    echo   merge.bat out/cabinetdoc/markdown --max-files 100
    echo   merge.bat out/cabinetdoc/json --merge-stats
    exit /b 1
)

REM Запуск объединения
echo [INFO] Запускаю объединение файлов...
docker run -it --rm ^
  -v "%cd%\out:/app/out" ^
  -v "%cd%\merge:/app/merge" ^
  scraping-its:test --merge --merge-dir %*

echo [SUCCESS] Готово!
