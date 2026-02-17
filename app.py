import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from gui import run_gui
from utils import logger
from config import APP_NAME, APP_VERSION


def main():
    """Main entry point for the application"""
    try:
        print(f"Starting {APP_NAME} v{APP_VERSION}...")
        logger.info(f"Starting {APP_NAME} v{APP_VERSION}")
        # Run PyQt6 GUI
        run_gui()
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        print(f"Error starting application: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()