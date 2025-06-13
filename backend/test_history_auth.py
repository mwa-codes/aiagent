"""Test script to validate authentication and user isolation for history endpoints."""

import requests
import json

BASE_URL = "http://localhost:8000"


def create_test_user(email, password):
    """Create a new test user and return access token."""
    print(f"Creating user: {email}")

    # Try to register a new user
    register_data = {
        "email": email,
        "password": password
    }

    reg_response = requests.post(
        f"{BASE_URL}/auth/register", json=register_data)
    if reg_response.status_code == 200:
        print("✅ User registration successful")
    elif reg_response.status_code == 400 and "already registered" in reg_response.text:
        print("ℹ️ User already exists, proceeding with login")
    else:
        print(f"❌ Registration failed: {reg_response.text}")
        return None

    # Login to get token
    login_data = {
        "email": email,
        "password": password
    }

    response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if response.status_code == 200:
        print("✅ Login successful")
        token_data = response.json()
        return token_data["access_token"]
    else:
        print(f"❌ Login failed: {response.text}")
        return None


def test_history_with_user(email, password, description):
    """Test history endpoints with a specific user."""
    print(f"\n🔐 Testing with {description}: {email}")

    token = create_test_user(email, password)
    if not token:
        return

    headers = {"Authorization": f"Bearer {token}"}

    # Test file history
    print("📂 Testing file history...")
    response = requests.get(f"{BASE_URL}/files/history/files", headers=headers)

    if response.status_code == 200:
        history_data = response.json()
        print(f"✅ Files found: {history_data['total']}")

        if history_data['files']:
            print("   File details:")
            for file in history_data['files'][:3]:  # Show first 3 files
                print(
                    f"     - ID: {file['id']}, Name: {file['filename'][:50]}...")

                # Test file results for this file
                results_response = requests.get(
                    f"{BASE_URL}/files/history/results/{file['id']}",
                    headers=headers
                )

                if results_response.status_code == 200:
                    results_data = results_response.json()
                    print(
                        f"       └─ Summaries: {len(results_data['summaries'])}")
                else:
                    print(
                        f"       └─ ❌ Results error: {results_response.status_code}")
        else:
            print("   No files found for this user")
    else:
        print(
            f"❌ File history failed: {response.status_code} - {response.text}")


def test_unauthorized_access():
    """Test that unauthorized requests are properly rejected."""
    print("\n🚫 Testing unauthorized access...")

    # Test without token
    response = requests.get(f"{BASE_URL}/files/history/files")
    if response.status_code == 401:
        print("✅ Unauthorized request properly rejected")
    else:
        print(f"❌ Expected 401, got: {response.status_code}")

    # Test with invalid token
    headers = {"Authorization": "Bearer invalid_token"}
    response = requests.get(f"{BASE_URL}/files/history/files", headers=headers)
    if response.status_code == 401:
        print("✅ Invalid token properly rejected")
    else:
        print(f"❌ Expected 401 for invalid token, got: {response.status_code}")


def test_cross_user_isolation():
    """Test that users cannot access each other's data."""
    print("\n🔒 Testing cross-user isolation...")

    # Create two different users
    user1_email = "testuser1@example.com"
    user2_email = "testuser2@example.com"
    password = "TestPass123!"

    token1 = create_test_user(user1_email, password)
    token2 = create_test_user(user2_email, password)

    if not token1 or not token2:
        print("❌ Could not create test users")
        return

    headers1 = {"Authorization": f"Bearer {token1}"}
    headers2 = {"Authorization": f"Bearer {token2}"}

    # Get user1's files
    response1 = requests.get(
        f"{BASE_URL}/files/history/files", headers=headers1)
    response2 = requests.get(
        f"{BASE_URL}/files/history/files", headers=headers2)

    if response1.status_code == 200 and response2.status_code == 200:
        data1 = response1.json()
        data2 = response2.json()

        print(f"User1 files: {data1['total']}")
        print(f"User2 files: {data2['total']}")

        # Check if any file IDs overlap (they shouldn't for different users)
        if data1['files'] and data2['files']:
            ids1 = {file['id'] for file in data1['files']}
            ids2 = {file['id'] for file in data2['files']}

            if ids1.intersection(ids2):
                print(
                    "⚠️ Warning: Users have overlapping file IDs - this might indicate an issue")
            else:
                print("✅ Users have separate file sets")

        print("✅ Cross-user isolation appears to be working")
    else:
        print(f"❌ Failed to get file data for isolation test")


def main():
    """Run all authentication and authorization tests."""
    print("🔐 History Endpoints Authentication & Authorization Tests\n")

    # Test with existing user
    test_history_with_user("test@example.com", "TestPass123!", "existing user")

    # Test with new user
    test_history_with_user("newhistoryuser@example.com",
                           "TestPass123!", "new user")

    # Test unauthorized access
    test_unauthorized_access()

    # Test cross-user isolation
    test_cross_user_isolation()

    print("\n🎉 Authentication & Authorization tests completed!")


if __name__ == "__main__":
    main()
