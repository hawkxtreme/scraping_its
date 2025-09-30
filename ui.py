import sys
import shutil

def print_header():
    """Prints the application header."""
    print("""
    *****************************************************************
    *                                                               *
    *        ITS.1C.RU Article Scraper & Exporter v1.0              *
    *                                                               *
    *****************************************************************
    """)

def print_fatal_error(message, log_func=None):
    """
    Prints a fatal error message to the console, logs it, and exits.

    Args:
        message (str): The error message to display.
        log_func (function, optional): The logging function to use. Defaults to None.
    """
    error_message = f"FATAL ERROR: {message}"
    print(f"\n\n{error_message}", file=sys.stderr)
    print("The application will now exit.", file=sys.stderr)
    if log_func:
        log_func(error_message)
    sys.exit(1)

def print_progress(current, total, stage, title):
    """
    Displays a progress bar in the console.

    Args:
        current (int): The current item number.
        total (int): The total number of items.
        stage (str): The current stage of the process (e.g., 'Discovering', 'Scraping').
        title (str): The title of the item being processed.
    """
    if total == 0:
        progress = 1.0
    else:
        progress = current / total
    
    bar_length = 30
    filled_len = int(bar_length * progress)
    bar = '█' * filled_len + '─' * (bar_length - filled_len)
    percent = progress * 100
    
    info_str = f"{stage}: ({current}/{total}) {title}"
    
    try:
        terminal_width = shutil.get_terminal_size().columns
    except OSError: # Fallback for environments without a terminal (e.g., CI/CD)
        terminal_width = 80
        
    max_info_len = terminal_width - (bar_length + 10)
    if len(info_str) > max_info_len > 0:
        info_str = info_str[:max_info_len - 3] + "..."
        
    progress_str = f"Progress: [{bar}] {percent:.1f}% | {info_str}"
    # Pad with spaces to clear the rest of the line
    output_str = f"\r{progress_str.ljust(terminal_width)}"

    try:
        sys.stdout.write(output_str)
    except UnicodeEncodeError:
        # Fallback for terminals that don't support the output encoding
        sys.stdout.buffer.write(output_str.encode('utf-8', 'replace'))
    
    sys.stdout.flush()