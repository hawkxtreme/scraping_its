@echo off
REM Универсальный скрипт для работы с 1С ИТС

REM Установка кодировки UTF-8
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

REM Проверка аргументов
if "%~1"=="" (
    echo 1С ИТС Scraper - Универсальный скрипт
    echo.
    echo Использование:
    echo   its.bat scrape [URL] [опции]     - Скачать документацию
    echo   its.bat merge [директория] [опции] - Объединить файлы
    echo   its.bat help                     - Показать справку
    echo.
    echo Примеры:
    echo   its.bat scrape https://its.1c.ru/db/cabinetdoc
    echo   its.bat scrape https://its.1c.ru/db/cabinetdoc --format json markdown --limit 10
    echo   its.bat merge out/cabinetdoc/json --max-files 100
    echo   its.bat merge out/cabinetdoc/markdown --merge-stats
    exit /b 1
)

if "%~1"=="help" (
    echo 1С ИТС Scraper - Справка
    echo.
    echo СКРАПИНГ:
    echo   its.bat scrape [URL] [опции]
    echo.
    echo   Опции скрапинга:
    echo     --format json|markdown|txt|pdf  - Форматы вывода
    echo     --limit N                       - Ограничить количество статей
    echo     --verbose                       - Подробный вывод
    echo     --timeout N                     - Таймаут загрузки страниц
    echo.
    echo ОБЪЕДИНЕНИЕ:
    echo   its.bat merge [директория] [опции]
    echo.
    echo   Опции объединения:
    echo     --max-files N                   - Максимум файлов в группе
    echo     --max-size N                    - Максимальный размер группы (MB)
    echo     --merge-stats                   - Показать статистику
    echo     --compress                      - Сжать результат
    echo.
    exit /b 0
)

if "%~1"=="scrape" (
    shift
    call scrape.bat %*
    exit /b 0
)

if "%~1"=="merge" (
    shift
    call merge.bat %*
    exit /b 0
)

echo [ERROR] Неизвестная команда: %~1
echo Используйте: its.bat help
exit /b 1
