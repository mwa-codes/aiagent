"""Test script for account management endpoints."""

import requests
import json
import time

BASE_URL = "http://localhost:8000"


def test_account_management():
    """Test the complete account management flow."""

    print("🧪 Testing Account Management System\n")

    # Test 1: Register a test user
    print("1️⃣ Setting up test user...")
    register_data = {
        "email": "testuser@example.com",
        "password": "TestPass123!"
    }

    try:
        response = requests.post(
            f"{BASE_URL}/auth/register", json=register_data)
        if response.status_code == 200:
            print("✅ Test user registered successfully")
        elif response.status_code == 400 and "already registered" in response.text:
            print("✅ Test user already exists")
        else:
            print(f"❌ Registration failed: {response.text}")
            return
    except Exception as e:
        print(f"❌ Registration error: {e}")
        return

    # Test 2: Login to get token
    print("\n2️⃣ Logging in...")
    login_data = {
        "email": "testuser@example.com",
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
            return
    except Exception as e:
        print(f"❌ Login error: {e}")
        return

    # Test 3: Get current user profile
    print("\n3️⃣ Testing GET /users/me...")
    try:
        response = requests.get(f"{BASE_URL}/users/me", headers=headers)
        if response.status_code == 200:
            print("✅ Current user profile retrieved")
            user_data = response.json()
            print(f"   User ID: {user_data['id']}")
            print(f"   Email: {user_data['email']}")
            print(f"   Plan ID: {user_data.get('plan_id', 'None')}")
        else:
            print(f"❌ Get profile failed: {response.text}")
    except Exception as e:
        print(f"❌ Get profile error: {e}")

    # Test 4: Get detailed profile
    print("\n4️⃣ Testing GET /users/me/profile...")
    try:
        response = requests.get(
            f"{BASE_URL}/users/me/profile", headers=headers)
        if response.status_code == 200:
            print("✅ Detailed profile retrieved")
            profile_data = response.json()
            print(f"   Plan: {profile_data.get('plan_name', 'Unknown')}")
            print(f"   Max files: {profile_data.get('max_files', 'Unknown')}")
            print(
                f"   Current files: {profile_data.get('current_files_count', 'Unknown')}")
        else:
            print(f"❌ Get detailed profile failed: {response.text}")
    except Exception as e:
        print(f"❌ Get detailed profile error: {e}")

    # Test 5: Get usage stats
    print("\n5️⃣ Testing GET /users/me/usage...")
    try:
        response = requests.get(f"{BASE_URL}/users/me/usage", headers=headers)
        if response.status_code == 200:
            print("✅ Usage stats retrieved")
            usage_data = response.json()
            print(f"   Current files: {usage_data.get('current_files', 0)}")
            print(f"   Max files: {usage_data.get('max_files', 0)}")
            print(f"   Usage: {usage_data.get('usage_percentage', 0)}%")
            print(f"   Can upload: {usage_data.get('can_upload', False)}")
        else:
            print(f"❌ Get usage stats failed: {response.text}")
    except Exception as e:
        print(f"❌ Get usage stats error: {e}")

    # Test 6: Update user profile (email only)
    print("\n6️⃣ Testing PUT /users/me (email update)...")
    new_email = f"updated_{int(time.time())}@example.com"
    update_data = {
        "email": new_email
    }

    try:
        response = requests.put(
            f"{BASE_URL}/users/me", json=update_data, headers=headers)
        if response.status_code == 200:
            print("✅ Email updated successfully")
            updated_user = response.json()
            print(f"   New email: {updated_user['email']}")
        else:
            print(f"❌ Email update failed: {response.text}")
    except Exception as e:
        print(f"❌ Email update error: {e}")

    # Test 7: Change password
    print("\n7️⃣ Testing PUT /users/me/password...")
    password_data = {
        "current_password": "TestPass123!",
        "new_password": "NewTestPass123!"
    }

    try:
        response = requests.put(
            f"{BASE_URL}/users/me/password", json=password_data, headers=headers)
        if response.status_code == 200:
            print("✅ Password changed successfully")
            print(f"   Message: {response.json().get('message', '')}")
        else:
            print(f"❌ Password change failed: {response.text}")
    except Exception as e:
        print(f"❌ Password change error: {e}")

    # Test 8: Try login with new password
    print("\n8️⃣ Testing login with new password...")
    new_login_data = {
        "email": new_email,
        "password": "NewTestPass123!"
    }

    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=new_login_data)
        if response.status_code == 200:
            print("✅ Login with new password successful")
            # Update headers with new token
            token_data = response.json()
            access_token = token_data["access_token"]
            headers = {"Authorization": f"Bearer {access_token}"}
        else:
            print(f"❌ Login with new password failed: {response.text}")
    except Exception as e:
        print(f"❌ Login with new password error: {e}")

    # Test 9: Test email change endpoint
    print("\n9️⃣ Testing PUT /users/me/email...")
    email_change_data = {
        "new_email": f"emailchange_{int(time.time())}@example.com",
        "password": "NewTestPass123!"
    }

    try:
        response = requests.put(
            f"{BASE_URL}/users/me/email", json=email_change_data, headers=headers)
        if response.status_code == 200:
            print("✅ Email change successful")
            result = response.json()
            print(f"   Old email: {result.get('old_email', '')}")
            print(f"   New email: {result.get('new_email', '')}")
        else:
            print(f"❌ Email change failed: {response.text}")
    except Exception as e:
        print(f"❌ Email change error: {e}")

    # Test 10: Test validation errors
    print("\n🔟 Testing validation errors...")

    # Test weak password
    weak_password_data = {
        "current_password": "NewTestPass123!",
        "new_password": "weak"
    }

    try:
        response = requests.put(
            f"{BASE_URL}/users/me/password", json=weak_password_data, headers=headers)
        if response.status_code == 422:
            print("✅ Weak password validation working")
            print("   Weak password correctly rejected")
        else:
            print(f"❌ Weak password validation failed: {response.text}")
    except Exception as e:
        print(f"❌ Weak password validation error: {e}")

    # Test duplicate email
    duplicate_email_data = {
        "email": "admin@example.com"  # This should exist from default setup
    }

    try:
        response = requests.put(
            f"{BASE_URL}/users/me", json=duplicate_email_data, headers=headers)
        if response.status_code == 400 and "already registered" in response.text:
            print("✅ Duplicate email validation working")
            print("   Duplicate email correctly rejected")
        else:
            print(f"❌ Duplicate email validation failed: {response.text}")
    except Exception as e:
        print(f"❌ Duplicate email validation error: {e}")

    # Test 11: Get account activity
    print("\n1️⃣1️⃣ Testing GET /users/me/activity...")
    try:
        response = requests.get(
            f"{BASE_URL}/users/me/activity", headers=headers)
        if response.status_code == 200:
            print("✅ Account activity retrieved")
            activity_data = response.json()
            print(f"   User ID: {activity_data.get('user_id', 'Unknown')}")
            print(f"   Current email: {activity_data.get('email', 'Unknown')}")
            print(f"   Plan: {activity_data.get('plan', 'Unknown')}")
            print(
                f"   Recent files: {len(activity_data.get('recent_files', []))}")
        else:
            print(f"❌ Get account activity failed: {response.text}")
    except Exception as e:
        print(f"❌ Get account activity error: {e}")

    print("\n🎉 Account management testing complete!")


def test_edge_cases():
    """Test edge cases and error conditions."""
    print("\n🔍 Testing Edge Cases...\n")

    # Test unauthorized access
    print("1️⃣ Testing unauthorized access...")
    try:
        response = requests.get(f"{BASE_URL}/users/me")
        if response.status_code == 401:
            print("✅ Unauthorized access properly blocked")
        else:
            print(f"❌ Unauthorized access not blocked: {response.status_code}")
    except Exception as e:
        print(f"❌ Unauthorized access test error: {e}")

    # Test invalid token
    print("\n2️⃣ Testing invalid token...")
    invalid_headers = {"Authorization": "Bearer invalid_token"}
    try:
        response = requests.get(
            f"{BASE_URL}/users/me", headers=invalid_headers)
        if response.status_code == 401:
            print("✅ Invalid token properly rejected")
        else:
            print(f"❌ Invalid token not rejected: {response.status_code}")
    except Exception as e:
        print(f"❌ Invalid token test error: {e}")


if __name__ == "__main__":
    test_account_management()
    test_edge_cases()
