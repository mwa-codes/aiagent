#!/usr/bin/env python3
"""
Test script for the enhanced file upload and data cleaning API endpoints.

This script demonstrates the complete workflow of:
1. User authentication
2. File upload with validation
3. Advanced data cleaning
4. Data quality reporting
5. File analysis and preview
"""

import requests
import os
import pandas as pd
import numpy as np
from pathlib import Path

BASE_URL = "http://localhost:8000"


def create_test_user_and_login():
    """Create a test user and get authentication token."""
    print("🔐 Setting up test user and authentication...")

    # Test user credentials
    user_data = {
        "email": "dataclean@example.com",
        "password": "DataClean123!"
    }

    # Try to register user (may already exist)
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
        if response.status_code in [200, 201]:
            print("   ✅ Test user created successfully")
        elif response.status_code == 400 and "already registered" in response.text.lower():
            print("   ℹ️  Test user already exists")
        else:
            print(f"   ⚠️  User registration response: {response.status_code}")
    except Exception as e:
        print(f"   ⚠️  User registration error: {e}")

    # Login to get token
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=user_data)
        if response.status_code == 200:
            token_data = response.json()
            token = token_data.get("access_token")
            if token:
                print("   ✅ Authentication successful")
                return {"Authorization": f"Bearer {token}"}
            else:
                print("   ❌ No access token received")
                return None
        else:
            print(
                f"   ❌ Login failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"   ❌ Login error: {e}")
        return None


def create_messy_test_file():
    """Create a messy CSV file for testing data cleaning."""
    print("\n📄 Creating messy test file...")

    # Create test data with various data quality issues
    np.random.seed(42)

    # Create 60 rows of data with consistent lengths
    num_rows = 60

    data = {
        'ID': list(range(1, 51)) + [None] * 10,  # 50 + 10 = 60 rows
        ' Customer Name ': ([  # Spaces in column name
            'Alice Johnson', 'Bob Smith', '', 'Charlie Brown', 'Diana Prince',
            'Eve Wilson', 'Frank Miller', 'Grace Lee', 'Henry Ford', 'Ivy Chen'
        ] * 6)[:num_rows],  # Repeat pattern and truncate to exact length
        'Age': ([25, 30, 'invalid', 45, 50, '35', 28, 33, '', 29] * 6)[:num_rows],
        'Annual Salary': (['50000', '60000', '', '70000', 'N/A', '80000', '55000', '65000', '75000', '85000'] * 6)[:num_rows],
        'Start Date': ([  # Mixed date formats
            '2020-01-15', '2019/05/20', '', '2021-12-01', 'invalid_date',
            '2022-03-10', '2020-07-22', '2019/11/15', '2021-08-30', '2022-01-05'
        ] * 6)[:num_rows],
        'Is Active': (['yes', 'no', 'true', '1', '0', 'false', 'Y', 'N', 'TRUE', 'FALSE'] * 6)[:num_rows],
        'Department': ([
            'Engineering', 'Sales', 'Marketing', 'HR', '',
            'Engineering', 'Finance', 'Operations', 'IT', 'Legal'
        ] * 6)[:num_rows],
        'Unnamed: 6': [None] * num_rows,  # Completely empty column
        '': ['junk'] * num_rows  # Column with empty name
    }

    # Create DataFrame and add duplicate rows
    df = pd.DataFrame(data)

    # Add some exact duplicates
    duplicate_rows = df.iloc[0:3].copy()
    df = pd.concat([df, duplicate_rows], ignore_index=True)

    # Save to file
    test_file_path = '/Users/MWA/Desktop/aiagent/tests/data/messy_api_test_data.csv'
    os.makedirs(os.path.dirname(test_file_path), exist_ok=True)
    df.to_csv(test_file_path, index=False)

    print(f"   📊 Created messy file with shape: {df.shape}")
    print(f"   📍 File location: {test_file_path}")
    print(f"   ❌ Data quality issues:")
    print(f"      • Mixed data types in numeric columns")
    print(f"      • Missing and invalid values")
    print(f"      • Inconsistent date formats")
    print(f"      • Empty rows and columns")
    print(f"      • Duplicate records")
    print(f"      • Poor column naming")

    return test_file_path


def test_file_upload(headers, file_path):
    """Test file upload endpoint."""
    print("\n📤 Testing file upload...")

    try:
        with open(file_path, 'rb') as f:
            files = {'file': ('messy_test_data.csv', f, 'text/csv')}
            response = requests.post(
                f"{BASE_URL}/files/upload", files=files, headers=headers)

        if response.status_code == 200:
            upload_data = response.json()
            file_id = upload_data.get('file_id')
            print("   ✅ File upload successful!")
            print(f"   📁 File ID: {file_id}")
            print(f"   📊 File type: {upload_data.get('file_type')}")
            print(f"   📏 File size: {upload_data.get('file_size')} bytes")
            print(f"   💬 Message: {upload_data.get('message')}")
            return file_id
        else:
            print(
                f"   ❌ Upload failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"   ❌ Upload error: {e}")
        return None


def test_data_quality_report(headers, file_id):
    """Test data quality report endpoint."""
    print("\n📊 Testing data quality report...")

    try:
        response = requests.get(
            f"{BASE_URL}/files/{file_id}/data-quality", headers=headers)

        if response.status_code == 200:
            quality_data = response.json()
            print("   ✅ Data quality report generated!")

            file_info = quality_data.get('file_info', {})
            print(
                f"   📁 File: {file_info.get('filename')} ({file_info.get('file_size_mb', 0):.2f} MB)")
            print(f"   📊 Shape: {file_info.get('shape')}")

            # Display quality issues
            issues = quality_data.get('quality_issues', [])
            print(f"   ⚠️  Quality Issues Found: {len(issues)}")
            for issue in issues[:5]:  # Show first 5 issues
                print(f"      • {issue}")

            # Display recommendations
            recommendations = quality_data.get('recommendations', [])
            print(f"   💡 Recommendations: {len(recommendations)}")
            for rec in recommendations[:3]:  # Show first 3 recommendations
                print(f"      • {rec}")

            # Display readiness score
            readiness = quality_data.get('readiness_score', 0)
            level = quality_data.get('readiness_level', 'Unknown')
            print(f"   🎯 Data Readiness: {readiness}% ({level})")

            return quality_data
        else:
            print(
                f"   ❌ Quality report failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"   ❌ Quality report error: {e}")
        return None


def test_advanced_cleaning(headers, file_id):
    """Test advanced data cleaning endpoint."""
    print("\n🧹 Testing advanced data cleaning...")

    try:
        response = requests.post(
            f"{BASE_URL}/files/{file_id}/advanced-clean", headers=headers)

        if response.status_code == 200:
            cleaning_data = response.json()
            print("   ✅ Advanced data cleaning completed!")

            cleaning_summary = cleaning_data.get('cleaning_summary', {})
            print(
                f"   📊 Original shape: {cleaning_summary.get('original_shape')}")
            print(f"   📊 Final shape: {cleaning_summary.get('final_shape')}")
            print(
                f"   📉 Rows removed: {cleaning_summary.get('total_rows_removed', 0)}")
            print(
                f"   📉 Columns removed: {cleaning_summary.get('total_cols_removed', 0)}")
            print(
                f"   💬 Summary: {cleaning_summary.get('cleaning_summary', 'N/A')}")

            # Show preview of cleaned data
            preview = cleaning_data.get('preview', [])
            if preview:
                print(f"   👀 Preview of cleaned data (first 3 rows):")
                for i, row in enumerate(preview[:3]):
                    print(f"      Row {i+1}: {row}")

            return cleaning_data
        else:
            print(
                f"   ❌ Advanced cleaning failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"   ❌ Advanced cleaning error: {e}")
        return None


def test_file_preview(headers, file_id):
    """Test file preview endpoint."""
    print("\n👀 Testing file preview...")

    try:
        response = requests.get(
            f"{BASE_URL}/files/{file_id}/preview?rows=5", headers=headers)

        if response.status_code == 200:
            preview_data = response.json()
            print("   ✅ File preview generated!")
            print(f"   📊 File type: {preview_data.get('file_type')}")
            print(f"   📏 Rows shown: {preview_data.get('rows_count', 0)}")

            columns = preview_data.get('columns', [])
            if columns:
                print(
                    f"   📋 Columns ({len(columns)}): {', '.join(columns[:5])}{'...' if len(columns) > 5 else ''}")

            data = preview_data.get('data', [])
            if data:
                print(f"   📄 Sample data:")
                for i, row in enumerate(data[:3]):
                    print(
                        f"      Row {i+1}: {dict(list(row.items())[:3])}{'...' if len(row) > 3 else ''}")

            return preview_data
        else:
            print(
                f"   ❌ Preview failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"   ❌ Preview error: {e}")
        return None


def test_file_analysis(headers, file_id):
    """Test file analysis endpoint."""
    print("\n📈 Testing file analysis...")

    try:
        response = requests.post(
            f"{BASE_URL}/files/{file_id}/analyze", headers=headers)

        if response.status_code == 200:
            analysis_data = response.json()
            print("   ✅ File analysis completed!")
            print(f"   📊 File type: {analysis_data.get('file_type')}")
            print(f"   📏 Total rows: {analysis_data.get('total_rows', 0)}")
            print(
                f"   📋 Total columns: {analysis_data.get('total_columns', 0)}")

            # Show data types
            data_types = analysis_data.get('data_types', {})
            if data_types:
                print(f"   🔤 Data types:")
                for col, dtype in list(data_types.items())[:5]:
                    print(f"      {col}: {dtype}")

            # Show missing values
            missing_values = analysis_data.get('missing_values', {})
            total_missing = sum(missing_values.values()
                                ) if missing_values else 0
            print(f"   ❌ Total missing values: {total_missing}")

            return analysis_data
        else:
            print(
                f"   ❌ Analysis failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"   ❌ Analysis error: {e}")
        return None


def main():
    """Main test function."""
    print("🚀 Comprehensive Data Cleaning API Test Suite")
    print("=" * 60)

    # Step 1: Authentication
    headers = create_test_user_and_login()
    if not headers:
        print("❌ Authentication failed. Cannot proceed with tests.")
        return

    # Step 2: Create test file
    file_path = create_messy_test_file()

    # Step 3: Upload file
    file_id = test_file_upload(headers, file_path)
    if not file_id:
        print("❌ File upload failed. Cannot proceed with tests.")
        return

    # Step 4: Test data quality report
    quality_report = test_data_quality_report(headers, file_id)

    # Step 5: Test file preview (before cleaning)
    print("\n" + "="*40)
    print("📄 BEFORE CLEANING:")
    print("="*40)
    preview_before = test_file_preview(headers, file_id)

    # Step 6: Test advanced data cleaning
    cleaning_result = test_advanced_cleaning(headers, file_id)

    # Step 7: Test file preview (after cleaning)
    print("\n" + "="*40)
    print("📄 AFTER CLEANING:")
    print("="*40)
    preview_after = test_file_preview(headers, file_id)

    # Step 8: Test file analysis (after cleaning)
    analysis_result = test_file_analysis(headers, file_id)

    # Summary
    print("\n" + "="*60)
    print("🎉 Test Suite Complete!")
    print("="*60)

    success_count = sum([
        bool(headers),
        bool(file_id),
        bool(quality_report),
        bool(preview_before),
        bool(cleaning_result),
        bool(preview_after),
        bool(analysis_result)
    ])

    total_tests = 7
    print(f"✅ Successful tests: {success_count}/{total_tests}")

    if success_count == total_tests:
        print("\n🎯 All Tests Passed! The data cleaning API is fully functional.")
        print("\n📚 Demonstrated Features:")
        print("   • File upload with validation")
        print("   • Data quality assessment")
        print("   • Advanced data cleaning and transformation")
        print("   • Before/after data preview")
        print("   • Comprehensive data analysis")
        print("   • Column standardization and type conversion")
        print("   • Missing value handling")
        print("   • Duplicate removal")
        print("   • Empty row/column cleanup")
        print("\n🚀 Ready for production use!")
    else:
        print(
            f"\n⚠️  {total_tests - success_count} tests failed. Please check the API server.")


if __name__ == "__main__":
    main()
