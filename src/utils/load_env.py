"""
Environment Loader

Loads .env file for the application.
"""
import os
from dotenv import load_dotenv

# Only load .env if not running tests
if not os.environ.get('PYTEST_VERSION'):
    # Load environment variables from .env file
    load_dotenv()
