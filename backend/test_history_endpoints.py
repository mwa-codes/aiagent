"""Test script for history endpoints."""

import requests
import json

BASE_URL = "http://localhost:8000"


def test_history_endpoints():
    """Test the history endpoints functionality."""

    print("🧪 Testing History Endpoints\n")

    # First, let's login to get a token
    print("1️⃣ Logging in to get access token...")
    login_data = {
        "email": "test@example.com",
        "password": "TestPass123!"
    }

    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        if response.status_code == 200:
            print("✅ Login successful")
            token_data = response.json()
            access_token = token_data["access_token"]
            headers = {"Authorization": f"Bearer {access_token}"}
        else:
            print(f"❌ Login failed: {response.text}")
            print("Creating a new user first...")

            # Try to register a new user
            register_data = {
                "email": "testhistory@example.com",
                "password": "TestPass123!"
            }

            reg_response = requests.post(
                f"{BASE_URL}/auth/register", json=register_data)
            if reg_response.status_code == 200:
                print("✅ New user registered")
                # Login with new user
                login_data["email"] = "testhistory@example.com"
                response = requests.post(
                    f"{BASE_URL}/auth/login", json=login_data)
                if response.status_code == 200:
                    token_data = response.json()
                    access_token = token_data["access_token"]
                    headers = {"Authorization": f"Bearer {access_token}"}
                else:
                    print(f"❌ Login with new user failed: {response.text}")
                    return
            else:
                print(f"❌ Registration failed: {reg_response.text}")
                return
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return

    # Test 2: Get user file history
    print("\n2️⃣ Testing GET /files/history/files...")
    try:
        response = requests.get(
            f"{BASE_URL}/files/history/files", headers=headers)
        if response.status_code == 200:
            print("✅ File history endpoint successful")
            history_data = response.json()
            print(f"   Total files: {history_data['total']}")
            if history_data['files']:
                print("   Files found:")
                for file in history_data['files']:
                    print(
                        f"     - ID: {file['id']}, Name: {file['filename']}, Has Summary: {file['has_summary']}")
            else:
                print("   No files found for this user")
        else:
            print(f"❌ File history failed: {response.text}")
    except Exception as e:
        print(f"❌ File history error: {e}")

    # Test 3: Get file results for a specific file (if any exist)
    print("\n3️⃣ Testing GET /files/history/results/{file_id}...")
    try:
        # First get the file list to find a file ID
        response = requests.get(
            f"{BASE_URL}/files/history/files", headers=headers)
        if response.status_code == 200:
            history_data = response.json()
            if history_data['files'] and len(history_data['files']) > 0:
                file_id = history_data['files'][0]['id']
                print(f"   Testing with file ID: {file_id}")

                results_response = requests.get(
                    f"{BASE_URL}/files/history/results/{file_id}",
                    headers=headers
                )
                if results_response.status_code == 200:
                    print("✅ File results endpoint successful")
                    results_data = results_response.json()
                    print(f"   File: {results_data['filename']}")
                    print(
                        f"   Summaries count: {len(results_data['summaries'])}")
                    if results_data['summaries']:
                        print("   Summaries found:")
                        for summary in results_data['summaries']:
                            print(
                                f"     - ID: {summary['id']}, Created: {summary['created_at']}")
                            print(
                                f"       Text: {summary['result_text'][:100]}...")
                    else:
                        print("   No summaries found for this file")
                else:
                    print(f"❌ File results failed: {results_response.text}")
            else:
                print("   No files available to test results endpoint")
    except Exception as e:
        print(f"❌ File results error: {e}")

    print("\n🎉 History endpoints testing completed!")


if __name__ == "__main__":
    test_history_endpoints()
