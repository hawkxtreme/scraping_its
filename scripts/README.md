# 📁 Scripts Directory

Эта директория содержит вспомогательные скрипты для работы с проектом.

## 🐧 **Linux/macOS скрипты (.sh)**

- `scrape.sh` - скрапинг документации
- `merge.sh` - объединение файлов  
- `its.sh` - универсальный скрипт

## 🐳 **Docker скрипты**

- `docker-build.sh` / `docker-build.bat` - сборка Docker образа
- `docker-run.sh` / `docker-run.bat` - запуск контейнера
- `docker-dev.sh` - режим разработки
- `docker-test.sh` - тестирование контейнера

## 📋 **Использование**

### Linux/macOS:
```bash
# Сделать исполняемыми
chmod +x *.sh

# Запуск
./scrape.sh https://its.1c.ru/db/cabinetdoc --format json
./merge.sh out/cabinetdoc/json --max-files 100
./its.sh help
```

### Docker:
```bash
# Сборка образа
./scripts/docker-build.sh

# Запуск контейнера
./scripts/docker-run.sh --help

# Режим разработки
./scripts/docker-dev.sh
```

## 🎯 **Основные скрипты**

Для ежедневного использования рекомендуется использовать основные скрипты в корне проекта:
- `scrape.bat` - скрапинг (Windows)
- `merge.bat` - объединение файлов (Windows)
- `its.bat` - универсальный скрипт (Windows)

