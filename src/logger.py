import os
import threading
from datetime import datetime

def setup_logger(output_dir):
    """
    Sets up a thread-safe logger.

    Args:
        output_dir (str): The directory where the log file will be saved.

    Returns:
        function: A function that can be called to log messages.
    """
    os.makedirs(output_dir, exist_ok=True)
    log_file_path = os.path.join(output_dir, "script_log.txt")
    log_lock = threading.Lock()
    
    # Ensure the log file is empty before starting
    with open(log_file_path, "w", encoding="utf-8") as f:
        pass

    def log(message):
        """
        Writes a message to the log file in a thread-safe manner.
        """
        with log_lock:
            with open(log_file_path, "a", encoding="utf-8") as f:
                f.write(f"{message}\n")

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log(f"---")
    log(f"Script started at: {timestamp}")
    
    return log
