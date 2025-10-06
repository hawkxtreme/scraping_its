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

# Timeout settings (in seconds)
DEFAULT_PAGE_TIMEOUT = 90000  # 90 seconds
DEFAULT_LOGIN_TIMEOUT = 60000  # 60 seconds
DEFAULT_NETWORK_IDLE_TIMEOUT = 30000  # 30 seconds
DEFAULT_WORKER_TIMEOUT = 300  # 5 minutes for worker operations

# Rate limiting settings
DEFAULT_REQUEST_DELAY = 0.5  # seconds between requests
DEFAULT_MAX_RETRIES = 3  # maximum number of retries for failed requests
DEFAULT_RETRY_DELAY = 2.0  # seconds to wait between retries

# Global variables for configurable settings
page_timeout = DEFAULT_PAGE_TIMEOUT
login_timeout = DEFAULT_LOGIN_TIMEOUT
network_idle_timeout = DEFAULT_NETWORK_IDLE_TIMEOUT
worker_timeout = DEFAULT_WORKER_TIMEOUT
request_delay = DEFAULT_REQUEST_DELAY
max_retries = DEFAULT_MAX_RETRIES
retry_delay = DEFAULT_RETRY_DELAY

# --- Directory Setup ---
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)

# Global variable for the dynamic output directory
dynamic_output_dir = None

def set_output_dir(name):
    """Sets the dynamic output directory."""
    global dynamic_output_dir
    dynamic_output_dir = os.path.join(PROJECT_ROOT, "out", name)

def get_output_dir():
    """Gets the current output directory."""
    if dynamic_output_dir:
        return dynamic_output_dir
    return os.path.join(PROJECT_ROOT, "out")

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

def get_docx_dir():
    """Gets the DOCX output directory."""
    return os.path.join(get_output_dir(), "docx")

def set_timeout_settings(page_timeout_ms=None, login_timeout_ms=None,
                        network_idle_timeout_ms=None, worker_timeout_sec=None):
    """Set timeout settings."""
    global page_timeout, login_timeout, network_idle_timeout, worker_timeout
    
    if page_timeout_ms is not None:
        page_timeout = page_timeout_ms
    if login_timeout_ms is not None:
        login_timeout = login_timeout_ms
    if network_idle_timeout_ms is not None:
        network_idle_timeout = network_idle_timeout_ms
    if worker_timeout_sec is not None:
        worker_timeout = worker_timeout_sec

def set_rate_limiting(request_delay_sec=None, max_retries_count=None, retry_delay_sec=None):
    """Set rate limiting settings."""
    global request_delay, max_retries, retry_delay
    
    if request_delay_sec is not None:
        request_delay = request_delay_sec
    if max_retries_count is not None:
        max_retries = max_retries_count
    if retry_delay_sec is not None:
        retry_delay = retry_delay_sec

def get_timeout_settings():
    """Get current timeout settings."""
    return {
        'page_timeout': page_timeout,
        'login_timeout': login_timeout,
        'network_idle_timeout': network_idle_timeout,
        'worker_timeout': worker_timeout
    }

def get_rate_limiting_settings():
    """Get current rate limiting settings."""
    return {
        'request_delay': request_delay,
        'max_retries': max_retries,
        'retry_delay': retry_delay
    }


async def check_dependencies(log_func):
    """
    Checks for necessary dependencies and configurations.

    Args:
        log_func (function): The logging function.

    Returns:
        bool: True if all checks pass, False otherwise.
    """
    success = True
    log_func("Step 1: Checking dependencies...")

    # Check for required libraries
    try:
        import playwright
        import dotenv
        import bs4
        import markdownify
        log_func.logger.info("  - [OK] All required libraries are installed.")
    except ImportError as e:
        success = False
        log_func.logger.error(f"A required library is not installed: {e.name}")
        log_func.logger.error("Please install the required libraries by running the following command:")
        log_func.logger.error("pip install -r requirements.txt")
        log_func.logger.error(f"Result: Failed - Missing library: {e.name}")
        return False

    # Check for optional libraries
    try:
        import docx
        log_func.logger.info("  - [OK] python-docx library is available (DOCX format supported).")
    except ImportError:
        log_func.logger.warning("  - [WARN] python-docx library not found. DOCX format will not be available.")
        log_func.logger.warning("  To install: pip install python-docx")

    # Check credentials
    if (not LOGIN_1C_USER or LOGIN_1C_USER == "your_login" or
            not LOGIN_1C_PASSWORD or LOGIN_1C_PASSWORD == "your_password"):
        success = False
        error_msg = "Credentials not found or are default in .env file. Please create and fill out the .env file."
        print(error_msg)
        log_func(f"  - [FAIL] {error_msg}")
        log_func("Result: Failed - Credentials not set.")
        return False
    else:
        log_func("  - [OK] Credentials found.")

    # Check browserless service
    try:
        async with async_playwright() as p:
            browser = await p.chromium.connect_over_cdp(BROWSERLESS_URL, timeout=5000)
            await browser.close()
        log_func(f"  - [OK] Browserless service is running at {BROWSERLESS_URL}.")
    except Exception as e:
        success = False
        error_msg = f"Browserless service not found at {BROWSERLESS_URL}."
        print(error_msg)
        log_func(f"  - [FAIL] {error_msg}")
        log_func(f"    Error: {e}")
        log_func(f"Result: Failed - Browserless service not available: {e}")
        return False

    if success:
        log_func("All dependency checks passed.")

    return success