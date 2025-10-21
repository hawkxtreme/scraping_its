import os
import sys
import asyncio
from dotenv import load_dotenv

try:
    from playwright.async_api import async_playwright
except ImportError:
    # This case is handled more gracefully in check_dependencies, 
    # but it's here as a safeguard.
    pass

# Load environment variables from .env file
load_dotenv()

# Credentials and Browserless URL
LOGIN_1C_USER = os.environ.get("LOGIN_1C_USER")
LOGIN_1C_PASSWORD = os.environ.get("LOGIN_1C_PASSWORD")
BROWSERLESS_URL = os.environ.get('BROWSERLESS_URL', 'http://localhost:3000')

# Base URL for the site
BASE_URL = "https://its.1c.ru"
LOGIN_URL = "https://login.1c.ru/login"

# --- Directory Setup ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# Global variable for the dynamic output directory
dynamic_output_dir = None

# Global variables for timeouts and retry configuration
_PAGE_TIMEOUT = 90000  # milliseconds (default 90 seconds)
_NETWORK_TIMEOUT = 60000  # milliseconds (default 60 seconds)
_RETRY_COUNT = 3
_RETRY_DELAY = 2.0  # seconds
_REQUEST_DELAY = 0.5  # seconds

def set_output_dir(name):
    """Sets the dynamic output directory."""
    global dynamic_output_dir
    dynamic_output_dir = os.path.join(PROJECT_ROOT, "out", name)

def get_output_dir():
    """Gets the current output directory."""
    if dynamic_output_dir:
        return dynamic_output_dir
    return os.path.join(PROJECT_ROOT, "out")

def set_timeouts(page_timeout=None, network_timeout=None, retry_count=None, retry_delay=None, request_delay=None):
    """
    Set global timeout and retry configuration.
    
    Args:
        page_timeout (int): Page load timeout in seconds
        network_timeout (int): Network operation timeout in seconds
        retry_count (int): Number of retry attempts
        retry_delay (float): Initial delay between retries in seconds
        request_delay (float): Delay between requests in seconds
    """
    global _PAGE_TIMEOUT, _NETWORK_TIMEOUT, _RETRY_COUNT, _RETRY_DELAY, _REQUEST_DELAY
    
    if page_timeout is not None:
        if page_timeout < 10 or page_timeout > 300:
            raise ValueError("Page timeout must be between 10 and 300 seconds")
        _PAGE_TIMEOUT = page_timeout * 1000  # Convert to milliseconds
    
    if network_timeout is not None:
        if network_timeout < 5 or network_timeout > 180:
            raise ValueError("Network timeout must be between 5 and 180 seconds")
        _NETWORK_TIMEOUT = network_timeout * 1000  # Convert to milliseconds
    
    if retry_count is not None:
        if retry_count < 0 or retry_count > 10:
            raise ValueError("Retry count must be between 0 and 10")
        _RETRY_COUNT = retry_count
    
    if retry_delay is not None:
        if retry_delay < 0.1 or retry_delay > 60:
            raise ValueError("Retry delay must be between 0.1 and 60 seconds")
        _RETRY_DELAY = retry_delay
    
    if request_delay is not None:
        if request_delay < 0 or request_delay > 10:
            raise ValueError("Request delay must be between 0 and 10 seconds")
        _REQUEST_DELAY = request_delay

def get_page_timeout():
    """Get page load timeout in milliseconds."""
    return _PAGE_TIMEOUT

def get_network_timeout():
    """Get network operation timeout in milliseconds."""
    return _NETWORK_TIMEOUT

def get_retry_count():
    """Get number of retry attempts."""
    return _RETRY_COUNT

def get_retry_delay():
    """Get initial retry delay in seconds."""
    return _RETRY_DELAY

def get_request_delay():
    """Get delay between requests in seconds."""
    return _REQUEST_DELAY

def get_tmp_index_dir():
    """Gets the temporary index directory."""
    return os.path.join(get_output_dir(), "tmp_index")

def get_json_dir():
    """Gets the JSON output directory."""
    return os.path.join(get_output_dir(), "json")

def get_pdf_dir():
    """Gets the PDF output directory."""
    return os.path.join(get_output_dir(), "pdf")

def get_txt_dir():
    """Gets the TXT output directory."""
    return os.path.join(get_output_dir(), "txt")

def get_markdown_dir():
    """Gets the Markdown output directory."""
    return os.path.join(get_output_dir(), "markdown")


async def check_dependencies(log_func):
    """
    Checks for necessary dependencies and configurations.

    Args:
        log_func: The logging object (ScraperLogger instance).

    Returns:
        bool: True if all checks pass, False otherwise.
    """
    success = True
    log_func.info("Step 1: Checking dependencies...")

    # Check for required libraries
    try:
        import playwright
        import dotenv
        import bs4
        import markdownify
        log_func.info("All required libraries are installed", status="OK")
    except ImportError as e:
        success = False
        log_func.error(f"A required library is not installed: {e.name}", library=e.name)
        log_func.info("Please install the required libraries by running the following command:")
        log_func.info("pip install -r requirements.txt")
        return False

    # Check credentials
    if (not LOGIN_1C_USER or LOGIN_1C_USER == "your_login" or
            not LOGIN_1C_PASSWORD or LOGIN_1C_PASSWORD == "your_password"):
        success = False
        error_msg = "Credentials not found or are default in .env file. Please create and fill out the .env file."
        print(error_msg)
        log_func.error(error_msg, status="FAIL")
        log_func.warning("Suggestion: Create .env file with LOGIN_1C_USER and LOGIN_1C_PASSWORD")
        return False
    else:
        log_func.info("Credentials found", status="OK")

    # Check browserless service
    try:
        async with async_playwright() as p:
            browser = await p.chromium.connect_over_cdp(BROWSERLESS_URL, timeout=5000)
            await browser.close()
        log_func.info(f"Browserless service is running", url=BROWSERLESS_URL, status="OK")
    except Exception as e:
        success = False
        error_msg = f"Browserless service not found at {BROWSERLESS_URL}."
        print(error_msg)
        log_func.error(error_msg, url=BROWSERLESS_URL, status="FAIL")
        log_func.log_error_with_context(e, "check_browserless", url=BROWSERLESS_URL)
        return False

    if success:
        log_func.info("All dependency checks passed", status="SUCCESS")

    return success