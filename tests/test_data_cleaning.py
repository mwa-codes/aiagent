#!/usr/bin/env python3
"""
Test script for data cleaning functionality
"""
import pandas as pd
import os


def clean_data(file_path: str) -> pd.DataFrame:
    """
    Load file into pandas and perform comprehensive data cleaning.

    Data cleaning best practices include:
    - Handling nulls and outliers
    - Removing empty rows/columns
    - Dropping irrelevant columns
    - Type conversion and date parsing
    - Ensuring data is ready for analysis and summarization
    """
    try:
        # Load data based on file extension
        if file_path.endswith(".csv") or file_path.endswith(".txt"):
            df = pd.read_csv(file_path)
        elif file_path.endswith(".xlsx") or file_path.endswith(".xls"):
            df = pd.read_excel(file_path)
        else:
            raise ValueError("Unsupported file type")

        print(f"Original data shape: {df.shape}")
        print("Original data:")
        print(df)
        print("\n" + "="*50 + "\n")

        # Remove rows that are entirely empty
        df = df.dropna(axis='index', how='all')
        print(f"After removing empty rows: {df.shape}")

        # Remove columns that are entirely empty
        df = df.dropna(axis='columns', how='all')
        print(f"After removing empty columns: {df.shape}")

        # Drop irrelevant columns (like "Unnamed" columns from CSV exports)
        unnamed_cols = [col for col in df.columns if str(
            col).startswith("Unnamed")]
        df = df.drop(columns=unnamed_cols, errors='ignore')
        print(f"After removing 'Unnamed' columns: {df.shape}")

        # Strip whitespace from string columns
        string_columns = df.select_dtypes(include=['object']).columns
        for col in string_columns:
            df[col] = df[col].astype(str).str.strip()
            # Replace empty strings with NaN for consistency
            df[col] = df[col].replace('', pd.NA)

        # Attempt to convert numeric-looking columns to proper numeric types
        for col in df.columns:
            if df[col].dtype == 'object':
                # Try to convert to numeric if it looks numeric
                numeric_series = pd.to_numeric(df[col], errors='coerce')
                # If more than 80% of non-null values are numeric, convert the column
                non_null_count = df[col].notna().sum()
                numeric_count = numeric_series.notna().sum()
                if non_null_count > 0 and (numeric_count / non_null_count) > 0.8:
                    df[col] = numeric_series
                    print(f"Converted column '{col}' to numeric type")

        # Reset index after cleaning
        df = df.reset_index(drop=True)

        print("\nCleaned data:")
        print(df)
        print(f"\nFinal data shape: {df.shape}")
        print("\nData types:")
        print(df.dtypes)

        return df

    except Exception as e:
        raise ValueError(f"Error cleaning data: {str(e)}")


def main():
    print("Testing Data Cleaning Functionality")
    print("="*50)

    # Test with dirty data
    test_file = "test_dirty_data.csv"
    if os.path.exists(test_file):
        print(f"Testing with {test_file}")
        cleaned_df = clean_data(test_file)

        # Save cleaned data
        cleaned_file = "test_dirty_data_cleaned.csv"
        cleaned_df.to_csv(cleaned_file, index=False)
        print(f"\nCleaned data saved to: {cleaned_file}")
    else:
        print(f"Test file {test_file} not found!")


if __name__ == "__main__":
    main()
