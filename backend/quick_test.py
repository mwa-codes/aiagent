#!/usr/bin/env python3
"""Quick test script for the Account Management API"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"


def test_account_management():
    print("🧪 Quick Account Management Test")
    print("=" * 50)

    # Test 1: Register a user
    print("\n1️⃣ Testing User Registration...")
    register_data = {
        "email": "quicktest@example.com",
        "password": "TestPassword123!"
    }

    try:
        response = requests.post(
            f"{BASE_URL}/auth/register", json=register_data)
        print(f"   Status: {response.status_code}")
        print(f"   Response: {response.text[:100]}...")

        if response.status_code == 400 and "already registered" in response.text:
            print("   ✅ User already exists, proceeding with login...")
        elif response.status_code == 201:
            print("   ✅ User registered successfully!")
        else:
            print(f"   ❌ Unexpected response: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Registration failed: {e}")
        return False

    # Test 2: Login to get access token
    print("\n2️⃣ Testing User Login...")
    login_data = {
        "username": "quicktest@example.com",
        "password": "TestPassword123!"
    }

    try:
        response = requests.post(f"{BASE_URL}/auth/login", data=login_data)
        print(f"   Status: {response.status_code}")

        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get("access_token")
            print("   ✅ Login successful!")
            print(f"   Token preview: {access_token[:30]}...")
        else:
            print(f"   ❌ Login failed: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ Login failed: {e}")
        return False

    # Test 3: Test Account Management Endpoints
    headers = {"Authorization": f"Bearer {access_token}"}

    print("\n3️⃣ Testing Account Management Endpoints...")

    # Test GET /users/me
    try:
        response = requests.get(f"{BASE_URL}/users/me", headers=headers)
        print(f"   GET /users/me - Status: {response.status_code}")
        if response.status_code == 200:
            user_data = response.json()
            print(f"   ✅ User profile: {user_data.get('email')}")
        else:
            print(f"   ❌ Failed: {response.text}")
    except Exception as e:
        print(f"   ❌ GET /users/me failed: {e}")

    # Test GET /users/me/profile
    try:
        response = requests.get(
            f"{BASE_URL}/users/me/profile", headers=headers)
        print(f"   GET /users/me/profile - Status: {response.status_code}")
        if response.status_code == 200:
            profile_data = response.json()
            print(
                f"   ✅ Profile with plan: {profile_data.get('plan', {}).get('name', 'No plan')}")
        else:
            print(f"   ❌ Failed: {response.text}")
    except Exception as e:
        print(f"   ❌ GET /users/me/profile failed: {e}")

    # Test GET /users/me/usage
    try:
        response = requests.get(f"{BASE_URL}/users/me/usage", headers=headers)
        print(f"   GET /users/me/usage - Status: {response.status_code}")
        if response.status_code == 200:
            usage_data = response.json()
            print(
                f"   ✅ Usage stats: {usage_data.get('files_uploaded', 0)} files uploaded")
        else:
            print(f"   ❌ Failed: {response.text}")
    except Exception as e:
        print(f"   ❌ GET /users/me/usage failed: {e}")

    print("\n✅ Account Management API Test Complete!")
    return True


if __name__ == "__main__":
    success = test_account_management()
    sys.exit(0 if success else 1)
