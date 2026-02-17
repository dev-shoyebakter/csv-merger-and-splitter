"""
Utility Functions for CSV/Excel Manager
"""
import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import pandas as pd
from config import LOGS_DIR, RECENT_FILES_PATH, MAX_RECENT_FILES


class Logger:
    """Custom logger for the application"""

    def __init__(self, name: str = "CSVExcelManager"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        # Create log file with timestamp
        log_file = LOGS_DIR / f"{name}_{datetime.now().strftime('%Y%m%d')}.log"

        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Add handlers
        if not self.logger.handlers:
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)

    def info(self, message: str):
        self.logger.info(message)

    def error(self, message: str):
        self.logger.error(message)

    def warning(self, message: str):
        self.logger.warning(message)

    def debug(self, message: str):
        self.logger.debug(message)


class RecentFilesManager:
    """Manage recently used files"""

    @staticmethod
    def load_recent_files() -> List[str]:
        """Load recent files from JSON"""
        try:
            if RECENT_FILES_PATH.exists():
                with open(RECENT_FILES_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Filter out files that no longer exist
                    return [f for f in data.get('files', []) if os.path.exists(f)]
            return []
        except Exception as e:
            print(f"Error loading recent files: {e}")
            return []

    @staticmethod
    def save_recent_file(file_path: str):
        """Add a file to recent files list"""
        try:
            recent_files = RecentFilesManager.load_recent_files()

            # Remove if already exists
            if file_path in recent_files:
                recent_files.remove(file_path)

            # Add to beginning
            recent_files.insert(0, file_path)

            # Keep only MAX_RECENT_FILES
            recent_files = recent_files[:MAX_RECENT_FILES]

            # Save to file
            with open(RECENT_FILES_PATH, 'w', encoding='utf-8') as f:
                json.dump({'files': recent_files}, f, indent=2)
        except Exception as e:
            print(f"Error saving recent file: {e}")

    @staticmethod
    def clear_recent_files():
        """Clear all recent files"""
        try:
            if RECENT_FILES_PATH.exists():
                RECENT_FILES_PATH.unlink()
        except Exception as e:
            print(f"Error clearing recent files: {e}")


class FileValidator:
    """Validate files before processing"""

    @staticmethod
    def is_valid_file(file_path: str) -> Tuple[bool, str]:
        """Check if file is valid and accessible"""
        if not file_path:
            return False, "No file path provided"

        if not os.path.exists(file_path):
            return False, f"File does not exist: {file_path}"

        if not os.path.isfile(file_path):
            return False, f"Path is not a file: {file_path}"

        if os.path.getsize(file_path) == 0:
            return False, f"File is empty: {file_path}"

        return True, "File is valid"

    @staticmethod
    def get_file_extension(file_path: str) -> str:
        """Get file extension in lowercase"""
        return Path(file_path).suffix.lower()

    @staticmethod
    def is_csv_file(file_path: str) -> bool:
        """Check if file is CSV"""
        return FileValidator.get_file_extension(file_path) == '.csv'

    @staticmethod
    def is_excel_file(file_path: str) -> bool:
        """Check if file is Excel"""
        return FileValidator.get_file_extension(file_path) in ['.xlsx', '.xls', '.xlsm']


class DataFrameHelper:
    """Helper functions for pandas DataFrames"""

    @staticmethod
    def read_file(file_path: str, encoding: str = 'utf-8', delimiter: str = ',',
                  sheet_name: int = 0) -> pd.DataFrame:
        """Read CSV or Excel file into DataFrame"""
        try:
            if FileValidator.is_csv_file(file_path):
                return pd.read_csv(file_path, encoding=encoding, delimiter=delimiter)
            elif FileValidator.is_excel_file(file_path):
                return pd.read_excel(file_path, sheet_name=sheet_name)
            else:
                raise ValueError(f"Unsupported file type: {file_path}")
        except Exception as e:
            raise Exception(f"Error reading file {file_path}: {str(e)}")

    @staticmethod
    def get_file_info(file_path: str) -> Dict:
        """Get information about a file"""
        try:
            df = DataFrameHelper.read_file(file_path)
            file_size = os.path.getsize(file_path)

            return {
                'path': file_path,
                'name': os.path.basename(file_path),
                'size': DataFrameHelper.format_file_size(file_size),
                'rows': len(df),
                'columns': len(df.columns),
                'column_names': list(df.columns),
                'extension': FileValidator.get_file_extension(file_path)
            }
        except Exception as e:
            return {
                'path': file_path,
                'error': str(e)
            }

    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """Format file size in human-readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"

    @staticmethod
    def remove_empty_rows(df: pd.DataFrame) -> pd.DataFrame:
        """Remove rows where all values are empty/null"""
        return df.dropna(how='all')

    @staticmethod
    def remove_duplicate_rows(df: pd.DataFrame) -> pd.DataFrame:
        """Remove exact duplicate rows"""
        return df.drop_duplicates()

    @staticmethod
    def filter_columns(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
        """Select specific columns from DataFrame"""
        return df[columns]

    @staticmethod
    def sort_dataframe(df: pd.DataFrame, column: str, ascending: bool = True) -> pd.DataFrame:
        """Sort DataFrame by column"""
        if column in df.columns:
            return df.sort_values(by=column, ascending=ascending)
        return df


# Initialize logger
logger = Logger()