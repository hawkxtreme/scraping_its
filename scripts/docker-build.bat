@echo off
REM Скрипт для сборки Docker образа в Windows

REM Установка кодировки UTF-8
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

REM Параметры по умолчанию
set IMAGE_NAME=scraping-its
set TAG=latest
set NO_CACHE=

REM Обработка аргументов
:parse_args
if "%~1"=="" goto :build
if "%~1"=="-t" (
    set TAG=%~2
    shift
    shift
    goto :parse_args
)
if "%~1"=="--tag" (
    set TAG=%~2
    shift
    shift
    goto :parse_args
)
if "%~1"=="-n" (
    set IMAGE_NAME=%~2
    shift
    shift
    goto :parse_args
)
if "%~1"=="--name" (
    set IMAGE_NAME=%~2
    shift
    shift
    goto :parse_args
)
if "%~1"=="--no-cache" (
    set NO_CACHE=--no-cache
    shift
    goto :parse_args
)
if "%~1"=="-h" goto :help
if "%~1"=="--help" goto :help
echo [ERROR] Неизвестный параметр: %~1
exit /b 1

:help
echo Использование: %0 [OPTIONS]
echo Опции:
echo   -t, --tag TAG       Тег образа (по умолчанию: latest)
echo   -n, --name NAME     Имя образа (по умолчанию: scraping-its)
echo   --no-cache          Сборка без кэша
echo   -h, --help          Показать эту справку
exit /b 0

:build
set FULL_IMAGE_NAME=%IMAGE_NAME%:%TAG%

echo [INFO] Собираю Docker образ: %FULL_IMAGE_NAME%

REM Проверка наличия Dockerfile
if not exist "Dockerfile" (
    echo [ERROR] Dockerfile не найден в текущей директории
    exit /b 1
)

REM Сборка образа
docker build %NO_CACHE% -t %FULL_IMAGE_NAME% .

if errorlevel 1 (
    echo [ERROR] Ошибка при сборке образа
    exit /b 1
)

echo [SUCCESS] Образ %FULL_IMAGE_NAME% собран успешно

REM Показать информацию об образе
echo [INFO] Информация об образе:
docker images %FULL_IMAGE_NAME%

REM Тест запуска
echo [INFO] Тестирую запуск контейнера...
docker run --rm %FULL_IMAGE_NAME% --help >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Тест запуска не прошел
    exit /b 1
)

echo [SUCCESS] Тест запуска прошел успешно
