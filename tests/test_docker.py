"""
Тесты для Docker контейнера
"""
import os
import subprocess
import tempfile
import pytest
from pathlib import Path


class TestDocker:
    """Тесты для Docker функциональности."""
    
    @pytest.fixture
    def image_name(self):
        """Имя Docker образа для тестирования."""
        return "scraping-its:test"
    
    @pytest.fixture
    def temp_dir(self):
        """Временная директория для тестов."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            yield Path(tmp_dir)
    
    def test_docker_build(self, image_name):
        """Тест сборки Docker образа."""
        # Проверяем наличие Docker
        try:
            subprocess.run(["docker", "--version"], 
                         capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pytest.skip("Docker не установлен или недоступен")
        
        # Собираем образ
        result = subprocess.run(
            ["docker", "build", "-t", image_name, "."],
            capture_output=True, text=True, cwd=os.getcwd()
        )
        
        assert result.returncode == 0, f"Ошибка сборки: {result.stderr}"
    
    def test_docker_run_help(self, image_name):
        """Тест запуска Docker контейнера с --help."""
        try:
            subprocess.run(["docker", "--version"], 
                         capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pytest.skip("Docker не установлен или недоступен")
        
        # Запускаем контейнер с --help
        result = subprocess.run([
            "docker", "run", "--rm",
            "-v", f"{os.getcwd()}/out:/app/out",
            "-v", f"{os.getcwd()}/merge:/app/merge",
            image_name, "--help"
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Ошибка запуска: {result.stderr}"
        assert "usage:" in result.stdout.lower() or "аргументы" in result.stdout.lower()
    
    def test_docker_run_merge_stats(self, image_name, temp_dir):
        """Тест запуска Docker контейнера с --merge-stats."""
        try:
            subprocess.run(["docker", "--version"], 
                         capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pytest.skip("Docker не установлен или недоступен")
        
        # Создаем тестовую структуру
        test_out_dir = temp_dir / "out" / "cabinetdoc" / "json"
        test_out_dir.mkdir(parents=True)
        
        # Создаем тестовый JSON файл
        test_file = test_out_dir / "test.json"
        test_file.write_text('{"test": "data"}')
        
        # Запускаем контейнер с --merge-stats
        result = subprocess.run([
            "docker", "run", "--rm",
            "-v", f"{temp_dir}/out:/app/out",
            "-v", f"{temp_dir}/merge:/app/merge",
            image_name, "--merge", "--merge-dir", "out/cabinetdoc/json", "--merge-stats"
        ], capture_output=True, text=True)
        
        # Проверяем, что команда выполнилась (может быть 0 или 1 в зависимости от наличия данных)
        assert result.returncode in [0, 1], f"Неожиданный код выхода: {result.returncode}"
    
    def test_docker_image_size(self, image_name):
        """Тест размера Docker образа."""
        try:
            subprocess.run(["docker", "--version"], 
                         capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pytest.skip("Docker не установлен или недоступен")
        
        # Получаем информацию об образе
        result = subprocess.run([
            "docker", "images", image_name, "--format", "{{.Size}}"
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Ошибка получения информации об образе: {result.stderr}"
        
        # Проверяем, что образ не слишком большой (менее 3GB)
        size_str = result.stdout.strip()
        if "GB" in size_str:
            size_gb = float(size_str.replace("GB", ""))
            assert size_gb < 3.0, f"Образ слишком большой: {size_str}"
    
    def test_docker_environment_variables(self, image_name):
        """Тест переменных окружения в Docker контейнере."""
        try:
            subprocess.run(["docker", "--version"], 
                         capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pytest.skip("Docker не установлен или недоступен")
        
        # Запускаем контейнер и проверяем переменные окружения
        result = subprocess.run([
            "docker", "run", "--rm", "--entrypoint", "",
            "-e", "TEST_VAR=test_value",
            image_name, "python", "-c", "import os; print(os.environ.get('TEST_VAR', 'NOT_FOUND'))"
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Ошибка запуска: {result.stderr}"
        assert "test_value" in result.stdout
    
    def test_docker_volumes(self, image_name, temp_dir):
        """Тест монтирования volumes в Docker контейнере."""
        try:
            subprocess.run(["docker", "--version"], 
                         capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pytest.skip("Docker не установлен или недоступен")
        
        # Создаем тестовый файл
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")
        
        # Запускаем контейнер с монтированием volume
        result = subprocess.run([
            "docker", "run", "--rm", "--entrypoint", "",
            "-v", f"{temp_dir}:/app/test_volume",
            image_name, "python", "-c", 
            "import os; print(os.path.exists('/app/test_volume/test.txt'))"
        ], capture_output=True, text=True)
        
        assert result.returncode == 0, f"Ошибка запуска: {result.stderr}"
        assert "True" in result.stdout
    
    def test_docker_healthcheck(self, image_name):
        """Тест healthcheck Docker контейнера."""
        try:
            subprocess.run(["docker", "--version"], 
                         capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            pytest.skip("Docker не установлен или недоступен")
        
        # Запускаем контейнер в фоне
        container_id = subprocess.run([
            "docker", "run", "-d",
            "-v", f"{os.getcwd()}/out:/app/out",
            "-v", f"{os.getcwd()}/merge:/app/merge",
            image_name, "sleep", "30"
        ], capture_output=True, text=True)
        
        if container_id.returncode != 0:
            pytest.skip("Не удалось запустить контейнер для теста healthcheck")
        
        try:
            # Проверяем healthcheck
            result = subprocess.run([
                "docker", "inspect", "--format", "{{.State.Health.Status}}", 
                container_id.stdout.strip()
            ], capture_output=True, text=True)
            
            # Healthcheck может быть в разных состояниях
            assert result.returncode == 0, f"Ошибка проверки healthcheck: {result.stderr}"
            
        finally:
            # Останавливаем контейнер
            subprocess.run(["docker", "stop", container_id.stdout.strip()], 
                         capture_output=True)
            subprocess.run(["docker", "rm", container_id.stdout.strip()], 
                         capture_output=True)
