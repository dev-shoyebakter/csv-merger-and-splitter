import os
from pathlib import Path

# Application Information
APP_NAME = "CSV & Excel Manager Pro"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Shoyeb Akter"
APP_DESCRIPTION = "Professional CSV and Excel file merger, splitter, and converter"

# File Paths
BASE_DIR = Path(__file__).parent
LOGS_DIR = BASE_DIR / "logs"
CONFIG_DIR = BASE_DIR / "config"
RECENT_FILES_PATH = CONFIG_DIR / "recent_files.json"

# Create directories if they don't exist
LOGS_DIR.mkdir(exist_ok=True)
CONFIG_DIR.mkdir(exist_ok=True)

# Supported File Types
SUPPORTED_EXTENSIONS = {
    'csv': ['.csv'],
    'excel': ['.xlsx', '.xls', '.xlsm'],
    'all': ['.csv', '.xlsx', '.xls', '.xlsm']
}

# CSV Delimiters
CSV_DELIMITERS = {
    'Comma (,)': ',',
    'Semicolon (;)': ';',
    'Tab (\\t)': '\t',
    'Pipe (|)': '|',
    'Space ( )': ' '
}

# Encoding Options
ENCODING_OPTIONS = [
    'utf-8',
    'utf-16',
    'latin-1',
    'iso-8859-1',
    'cp1252',
    'ascii'
]

# GUI Settings
WINDOW_SIZE = "1200x800"
WINDOW_MIN_SIZE = (1000, 700)
THEME_MODE = "dark"
COLOR_THEME = "blue"

# Preview Settings
PREVIEW_ROWS = 20
MAX_RECENT_FILES = 10

# Processing Settings
DEFAULT_CHUNK_SIZE = 10000
MAX_ROWS_WARNING = 100000

# Colors
COLORS = {
    'button': '#E5FF01',               # Lemon-Lime for buttons only
    'button_hover': '#F0FF4D',         # Lighter lemon-lime on hover
    'toggle_active': '#E5FF01',        # Lemon-Lime for active toggle
    'text': '#FFFFFF',                 # White text
    'bg_dark': '#1a1a1a',             # Dark background
    'success': '#2fa572',
    'warning': '#e67e22',
    'danger': '#e74c3c'
}