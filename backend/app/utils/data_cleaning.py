"""
Data cleaning and preprocessing utilities for uploaded files.

This module provides comprehensive data cleaning functions for CSV, TXT, and XLSX files,
including data type conversion, missing value handling, duplicate removal, and more.
"""

from typing import Dict, Any, Tuple, List
import pandas as pd
import numpy as np
import re
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataCleaner:
    """
    Comprehensive data cleaning class for various file formats.
    """

    def __init__(self):
        self.cleaning_stats = {}

    def load_file(self, file_path: str) -> pd.DataFrame:
        """
        Load file into pandas DataFrame with robust encoding detection.

        Args:
            file_path (str): Path to the file to load

        Returns:
            pd.DataFrame: Loaded DataFrame

        Raises:
            ValueError: If file cannot be loaded or format is unsupported
        """
        file_ext = file_path.lower()

        try:
            if file_ext.endswith((".csv", ".txt")):
                return self._load_csv_txt(file_path)
            elif file_ext.endswith((".xlsx", ".xls")):
                return self._load_excel(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_ext}")
        except Exception as e:
            logger.error(f"Error loading file {file_path}: {str(e)}")
            raise ValueError(f"Failed to load file: {str(e)}")

    def _load_csv_txt(self, file_path: str) -> pd.DataFrame:
        """Load CSV/TXT files with encoding detection."""
        encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']

        for encoding in encodings:
            try:
                df = pd.read_csv(file_path, encoding=encoding)
                logger.info(
                    f"Successfully loaded CSV/TXT with {encoding} encoding")
                return df
            except UnicodeDecodeError:
                continue
            except Exception as e:
                logger.warning(f"Failed to load with {encoding}: {str(e)}")
                continue

        raise ValueError("Could not decode file with any supported encoding")

    def _load_excel(self, file_path: str) -> pd.DataFrame:
        """Load Excel files."""
        try:
            df = pd.read_excel(file_path)
            logger.info("Successfully loaded Excel file")
            return df
        except Exception as e:
            raise ValueError(f"Failed to load Excel file: {str(e)}")

    def clean_dataframe(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Perform comprehensive data cleaning on a DataFrame.

        Args:
            df (pd.DataFrame): Input DataFrame to clean

        Returns:
            Tuple[pd.DataFrame, Dict[str, Any]]: Cleaned DataFrame and cleaning statistics
        """
        original_shape = df.shape
        stats = {
            'original_shape': original_shape,
            'operations_performed': [],
            'data_type_changes': {},
            'missing_values_handled': 0,
            'duplicates_removed': 0
        }

        # Step 1: Remove empty rows and columns
        df, empty_stats = self._remove_empty_data(df)
        if empty_stats['rows_removed'] > 0 or empty_stats['cols_removed'] > 0:
            stats['operations_performed'].append(
                f"Removed {empty_stats['rows_removed']} empty rows, {empty_stats['cols_removed']} empty columns")

        # Step 2: Clean column names
        df, column_stats = self._clean_column_names(df)
        if column_stats['columns_renamed'] > 0:
            stats['operations_performed'].append(
                f"Standardized {column_stats['columns_renamed']} column names")

        # Step 3: Convert data types
        df, type_stats = self._convert_data_types(df)
        stats['data_type_changes'] = type_stats
        if type_stats:
            stats['operations_performed'].append(
                f"Optimized data types for {len(type_stats)} columns")

        # Step 4: Remove duplicates
        df, duplicate_stats = self._remove_duplicates(df)
        stats['duplicates_removed'] = duplicate_stats['duplicates_removed']
        if duplicate_stats['duplicates_removed'] > 0:
            stats['operations_performed'].append(
                f"Removed {duplicate_stats['duplicates_removed']} duplicate rows")

        # Step 5: Handle missing values
        df, missing_stats = self._handle_missing_values(df)
        stats['missing_values_handled'] = missing_stats['values_filled']
        if missing_stats['values_filled'] > 0:
            stats['operations_performed'].append(
                f"Handled {missing_stats['values_filled']} missing values")

        # Final cleanup
        df = df.reset_index(drop=True)

        stats['final_shape'] = df.shape
        stats['total_rows_removed'] = original_shape[0] - df.shape[0]
        stats['total_cols_removed'] = original_shape[1] - df.shape[1]

        logger.info(f"Data cleaning completed: {original_shape} -> {df.shape}")

        return df, stats

    def _remove_empty_data(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int]]:
        """Remove entirely empty rows and columns."""
        original_shape = df.shape

        # Remove empty rows
        df = df.dropna(axis='index', how='all')

        # Remove empty columns
        df = df.dropna(axis='columns', how='all')

        # Remove unnamed columns (common in Excel exports)
        unnamed_cols = [col for col in df.columns if str(
            col).startswith("Unnamed")]
        df = df.drop(columns=unnamed_cols, errors='ignore')

        final_shape = df.shape

        return df, {
            'rows_removed': original_shape[0] - final_shape[0],
            'cols_removed': original_shape[1] - final_shape[1]
        }

    def _clean_column_names(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int]]:
        """Standardize column names."""
        if df.empty:
            return df, {'columns_renamed': 0}

        original_columns = df.columns.tolist()

        # Clean and standardize column names
        new_columns = []
        for col in df.columns:
            # Convert to string and strip whitespace
            clean_col = str(col).strip()

            # Replace spaces and special characters with underscores
            clean_col = re.sub(r'[\s\-\.]+', '_', clean_col)

            # Remove special characters except underscores
            clean_col = re.sub(r'[^\w_]', '', clean_col)

            # Convert to lowercase
            clean_col = clean_col.lower()

            # Replace multiple underscores with single
            clean_col = re.sub(r'_+', '_', clean_col)

            # Remove leading/trailing underscores
            clean_col = clean_col.strip('_')

            # Ensure column name is not empty
            if not clean_col:
                clean_col = f'column_{len(new_columns)}'

            new_columns.append(clean_col)

        # Handle duplicate column names
        final_columns = []
        for i, col in enumerate(new_columns):
            if col in final_columns:
                suffix = 1
                while f"{col}_{suffix}" in final_columns:
                    suffix += 1
                final_columns.append(f"{col}_{suffix}")
            else:
                final_columns.append(col)

        df.columns = final_columns

        columns_renamed = sum(1 for orig, new in zip(
            original_columns, final_columns) if str(orig) != new)

        return df, {'columns_renamed': columns_renamed}

    def _convert_data_types(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, str]]:
        """Convert data types intelligently."""
        type_changes = {}

        if df.empty:
            return df, type_changes

        for column in df.columns:
            original_dtype = str(df[column].dtype)

            # Skip if already numeric or boolean
            if df[column].dtype in ['int64', 'float64', 'bool']:
                continue

            # Try numeric conversion
            if self._try_numeric_conversion(df, column):
                type_changes[column] = f"{original_dtype} -> numeric"
                continue

            # Try datetime conversion
            if self._try_datetime_conversion(df, column):
                type_changes[column] = f"{original_dtype} -> datetime"
                continue

            # Try boolean conversion
            if self._try_boolean_conversion(df, column):
                type_changes[column] = f"{original_dtype} -> boolean"

        return df, type_changes

    def _try_numeric_conversion(self, df: pd.DataFrame, column: str) -> bool:
        """Try to convert column to numeric type."""
        try:
            numeric_series = pd.to_numeric(df[column], errors='coerce')
            # Convert if more than 50% of non-null values are numeric
            non_null_count = df[column].notna().sum()
            if non_null_count > 0 and (numeric_series.notna().sum() / non_null_count) > 0.5:
                df[column] = numeric_series
                return True
        except:
            pass
        return False

    def _try_datetime_conversion(self, df: pd.DataFrame, column: str) -> bool:
        """Try to convert column to datetime type."""
        if df[column].dtype != 'object':
            return False

        try:
            sample_values = df[column].dropna().head(10)
            if len(sample_values) == 0:
                return False

            # Try common date formats
            date_formats = [
                '%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y',
                '%Y-%m-%d %H:%M:%S', '%m/%d/%Y %H:%M:%S',
                '%d/%m/%Y %H:%M:%S', '%Y%m%d'
            ]

            for date_format in date_formats:
                try:
                    pd.to_datetime(sample_values.iloc[0], format=date_format)
                    datetime_series = pd.to_datetime(
                        df[column], format=date_format, errors='coerce')
                    non_null_count = df[column].notna().sum()
                    if non_null_count > 0 and (datetime_series.notna().sum() / non_null_count) > 0.5:
                        df[column] = datetime_series
                        return True
                except:
                    continue

            # Try general datetime parsing
            datetime_series = pd.to_datetime(df[column], errors='coerce')
            non_null_count = df[column].notna().sum()
            if non_null_count > 0 and (datetime_series.notna().sum() / non_null_count) > 0.5:
                df[column] = datetime_series
                return True

        except:
            pass
        return False

    def _try_boolean_conversion(self, df: pd.DataFrame, column: str) -> bool:
        """Try to convert column to boolean type."""
        try:
            unique_values = df[column].dropna().unique()
            if len(unique_values) <= 2:
                # Check if values look like booleans
                bool_like = {'true', 'false', 'yes', 'no', '1', '0', 'y', 'n'}
                if all(str(val).lower() in bool_like for val in unique_values):
                    # Create boolean mapping
                    true_values = {'true', 'yes', '1', 'y'}
                    df[column] = df[column].apply(
                        lambda x: str(x).lower(
                        ) in true_values if pd.notna(x) else x
                    )
                    return True
        except:
            pass
        return False

    def _remove_duplicates(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int]]:
        """Remove duplicate rows."""
        if df.empty:
            return df, {'duplicates_removed': 0}

        original_count = len(df)
        df = df.drop_duplicates()
        duplicates_removed = original_count - len(df)

        return df, {'duplicates_removed': duplicates_removed}

    def _handle_missing_values(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int]]:
        """Handle missing values intelligently."""
        if df.empty:
            return df, {'values_filled': 0}

        values_filled = 0

        for column in df.columns:
            missing_count = df[column].isna().sum()
            if missing_count == 0:
                continue

            if df[column].dtype in ['int64', 'float64']:
                # For numeric columns, fill with median
                median_value = df[column].median()
                if pd.notna(median_value):
                    df[column] = df[column].fillna(median_value)
                    values_filled += missing_count
            elif df[column].dtype == 'bool':
                # For boolean columns, fill with mode or False
                mode_value = df[column].mode()
                fill_value = mode_value.iloc[0] if len(
                    mode_value) > 0 else False
                df[column] = df[column].fillna(fill_value)
                values_filled += missing_count
            elif df[column].dtype == 'object':
                # For text columns, fill with mode or 'Unknown'
                mode_value = df[column].mode()
                fill_value = mode_value.iloc[0] if len(
                    mode_value) > 0 else 'Unknown'
                df[column] = df[column].fillna(fill_value)
                values_filled += missing_count
            else:
                # For datetime and other types, fill with mode or forward fill
                mode_value = df[column].mode()
                if len(mode_value) > 0:
                    df[column] = df[column].fillna(mode_value.iloc[0])
                else:
                    # Use forward fill as backup
                    df[column] = df[column].fillna(method='ffill')
                    # If still have NaN values (all were NaN), fill with a default
                    if df[column].isna().any():
                        if pd.api.types.is_datetime64_any_dtype(df[column]):
                            df[column] = df[column].fillna(
                                pd.Timestamp('1900-01-01'))
                        else:
                            df[column] = df[column].fillna('Unknown')
                values_filled += missing_count

        return df, {'values_filled': values_filled}

    def get_data_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate comprehensive data summary after cleaning.

        Args:
            df (pd.DataFrame): Cleaned DataFrame

        Returns:
            Dict[str, Any]: Summary statistics and information
        """
        if df.empty:
            return {
                'shape': (0, 0),
                'columns': [],
                'data_types': {},
                'missing_values': {},
                'summary': "Dataset is empty"
            }

        summary = {
            'shape': df.shape,
            'columns': df.columns.tolist(),
            'data_types': {col: str(dtype) for col, dtype in df.dtypes.items()},
            'missing_values': df.isnull().sum().to_dict(),
            'memory_usage_mb': df.memory_usage(deep=True).sum() / 1024 / 1024,
        }

        # Add type counts
        type_counts = df.dtypes.value_counts().to_dict()
        summary['type_distribution'] = {
            str(k): v for k, v in type_counts.items()}

        # Add basic statistics for numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            summary['numeric_summary'] = df[numeric_cols].describe().to_dict()

        # Add value counts for categorical columns (if not too many unique values)
        categorical_cols = df.select_dtypes(include=['object']).columns
        summary['categorical_info'] = {}
        for col in categorical_cols:
            if df[col].nunique() <= 10:  # Only for columns with few unique values
                summary['categorical_info'][col] = df[col].value_counts().head(
                    5).to_dict()

        return summary


def clean_uploaded_file(file_path: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Main function to clean an uploaded file.

    Args:
        file_path (str): Path to the uploaded file

    Returns:
        Tuple[pd.DataFrame, Dict[str, Any]]: Cleaned DataFrame and cleaning statistics
    """
    cleaner = DataCleaner()

    try:
        # Load the file
        df = cleaner.load_file(file_path)

        # Clean the data
        cleaned_df, cleaning_stats = cleaner.clean_dataframe(df)

        # Get summary
        data_summary = cleaner.get_data_summary(cleaned_df)

        # Combine stats
        final_stats = {
            **cleaning_stats,
            'data_summary': data_summary,
            'success': True,
            'message': f"Successfully cleaned data: {cleaning_stats['original_shape']} -> {cleaning_stats['final_shape']}"
        }

        return cleaned_df, final_stats

    except Exception as e:
        logger.error(f"Error in clean_uploaded_file: {str(e)}")
        return pd.DataFrame(), {
            'success': False,
            'error': str(e),
            'message': f"Failed to clean file: {str(e)}"
        }
