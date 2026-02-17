import pandas as pd
from typing import List, Dict, Optional, Callable
from pathlib import Path
from utils import logger, FileValidator, DataFrameHelper


class CSVExcelMerger:
    """Merge multiple CSV/Excel files with advanced options"""

    def __init__(self):
        self.logger = logger
        self.files: List[str] = []
        self.merged_df: Optional[pd.DataFrame] = None

    def add_files(self, file_paths: List[str]) -> Dict:
        """Add files to merge queue with validation"""
        valid_files = []
        invalid_files = []

        for file_path in file_paths:
            is_valid, message = FileValidator.is_valid_file(file_path)
            if is_valid:
                valid_files.append(file_path)
                self.logger.info(f"Added file: {file_path}")
            else:
                invalid_files.append({'file': file_path, 'error': message})
                self.logger.error(f"Invalid file: {file_path} - {message}")

        self.files.extend(valid_files)

        return {
            'valid_count': len(valid_files),
            'invalid_count': len(invalid_files),
            'invalid_files': invalid_files,
            'total_files': len(self.files)
        }

    def clear_files(self):
        """Clear all files from merge queue"""
        self.files = []
        self.merged_df = None
        self.logger.info("Cleared all files from merge queue")

    def merge_files(self,
                    keep_header: bool = True,
                    skip_empty_rows: bool = True,
                    remove_duplicates: bool = False,
                    encoding: str = 'utf-8',
                    delimiter: str = ',',
                    selected_columns: Optional[List[str]] = None,
                    sort_by_column: Optional[str] = None,
                    sort_ascending: bool = True,
                    progress_callback: Optional[Callable] = None) -> Dict:
        """
        Merge all files in queue with specified options

        Args:
            keep_header: Keep column headers from first file
            skip_empty_rows: Remove rows where all values are empty
            remove_duplicates: Remove exact duplicate rows
            encoding: Encoding for CSV files
            delimiter: Delimiter for CSV files
            selected_columns: List of columns to include (None = all)
            sort_by_column: Column name to sort by (None = no sorting)
            sort_ascending: Sort order (True = ascending, False = descending)
            progress_callback: Callback function for progress updates

        Returns:
            Dictionary with merge results and statistics
        """
        if not self.files:
            return {
                'success': False,
                'error': 'No files to merge',
                'stats': {}
            }

        try:
            dfs = []
            total_files = len(self.files)
            total_rows_before = 0
            file_info = []

            self.logger.info(f"Starting merge of {total_files} files")

            # Read all files
            for idx, file_path in enumerate(self.files):
                if progress_callback:
                    progress = (idx / total_files) * 50  # First 50% is reading
                    progress_callback(progress, f"Reading file {idx + 1}/{total_files}")

                try:
                    # Read file
                    df = DataFrameHelper.read_file(file_path, encoding, delimiter)
                    rows_before = len(df)
                    total_rows_before += rows_before

                    file_info.append({
                        'name': Path(file_path).name,
                        'rows': rows_before,
                        'columns': len(df.columns)
                    })

                    # Process based on options
                    if skip_empty_rows:
                        df = DataFrameHelper.remove_empty_rows(df)

                    # Filter columns if specified
                    if selected_columns:
                        available_columns = [col for col in selected_columns if col in df.columns]
                        if available_columns:
                            df = DataFrameHelper.filter_columns(df, available_columns)

                    dfs.append(df)
                    self.logger.info(f"Processed: {Path(file_path).name} ({rows_before} rows)")

                except Exception as e:
                    self.logger.error(f"Error reading {file_path}: {str(e)}")
                    return {
                        'success': False,
                        'error': f"Error reading {Path(file_path).name}: {str(e)}",
                        'stats': {}
                    }

            if progress_callback:
                progress_callback(50, "Merging files...")

            # Merge all dataframes
            if keep_header:
                self.merged_df = pd.concat(dfs, ignore_index=True)
            else:
                # Remove headers by skipping first row of subsequent files
                first_df = dfs[0]
                other_dfs = [df.iloc[1:] if idx > 0 else df for idx, df in enumerate(dfs)]
                self.merged_df = pd.concat(other_dfs, ignore_index=True)

            rows_after_merge = len(self.merged_df)

            if progress_callback:
                progress_callback(70, "Applying filters...")

            # Remove duplicates if requested
            rows_before_dedup = rows_after_merge
            if remove_duplicates:
                self.merged_df = DataFrameHelper.remove_duplicate_rows(self.merged_df)
                rows_after_merge = len(self.merged_df)
                duplicates_removed = rows_before_dedup - rows_after_merge
                self.logger.info(f"Removed {duplicates_removed} duplicate rows")

            # Sort if requested
            if sort_by_column and sort_by_column in self.merged_df.columns:
                if progress_callback:
                    progress_callback(85, f"Sorting by {sort_by_column}...")
                self.merged_df = DataFrameHelper.sort_dataframe(
                    self.merged_df, sort_by_column, sort_ascending
                )
                self.logger.info(f"Sorted by column: {sort_by_column}")

            if progress_callback:
                progress_callback(100, "Merge complete!")

            # Prepare statistics
            stats = {
                'files_merged': total_files,
                'total_rows_before': total_rows_before,
                'total_rows_after': rows_after_merge,
                'total_columns': len(self.merged_df.columns),
                'duplicates_removed': rows_before_dedup - rows_after_merge if remove_duplicates else 0,
                'empty_rows_skipped': skip_empty_rows,
                'file_details': file_info
            }

            self.logger.info(f"Merge completed successfully: {rows_after_merge} rows, {len(self.merged_df.columns)} columns")

            return {
                'success': True,
                'stats': stats,
                'dataframe': self.merged_df
            }

        except Exception as e:
            error_msg = f"Error during merge: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'stats': {}
            }

    def save_merged_file(self,
                         output_path: str,
                         encoding: str = 'utf-8',
                         delimiter: str = ',',
                         index: bool = False) -> Dict:
        """
        Save merged data to file

        Args:
            output_path: Path where to save the file
            encoding: Encoding for CSV files
            delimiter: Delimiter for CSV files
            index: Whether to include index column

        Returns:
            Dictionary with save results
        """
        if self.merged_df is None:
            return {
                'success': False,
                'error': 'No merged data to save. Please merge files first.'
            }

        try:
            output_path = Path(output_path)
            extension = output_path.suffix.lower()

            # Save based on file extension
            if extension == '.csv':
                self.merged_df.to_csv(
                    output_path,
                    encoding=encoding,
                    sep=delimiter,
                    index=index
                )
            elif extension in ['.xlsx', '.xls']:
                self.merged_df.to_excel(
                    output_path,
                    index=index,
                    engine='openpyxl'
                )
            else:
                return {
                    'success': False,
                    'error': f'Unsupported file extension: {extension}'
                }

            file_size = output_path.stat().st_size
            self.logger.info(f"Saved merged file: {output_path} ({DataFrameHelper.format_file_size(file_size)})")

            return {
                'success': True,
                'file_path': str(output_path),
                'file_size': DataFrameHelper.format_file_size(file_size),
                'rows': len(self.merged_df),
                'columns': len(self.merged_df.columns)
            }

        except Exception as e:
            error_msg = f"Error saving file: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg
            }

    def get_preview(self, rows: int = 20) -> Optional[pd.DataFrame]:
        """Get preview of merged data"""
        if self.merged_df is not None:
            return self.merged_df.head(rows)
        return None

    def get_column_names(self) -> List[str]:
        """Get list of column names from merged data"""
        if self.merged_df is not None:
            return list(self.merged_df.columns)
        return []

    def get_files_info(self) -> List[Dict]:
        """Get information about all files in queue"""
        return [DataFrameHelper.get_file_info(f) for f in self.files]