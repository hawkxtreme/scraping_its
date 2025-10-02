import os
from datetime import datetime

def setup_logger(output_dir):
    """
    Sets up the logger.

    Args:
        output_dir (str): The directory where the log file will be saved.

    Returns:
        function: A function that can be called to log messages.
    """
    os.makedirs(output_dir, exist_ok=True)
    log_file_path = os.path.join(output_dir, "script_log.txt")
    
    # Ensure the log file is empty before starting
    with open(log_file_path, "w", encoding="utf-8") as f:
        pass

    def log(message):
        """
        Writes a message to the log file.
        """
        with open(log_file_path, "a", encoding="utf-8") as f:
            f.write(f"{message}\n")

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log(f"---")
    log(f"Script started at: {timestamp}")
    
    return log
