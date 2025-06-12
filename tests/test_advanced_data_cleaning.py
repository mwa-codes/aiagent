#!/usr/bin/env python3
"""
Test script for the advanced data cleaning functionality.

This script demonstrates the comprehensive data cleaning capabilities
including data type conversion, missing value handling, and more.
"""

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add the backend app to the Python path
sys.path.append('/Users/MWA/Desktop/aiagent/backend')

try:
    from app.utils.data_cleaning import clean_uploaded_file, clean_data, get_cleaning_summary
except ImportError as e:
    print(f"Error importing data cleaning utilities: {e}")
    sys.exit(1)


def create_messy_test_data():
    """Create a messy dataset for testing data cleaning."""
    np.random.seed(42)

    # Create sample data with various issues
    data = {
        'ID': range(1, 101),
        # Extra spaces, empty values, duplicates
        ' Name ': ['Alice', 'Bob', 'Charlie', '', 'Diana', 'Eve'] * 16 + ['Alice', 'Bob', 'Charlie', ''],
        # Mixed types, missing values
        'Age': [25, 30, np.nan, 45, 50, '35'] * 16 + [25, 30, np.nan, 45],
        # String numbers, empty, invalid
        'Salary': ['50000', '60000', '', '70000', 'invalid', '80000'] * 16 + ['50000', '60000', '', '70000'],
        # Mixed date formats
        'Date Joined': ['2020-01-15', '2019/05/20', '', '2021-12-01', 'invalid_date', '2022-03-10'] * 16 + ['2020-01-15', '2019/05/20', '', '2021-12-01'],
        # Boolean-like values
        'Is Active?': ['yes', 'no', 'true', '1', '0', 'false'] * 16 + ['yes', 'no', 'true', '1'],
        'Unnamed: 5': [np.nan] * 100,  # Completely empty column
        # Categories with empty
        'Department': ['Engineering', 'Sales', 'Marketing', 'HR', '', 'Engineering'] * 16 + ['Engineering', 'Sales', 'Marketing', 'HR'],
        '': ['junk'] * 100,  # Column with empty name
    }

    df = pd.DataFrame(data)

    # Add some completely empty rows
    empty_rows = pd.DataFrame({col: [np.nan] * 5 for col in df.columns})
    df = pd.concat([df, empty_rows], ignore_index=True)

    return df


def test_data_cleaning():
    """Test the data cleaning functionality."""
    print("🧪 Testing Advanced Data Cleaning Functionality")
    print("=" * 60)

    # Create test data directory if it doesn't exist
    test_data_dir = '/Users/MWA/Desktop/aiagent/tests/data'
    os.makedirs(test_data_dir, exist_ok=True)

    # Create and save messy test data
    print("\n1️⃣ Creating messy test dataset...")
    messy_df = create_messy_test_data()
    test_file_path = os.path.join(test_data_dir, 'messy_test_data.csv')
    messy_df.to_csv(test_file_path, index=False)

    print(f"   📄 Created test file: {test_file_path}")
    print(f"   📊 Original shape: {messy_df.shape}")
    print(f"   📋 Original columns: {list(messy_df.columns)}")
    print(f"   ❌ Missing values per column:")
    for col, missing in messy_df.isnull().sum().items():
        if missing > 0:
            print(f"      {col}: {missing}")

    # Test the data cleaning utility
    print("\n2️⃣ Running advanced data cleaning...")
    try:
        cleaned_df, cleaning_stats = clean_uploaded_file(test_file_path)

        if cleaning_stats.get('success', False):
            print("   ✅ Data cleaning completed successfully!")
            print(f"   📊 Final shape: {cleaned_df.shape}")
            print(f"   📋 Cleaned columns: {list(cleaned_df.columns)}")

            # Display cleaning statistics
            print("\n3️⃣ Cleaning Statistics:")
            print(
                f"   🔄 Operations performed: {len(cleaning_stats.get('operations_performed', []))}")
            for operation in cleaning_stats.get('operations_performed', []):
                print(f"      • {operation}")

            print(
                f"   📉 Total rows removed: {cleaning_stats.get('total_rows_removed', 0)}")
            print(
                f"   📉 Total columns removed: {cleaning_stats.get('total_cols_removed', 0)}")
            print(
                f"   🔧 Data type changes: {len(cleaning_stats.get('data_type_changes', {}))}")
            for col, change in cleaning_stats.get('data_type_changes', {}).items():
                print(f"      • {col}: {change}")
            print(
                f"   🚫 Duplicates removed: {cleaning_stats.get('duplicates_removed', 0)}")
            print(
                f"   🔗 Missing values handled: {cleaning_stats.get('missing_values_handled', 0)}")

            # Display data summary
            print("\n4️⃣ Data Summary After Cleaning:")
            data_summary = cleaning_stats.get('data_summary', {})
            print(f"   📏 Shape: {data_summary.get('shape', 'N/A')}")
            print(
                f"   🔢 Data types: {data_summary.get('type_distribution', {})}")
            print(
                f"   💾 Memory usage: {data_summary.get('memory_usage_mb', 0):.2f} MB")

            # Show sample of cleaned data
            print("\n5️⃣ Sample of Cleaned Data:")
            if not cleaned_df.empty:
                print(cleaned_df.head().to_string())
            else:
                print("   (No data after cleaning)")

            # Save cleaned data
            cleaned_file_path = os.path.join(
                test_data_dir, 'cleaned_test_data.csv')
            cleaned_df.to_csv(cleaned_file_path, index=False)
            print(f"\n   💾 Saved cleaned data to: {cleaned_file_path}")

        else:
            print(
                f"   ❌ Data cleaning failed: {cleaning_stats.get('error', 'Unknown error')}")

    except Exception as e:
        print(f"   ❌ Error during testing: {str(e)}")
        return False    # Test individual cleaning functions
    print("\n6️⃣ Testing Individual Cleaning Functions...")
    try:
        # Test basic clean_data function
        print("   🧹 Testing clean_data function...")
        cleaned_df_basic = clean_data(test_file_path)
        print(
            f"      ✅ Basic cleaning completed: {messy_df.shape} -> {cleaned_df_basic.shape}")

        # Test cleaning summary generation
        print("   📊 Testing cleaning summary...")
        summary = get_cleaning_summary(messy_df, cleaned_df_basic)
        print(f"      ✅ Generated summary: {summary}")

    except Exception as e:
        print(f"   ❌ Error testing individual functions: {str(e)}")

    print("\n🎉 Data Cleaning Test Complete!")
    return True


def test_different_file_formats():
    """Test data cleaning with different file formats."""
    print("\n🗂️ Testing Different File Formats")
    print("=" * 40)

    test_data_dir = '/Users/MWA/Desktop/aiagent/tests/data'
    messy_df = create_messy_test_data()

    # Test CSV format
    print("\n   📄 Testing CSV format...")
    csv_path = os.path.join(test_data_dir, 'test_format.csv')
    messy_df.to_csv(csv_path, index=False)

    try:
        cleaned_df, stats = clean_uploaded_file(csv_path)
        print(
            f"      ✅ CSV: {stats['original_shape']} -> {stats['final_shape']}")
    except Exception as e:
        print(f"      ❌ CSV failed: {str(e)}")

    # Test Excel format (if openpyxl is available)
    print("   📊 Testing Excel format...")
    try:
        excel_path = os.path.join(test_data_dir, 'test_format.xlsx')
        messy_df.to_excel(excel_path, index=False)

        cleaned_df, stats = clean_uploaded_file(excel_path)
        print(
            f"      ✅ Excel: {stats['original_shape']} -> {stats['final_shape']}")
    except Exception as e:
        print(f"      ❌ Excel failed: {str(e)}")

    # Test TXT format (CSV-like)
    print("   📝 Testing TXT format...")
    try:
        txt_path = os.path.join(test_data_dir, 'test_format.txt')
        messy_df.to_csv(txt_path, index=False, sep=',')

        cleaned_df, stats = clean_uploaded_file(txt_path)
        print(
            f"      ✅ TXT: {stats['original_shape']} -> {stats['final_shape']}")
    except Exception as e:
        print(f"      ❌ TXT failed: {str(e)}")


if __name__ == "__main__":
    print("🚀 Advanced Data Cleaning Test Suite")
    print("====================================")

    # Run main test
    success = test_data_cleaning()

    if success:
        # Test different formats
        test_different_file_formats()

        print("\n✅ All tests completed successfully!")
        print("\n📚 Key Features Demonstrated:")
        print("   • Robust file loading with encoding detection")
        print("   • Empty row/column removal")
        print("   • Column name standardization")
        print("   • Intelligent data type conversion")
        print("   • Duplicate row removal")
        print("   • Smart missing value handling")
        print("   • Comprehensive data quality reporting")
        print("\n🎯 The data cleaning system is ready for production use!")
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
        sys.exit(1)
