import pandas as pd
from typing import Dict, Optional, Callable, List
from pathlib import Path
from utils import logger, FileValidator, DataFrameHelper


class CSVExcelSplitter:
    """Split CSV/Excel files into smaller files based on row count"""

    def __init__(self):
        self.logger = logger
        self.file_path: Optional[str] = None
        self.df: Optional[pd.DataFrame] = None

    def load_file(self,
                  file_path: str,
                  encoding: str = 'utf-8',
                  delimiter: str = ',') -> Dict:
        """
        Load file for splitting

        Args:
            file_path: Path to file to split
            encoding: Encoding for CSV files
            delimiter: Delimiter for CSV files

        Returns:
            Dictionary with load results and file info
        """
        # Validate file
        is_valid, message = FileValidator.is_valid_file(file_path)
        if not is_valid:
            return {
                'success': False,
                'error': message
            }

        try:
            # Read file
            self.df = DataFrameHelper.read_file(file_path, encoding, delimiter)
            self.file_path = file_path

            self.logger.info(f"Loaded file for splitting: {file_path} ({len(self.df)} rows)")

            return {
                'success': True,
                'file_info': {
                    'path': file_path,
                    'name': Path(file_path).name,
                    'rows': len(self.df),
                    'columns': len(self.df.columns),
                    'size': DataFrameHelper.format_file_size(Path(file_path).stat().st_size)
                }
            }

        except Exception as e:
            error_msg = f"Error loading file: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }

    def split_file(self,
                   rows_per_file: int,
                   output_dir: str,
                   base_filename: Optional[str] = None,
                   keep_header: bool = True,
                   skip_empty_rows: bool = True,
                   remove_duplicates: bool = False,
                   encoding: str = 'utf-8',
                   delimiter: str = ',',
                   output_format: Optional[str] = None,
                   progress_callback: Optional[Callable] = None) -> Dict:
        """
        Split loaded file into multiple smaller files

        Args:
            rows_per_file: Number of rows per output file
            output_dir: Directory where to save split files
            base_filename: Base name for output files (default: original filename)
            keep_header: Include header in each split file
            skip_empty_rows: Remove empty rows before splitting
            remove_duplicates: Remove duplicate rows before splitting
            encoding: Encoding for CSV files
            delimiter: Delimiter for CSV files
            output_format: Output format ('csv', 'xlsx', or None for same as input)
            progress_callback: Callback function for progress updates

        Returns:
            Dictionary with split results and statistics
        """
        if self.df is None:
            return {
                'success': False,
                'error': 'No file loaded. Please load a file first.'
            }

        if rows_per_file <= 0:
            return {
                'success': False,
                'error': 'Rows per file must be greater than 0'
            }

        try:
            # Create output directory if it doesn't exist
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            # Determine base filename
            if base_filename is None:
                base_filename = Path(self.file_path).stem

            # Determine output extension
            if output_format:
                output_ext = f'.{output_format}' if not output_format.startswith('.') else output_format
            else:
                output_ext = Path(self.file_path).suffix

            # Process dataframe
            df_to_split = self.df.copy()
            original_rows = len(df_to_split)

            if progress_callback:
                progress_callback(10, "Processing data...")

            # Skip empty rows if requested
            if skip_empty_rows:
                df_to_split = DataFrameHelper.remove_empty_rows(df_to_split)
                self.logger.info(f"Removed {original_rows - len(df_to_split)} empty rows")

            # Remove duplicates if requested
            rows_before_dedup = len(df_to_split)
            if remove_duplicates:
                df_to_split = DataFrameHelper.remove_duplicate_rows(df_to_split)
                duplicates_removed = rows_before_dedup - len(df_to_split)
                self.logger.info(f"Removed {duplicates_removed} duplicate rows")

            total_rows = len(df_to_split)
            num_files = (total_rows + rows_per_file - 1) // rows_per_file  # Ceiling division

            if progress_callback:
                progress_callback(20, f"Splitting into {num_files} files...")

            created_files = []
            total_rows_written = 0

            # Split and save
            for i in range(num_files):
                start_idx = i * rows_per_file
                end_idx = min((i + 1) * rows_per_file, total_rows)

                # Get chunk
                chunk = df_to_split.iloc[start_idx:end_idx]

                # Create filename with part number
                output_filename = f"{base_filename}_part{i + 1:04d}{output_ext}"
                output_file_path = output_path / output_filename

                # Save chunk
                if output_ext == '.csv':
                    chunk.to_csv(
                        output_file_path,
                        encoding=encoding,
                        sep=delimiter,
                        index=False,
                        header=keep_header
                    )
                elif output_ext in ['.xlsx', '.xls']:
                    chunk.to_excel(
                        output_file_path,
                        index=False,
                        header=keep_header,
                        engine='openpyxl'
                    )
                else:
                    return {
                        'success': False,
                        'error': f'Unsupported output format: {output_ext}'
                    }

                file_size = output_file_path.stat().st_size
                rows_in_file = len(chunk)
                total_rows_written += rows_in_file

                created_files.append({
                    'filename': output_filename,
                    'path': str(output_file_path),
                    'rows': rows_in_file,
                    'size': DataFrameHelper.format_file_size(file_size)
                })

                self.logger.info(f"Created: {output_filename} ({rows_in_file} rows)")

                # Update progress
                if progress_callback:
                    progress = 20 + int((i + 1) / num_files * 80)
                    progress_callback(progress, f"Created {i + 1}/{num_files} files")

            if progress_callback:
                progress_callback(100, "Split complete!")

            # Prepare statistics
            stats = {
                'original_file': Path(self.file_path).name,
                'original_rows': original_rows,
                'rows_processed': total_rows,
                'rows_per_file': rows_per_file,
                'files_created': num_files,
                'total_rows_written': total_rows_written,
                'output_directory': str(output_path),
                'duplicates_removed': rows_before_dedup - len(df_to_split) if remove_duplicates else 0,
                'empty_rows_removed': original_rows - rows_before_dedup if skip_empty_rows else 0,
                'files': created_files
            }

            self.logger.info(f"Split completed: {num_files} files created in {output_path}")

            return {
                'success': True,
                'stats': stats
            }

        except Exception as e:
            error_msg = f"Error during split: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }

    def get_preview(self, rows: int = 20) -> Optional[pd.DataFrame]:
        """Get preview of loaded data"""
        if self.df is not None:
            return self.df.head(rows)
        return None

    def get_column_names(self) -> List[str]:
        """Get list of column names"""
        if self.df is not None:
            return list(self.df.columns)
        return []

    def get_file_info(self) -> Optional[Dict]:
        """Get information about loaded file"""
        if self.file_path and self.df is not None:
            return DataFrameHelper.get_file_info(self.file_path)
        return None

    def calculate_split_info(self, rows_per_file: int) -> Dict:
        """
        Calculate how many files will be created

        Args:
            rows_per_file: Number of rows per file

        Returns:
            Dictionary with split calculation
        """
        if self.df is None or rows_per_file <= 0:
            return {
                'total_rows': 0,
                'num_files': 0,
                'rows_per_file': rows_per_file,
                'last_file_rows': 0
            }

        total_rows = len(self.df)
        num_files = (total_rows + rows_per_file - 1) // rows_per_file
        last_file_rows = total_rows - (num_files - 1) * rows_per_file

        return {
            'total_rows': total_rows,
            'num_files': num_files,
            'rows_per_file': rows_per_file,
            'last_file_rows': last_file_rows
        }