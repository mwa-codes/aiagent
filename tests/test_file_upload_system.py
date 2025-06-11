#!/usr/bin/env python3
"""
Comprehensive test of the enhanced file upload system
"""
import requests
import json
import os

# API Configuration
BASE_URL = "http://localhost:8000"
API_HEADERS = {"Content-Type": "application/json"}


def test_api_health():
    """Test if the API is accessible"""
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ API is healthy and accessible")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        return False


def test_file_endpoints():
    """Test available file endpoints"""
    try:
        response = requests.get(f"{BASE_URL}/openapi.json")
        if response.status_code == 200:
            openapi_spec = response.json()
            file_endpoints = [
                path for path in openapi_spec['paths'].keys() if 'files' in path]
            print("✅ Available file endpoints:")
            for endpoint in sorted(file_endpoints):
                methods = list(openapi_spec['paths'][endpoint].keys())
                print(f"   {', '.join(m.upper() for m in methods)} {endpoint}")
            return file_endpoints
        else:
            print(f"❌ Cannot get API spec: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Error getting API endpoints: {e}")
        return []


def create_test_user():
    """Create a test user for file upload testing"""
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPass123!"
    }

    try:
        # Try to register
        response = requests.post(f"{BASE_URL}/auth/register", json=user_data)
        if response.status_code in [200, 201]:
            print("✅ Test user created successfully")
        elif response.status_code == 400 and "already registered" in response.text.lower():
            print("ℹ️  Test user already exists")
        else:
            print(
                f"❌ User creation failed: {response.status_code} - {response.text}")
            return None

        # Login to get token
        login_data = {
            "email": user_data["email"], "password": user_data["password"]}
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        if response.status_code == 200:
            token_data = response.json()
            token = token_data.get("access_token")
            print("✅ Successfully logged in")
            return token
        else:
            print(f"❌ Login failed: {response.status_code} - {response.text}")
            return None

    except Exception as e:
        print(f"❌ Error with user creation/login: {e}")
        return None


def test_file_upload(token):
    """Test file upload functionality"""
    if not token:
        print("❌ Cannot test file upload without token")
        return

    # Test files
    test_files = [
        "test_data.csv",
        "test_data.txt",
        "test_dirty_data.csv"
    ]

    headers = {"Authorization": f"Bearer {token}"}

    for test_file in test_files:
        if os.path.exists(test_file):
            print(f"\n📁 Testing upload of {test_file}")
            try:
                with open(test_file, 'rb') as f:
                    files = {'file': (
                        test_file, f, 'text/csv' if test_file.endswith('.csv') else 'text/plain')}
                    response = requests.post(
                        f"{BASE_URL}/files/upload", headers=headers, files=files)

                if response.status_code in [200, 201]:
                    result = response.json()
                    print(f"   ✅ Upload successful!")
                    print(f"   📊 File ID: {result.get('file_id')}")
                    print(f"   📏 File size: {result.get('file_size')} bytes")
                    print(f"   📝 Summary: {result.get('message')}")

                    # Test preview if this was a successful upload
                    if result.get('file_id'):
                        test_file_preview(token, result['file_id'], test_file)
                        test_file_analysis(token, result['file_id'], test_file)

                else:
                    print(f"   ❌ Upload failed: {response.status_code}")
                    print(f"   Error: {response.text}")

            except Exception as e:
                print(f"   ❌ Upload error: {e}")
        else:
            print(f"❌ Test file {test_file} not found")


def test_file_preview(token, file_id, filename):
    """Test file preview functionality"""
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.get(
            f"{BASE_URL}/files/{file_id}/preview?rows=3", headers=headers)
        if response.status_code == 200:
            preview = response.json()
            print(f"   📖 Preview successful for {filename}")
            print(f"      Rows in preview: {preview.get('rows_count', 'N/A')}")
            if 'columns' in preview:
                print(
                    f"      Columns: {', '.join(preview['columns'][:3])}{'...' if len(preview['columns']) > 3 else ''}")
        else:
            print(f"   ❌ Preview failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Preview error: {e}")


def test_file_analysis(token, file_id, filename):
    """Test file analysis functionality"""
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.post(
            f"{BASE_URL}/files/{file_id}/analyze", headers=headers)
        if response.status_code == 200:
            analysis = response.json()
            print(f"   📊 Analysis successful for {filename}")
            print(f"      File type: {analysis.get('file_type')}")
            if 'total_rows' in analysis:
                print(f"      Total rows: {analysis.get('total_rows')}")
            if 'total_columns' in analysis:
                print(f"      Total columns: {analysis.get('total_columns')}")
        else:
            print(f"   ❌ Analysis failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Analysis error: {e}")


def main():
    print("🚀 Testing Enhanced File Upload System")
    print("=" * 60)

    # Test API health
    if not test_api_health():
        return

    print("\n" + "=" * 60)

    # Test available endpoints
    endpoints = test_file_endpoints()

    print("\n" + "=" * 60)

    # Create test user and get token
    token = create_test_user()

    print("\n" + "=" * 60)

    # Test file uploads
    test_file_upload(token)

    print("\n" + "=" * 60)
    print("🎉 File upload system testing completed!")
    print("\n💡 Next steps:")
    print("   - Visit http://localhost:8000/docs to explore the API")
    print("   - Visit http://localhost:3000 for the frontend")
    print("   - Use the file upload, preview, and analysis endpoints")


if __name__ == "__main__":
    main()
