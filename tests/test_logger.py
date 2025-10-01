import pytest
import os
from unittest.mock import patch, mock_open
from src import logger

def test_setup_logger_creates_log_file():
    """Тест создания лог-файла."""
    test_output_dir = "/tmp/test_output"
    
    # Мокаем open, чтобы не создавать реальный файл
    with patch("builtins.open", mock_open()) as mock_file:
        with patch('src.logger.os.path.join', return_value="/tmp/test_output/script_log.txt"):
            log_func = logger.setup_logger(test_output_dir)
            
            # Проверяем, что функция возвращается
            assert callable(log_func)
            
            # Проверяем, что файл был открыт для записи (первый вызов)
            # setup_logger открывает файл 3 раза: 1 для очистки в "w" режиме, 2 для логирования в "a" режиме
            assert mock_file.call_count >= 1
            # First call should be with "w" mode
            mock_file.assert_any_call("/tmp/test_output/script_log.txt", "w", encoding="utf-8")

def test_logger_logs_message():
    """Тест логирования сообщений."""
    test_output_dir = "/tmp/test_output"
    test_message = "Test log message"
    
    # Мокаем open и os.path.join
    with patch("builtins.open", mock_open()) as mock_file:
        with patch('src.logger.os.path.join', return_value="/tmp/test_output/script_log.txt"):
            log_func = logger.setup_logger(test_output_dir)
            
            # Логируем сообщение
            log_func(test_message)
            
            # Проверяем, что сообщение было записано
            handle = mock_file()
            handle.write.assert_called()