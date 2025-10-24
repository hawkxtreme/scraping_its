@echo off
REM Скрипт для запуска Docker контейнера в Windows

REM Установка кодировки UTF-8
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

REM Проверка наличия Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker не установлен или не найден в PATH
    exit /b 1
)

REM Проверка наличия .env файла
if not exist ".env" (
    echo [WARNING] .env файл не найден. Создайте его на основе .env-example
    if exist ".env-example" (
        echo [INFO] Копирую .env-example в .env...
        copy .env-example .env
        echo [WARNING] Отредактируйте .env файл с вашими учетными данными
    )
)

REM Создание необходимых директорий
if not exist "out" mkdir out
if not exist "merge" mkdir merge

REM Определение образа
set IMAGE_NAME=scraping-its:latest

REM Проверка существования образа
docker image inspect %IMAGE_NAME% >nul 2>&1
if errorlevel 1 (
    echo [INFO] Образ %IMAGE_NAME% не найден. Собираю...
    docker build -t %IMAGE_NAME% .
    if errorlevel 1 (
        echo [ERROR] Ошибка при сборке образа
        exit /b 1
    )
    echo [SUCCESS] Образ собран успешно
)

REM Запуск контейнера
echo [INFO] Запускаю контейнер с аргументами: %*
docker run -it --rm --name scraping-its-run -v "%cd%\out:/app/out" -v "%cd%\merge:/app/merge" -v "%cd%\.env:/app/.env:ro" -e PYTHONUNBUFFERED=1 %IMAGE_NAME% %*

if errorlevel 1 (
    echo [ERROR] Ошибка при запуске контейнера
    exit /b 1
)

echo [SUCCESS] Контейнер завершил работу
