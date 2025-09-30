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
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "out")

# Article directories
BASE_ARTICLES_DIR = os.path.join(OUTPUT_DIR, "articles")
TMP_INDEX_DIR = os.path.join(OUTPUT_DIR, "tmp_index")
JSON_DIR = os.path.join(BASE_ARTICLES_DIR, "json")
PDF_DIR = os.path.join(BASE_ARTICLES_DIR, "pdf")
TXT_DIR = os.path.join(BASE_ARTICLES_DIR, "txt")
MARKDOWN_DIR = os.path.join(BASE_ARTICLES_DIR, "markdown")


async def check_dependencies(log_func):
    """
    Checks for necessary dependencies and configurations.

    Args:
        log_func (function): The logging function.

    Returns:
        bool: True if all checks pass, False otherwise.
    """
    log_func("Step 1: Checking dependencies...")

    # Check for required libraries
    try:
        import playwright
        import dotenv
        import bs4
        import markdownify
    except ImportError as e:
        log_func(f"[ERROR] A required library is not installed: {e.name}")
        log_func("Please install the required libraries by running the following command:")
        log_func("pip install -r requirements.txt")
        log_func(f"Result: Failed - Missing library: {e.name}")
        return False

    # Check credentials
    if not LOGIN_1C_USER or not LOGIN_1C_PASSWORD or LOGIN_1C_USER == "your_username":
        log_func("  - [FAIL] Credentials not found in .env file.")
        log_func("Result: Failed - Credentials not set.")
        return False
    log_func("  - [OK] Credentials found.")

    # Check browserless service
    try:
        async with async_playwright() as p:
            browser = await p.chromium.connect_over_cdp(BROWSERLESS_URL, timeout=5000)
            await browser.close()
        log_func(f"  - [OK] Browserless service is running at {BROWSERLESS_URL}.")
    except Exception as e:
        log_func(f"  - [FAIL] Browserless service not found at {BROWSERLESS_URL}.")
        log_func(f"    Error: {e}")
        log_func(f"Result: Failed - Browserless service not available: {e}")
        return False

    log_func("All dependency checks passed.")
    return True