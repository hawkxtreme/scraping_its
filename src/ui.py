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