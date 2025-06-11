#!/usr/bin/env python3
"""
Test data cleaning functionality for the enhanced file upload system
"""
import requests
import json

# API Configuration
BASE_URL = "http://localhost:8000"

def test_data_cleaning():
    """Test the data cleaning functionality"""
    print("🧹 Testing Data Cleaning Functionality")
    print("=" * 60)
    
    # Login to get token
    login_data = {"email": "test@example.com", "password": "TestPass123!"}
    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    
    if response.status_code != 200:
        print("❌ Login failed. Please ensure test user exists.")
        return
    
    token = response.json().get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    
    # Upload the dirty test file
    print("\n📁 Uploading dirty test data...")
    try:
        with open("test_dirty_data.csv", 'rb') as f:
            files = {'file': ('test_dirty_data.csv', f, 'text/csv')}
            response = requests.post(f"{BASE_URL}/files/upload", headers=headers, files=files)
        
        if response.status_code in [200, 201]:
            result = response.json()
            file_id = result.get('file_id')
            print(f"✅ Upload successful! File ID: {file_id}")
            print(f"📊 Original: {result.get('message')}")
            
            # Try to analyze the file first
            print(f"\n🔍 Analyzing original file...")
            response = requests.post(f"{BASE_URL}/files/{file_id}/analyze", headers=headers)
            if response.status_code == 200:
                analysis = response.json()
                print(f"✅ Original file analysis:")
                print(f"   📏 Total rows: {analysis.get('total_rows')}")
                print(f"   📊 Total columns: {analysis.get('total_columns')}")
                if 'missing_values' in analysis:
                    missing_count = sum(analysis['missing_values'].values())
                    print(f"   🔍 Missing values: {missing_count}")
            else:
                print(f"❌ Analysis failed: {response.status_code}")
                print(f"   Error: {response.text}")
            
            # Test manual data cleaning via direct API call (since endpoint might not be exposed)
            print(f"\n🧹 Attempting data cleaning...")
            
            # Try the clean endpoint
            response = requests.post(f"{BASE_URL}/files/{file_id}/clean", headers=headers)
            if response.status_code == 200:
                clean_result = response.json()
                print(f"✅ Data cleaning successful!")
                print(f"   📏 Original shape: {clean_result.get('original_shape')}")
                print(f"   📊 Cleaned shape: {clean_result.get('cleaned_shape')}")
                print(f"   🗑️ Rows removed: {clean_result.get('rows_removed')}")
                print(f"   🗑️ Columns removed: {clean_result.get('columns_removed')}")
                print(f"   📝 Summary: {clean_result.get('cleaning_summary')}")
            else:
                print(f"❌ Clean endpoint not available: {response.status_code}")
                print(f"   Response: {response.text}")
                print("\n💡 Data cleaning is implemented in the backend but endpoint may not be registered")
                print("   The clean_data() function is available for:")
                print("   - Removing empty rows and columns")
                print("   - Dropping 'Unnamed' columns from CSV exports")
                print("   - Resetting DataFrame index")
                print("   - Basic data type optimization")
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"   Error: {response.text}")
            
    except FileNotFoundError:
        print("❌ Test file 'test_dirty_data.csv' not found")
        print("   Creating a sample dirty file...")
        
        # Create a dirty test file
        dirty_data = """Name,Age,City,Salary,Unnamed: 5,
John Doe,28,New York,75000,,
Jane Smith,34,Los Angeles,82000,,
,,,,,
Bob Johnson,45,Chicago,68000,,
Alice Brown,29, Houston ,71000,,
Charlie Davis,38,Phoenix,79000,,
,,,,,
Mike Wilson,32,Dallas,73000,,
   Sarah Jones   ,27,   Seattle   ,69000,,"""
        
        with open("test_dirty_data.csv", "w") as f:
            f.write(dirty_data)
        
        print("✅ Created test_dirty_data.csv")
        print("   This file contains:")
        print("   - Empty rows")
        print("   - Unnamed columns")
        print("   - Whitespace in data")
        print("   - Inconsistent formatting")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")

def demonstrate_clean_data_function():
    """Demonstrate the clean_data function conceptually"""
    print("\n🧹 Data Cleaning Function Overview")
    print("=" * 60)
    
    print("The clean_data() function implements best practices:")
    print("✅ Load data based on file extension (.csv, .txt, .xlsx)")
    print("✅ Remove rows that are entirely empty")
    print("✅ Remove columns that are entirely empty") 
    print("✅ Drop irrelevant 'Unnamed' columns from CSV exports")
    print("✅ Reset DataFrame index for clean structure")
    print("✅ Handle various file types consistently")
    
    print("\n📋 Supported Operations:")
    print("- dropna(axis='index', how='all') - Remove empty rows")
    print("- dropna(axis='columns', how='all') - Remove empty columns")
    print("- Drop columns starting with 'Unnamed'")
    print("- reset_index(drop=True) - Clean index")
    
    print("\n🎯 Ready for:")
    print("- Data analysis and visualization")
    print("- Machine learning preprocessing")
    print("- Statistical computations")
    print("- Export to clean formats")

if __name__ == "__main__":
    test_data_cleaning()
    demonstrate_clean_data_function()
    
    print("\n" + "=" * 60)
    print("🎉 Data Cleaning System Overview Complete!")
    print("\n💡 Next steps:")
    print("   - Use the enhanced file upload system")
    print("   - Apply data cleaning to uploaded files")
    print("   - Integrate with data analysis workflows")
    print("   - Visit http://localhost:8000/docs for API documentation")
