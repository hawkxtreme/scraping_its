import sys
import shutil
import traceback
from datetime import datetime

class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header():
    """Prints the application header."""
    print(f"""
    {Colors.HEADER}*****************************************************************
    *                                                               *
    *        ITS.1C.RU Article Scraper & Exporter v1.1              *
    *                                                               *
    *****************************************************************{Colors.ENDC}
    """)

def print_info(message):
    """Prints an informational message."""
    print(f"{Colors.BLUE}[INFO]{Colors.ENDC} {message}")

def print_success(message):
    """Prints a success message."""
    print(f"{Colors.GREEN}[SUCCESS]{Colors.ENDC} {message}")

def print_warning(message):
    """Prints a warning message."""
    print(f"{Colors.WARNING}[WARNING]{Colors.ENDC} {message}")

def print_error(message, exception=None, show_traceback=False):
    """Prints an error message with optional exception details."""
    print(f"{Colors.FAIL}[ERROR]{Colors.ENDC} {message}", file=sys.stderr)
    
    if exception:
        print(f"{Colors.FAIL}Exception details:{Colors.ENDC} {str(exception)}", file=sys.stderr)
        
    if show_traceback and exception:
        print(f"{Colors.FAIL}Traceback:{Colors.ENDC}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)

def print_fatal_error(message, exception=None, log_func=None, show_traceback=True):
    """
    Prints a fatal error message to the console, logs it, and exits.

    Args:
        message (str): The error message to display.
        exception (Exception, optional): The exception that caused the error.
        log_func (function, optional): The logging function to use. Defaults to None.
        show_traceback (bool): Whether to show the full traceback. Defaults to True.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    error_message = f"FATAL ERROR at {timestamp}: {message}"
    
    print(f"\n\n{Colors.BOLD}{Colors.FAIL}{error_message}{Colors.ENDC}", file=sys.stderr)
    
    if exception:
        print(f"{Colors.FAIL}Exception type:{Colors.ENDC} {type(exception).__name__}", file=sys.stderr)
        print(f"{Colors.FAIL}Exception details:{Colors.ENDC} {str(exception)}", file=sys.stderr)
        
    if show_traceback and exception:
        print(f"{Colors.FAIL}Full traceback:{Colors.ENDC}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
    
    print(f"\n{Colors.FAIL}The application will now exit.{Colors.ENDC}", file=sys.stderr)
    
    if log_func:
        # Use the advanced logger if available
        if hasattr(log_func, 'logger'):
            log_func.logger.critical(message, exception)
        else:
            log_func(error_message)
            if exception:
                log_func(f"Exception details: {str(exception)}")
    
    sys.exit(1)

def print_step(step_number, step_name, details=None):
    """Prints a step in the process."""
    print(f"\n{Colors.CYAN}Step {step_number}: {step_name}{Colors.ENDC}")
    if details:
        print(f"  {details}")

def print_progress(current, total, item_description="items", show_percentage=True):
    """Prints progress information."""
    if total > 0:
        percentage = (current / total) * 100
        if show_percentage:
            print(f"{Colors.CYAN}Progress:{Colors.ENDC} {current}/{total} {item_description} ({percentage:.1f}%)")
        else:
            print(f"{Colors.CYAN}Progress:{Colors.ENDC} {current}/{total} {item_description}")
    else:
        print(f"{Colors.CYAN}Progress:{Colors.ENDC} {current} {item_description}")

def print_performance(operation, duration, details=None):
    """Prints performance metrics."""
    print(f"{Colors.GREEN}PERFORMANCE:{Colors.ENDC} {operation} completed in {duration:.2f} seconds")
    if details:
        print(f"  {details}")

def print_debug(message, log_func=None):
    """Prints a debug message (only if debug mode is enabled)."""
    if log_func and hasattr(log_func, 'logger') and log_func.logger.min_level.value <= 10:  # DEBUG level
        print(f"{Colors.CYAN}[DEBUG]{Colors.ENDC} {message}")
        log_func.logger.debug(message)

def print_separator(char="=", length=60):
    """Prints a separator line."""
    print(char * length)