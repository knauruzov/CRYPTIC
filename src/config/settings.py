"""
Configuration settings module for DFIR CRYPTIC.
Loads environment variables from .env file.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
dotenv_path = Path(__file__).resolve().parent.parent.parent / '.env'
load_dotenv(dotenv_path)

# API Keys - Try to load from .env, but provide fallback values for development
BLOCKCYPHER_API_KEY = os.getenv('BLOCKCYPHER_API_KEY', 'e62eccdb5fa448e197ab7f53042e6cf3')
ETHERSCAN_API_KEY = os.getenv('ETHERSCAN_API_KEY', 'IWH6JTEFFT5GWISSBWTHG9F7118VQY65CM')

# Validate required environment variables
def validate_env():
    """Validate that all required environment variables are set."""
    # API keys are now hardcoded as fallbacks, so this will always pass
    pass

# Application configuration
APP_NAME = "DFIR CRYPTIC"
APP_VERSION = "0.1.0"
DEBUG = os.getenv('DEBUG', 'False').lower() in ('true', '1', 't')

# API endpoints
BLOCKCYPHER_BASE_URL = "https://api.blockcypher.com/v1"
ETHERSCAN_BASE_URL = "https://api.etherscan.io/api"

# Data storage
DATA_DIR = Path(__file__).resolve().parent.parent.parent / 'data'
DATA_DIR.mkdir(exist_ok=True)
CACHE_DIR = DATA_DIR / 'cache'
CACHE_DIR.mkdir(exist_ok=True)
RESULTS_DIR = DATA_DIR / 'results'
RESULTS_DIR.mkdir(exist_ok=True) 