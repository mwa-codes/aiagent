"""Test script for authentication endpoints."""

import requests
import json

BASE_URL = "http://localhost:8000"


def test_authentication():
    """Test the authentication flow."""

    print("🧪 Testing Authentication System\n")

    # Test 1: Register a new user
    print("1️⃣ Testing user registration...")
    register_data = {
        "email": "test@example.com",
        "password": "TestPass123!"
    }

    try:
        response = requests.post(
            f"{BASE_URL}/auth/register", json=register_data)
        if response.status_code == 200:
            print("✅ User registration successful")
            user_data = response.json()
            print(f"   User ID: {user_data['id']}")
            print(f"   Email: {user_data['email']}")
        else:
            print(f"❌ Registration failed: {response.text}")
            return
    except Exception as e:
        print(f"❌ Registration error: {e}")
        return

    # Test 2: Login with the user
    print("\n2️⃣ Testing user login...")
    login_data = {
        "email": "test@example.com",
        "password": "TestPass123!"
    }

    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        if response.status_code == 200:
            print("✅ User login successful")
            token_data = response.json()
            access_token = token_data["access_token"]
            print(f"   Token type: {token_data['token_type']}")
            print(f"   Access token: {access_token[:20]}...")
        else:
            print(f"❌ Login failed: {response.text}")
            return
    except Exception as e:
        print(f"❌ Login error: {e}")
        return

    # Test 3: Access protected endpoint
    print("\n3️⃣ Testing protected endpoint...")
    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
        if response.status_code == 200:
            print("✅ Protected endpoint access successful")
            user_data = response.json()
            print(f"   User: {user_data['email']}")
            print(f"   Plan ID: {user_data['plan_id']}")
        else:
            print(f"❌ Protected endpoint failed: {response.text}")
    except Exception as e:
        print(f"❌ Protected endpoint error: {e}")

    # Test 4: Test password validation
    print("\n4️⃣ Testing password validation...")
    weak_password_data = {
        "email": "weak@example.com",
        "password": "weak"
    }

    try:
        response = requests.post(
            f"{BASE_URL}/auth/register", json=weak_password_data)
        if response.status_code == 422:
            print("✅ Password validation working")
            print("   Weak password correctly rejected")
        else:
            print(f"❌ Password validation failed: {response.text}")
    except Exception as e:
        print(f"❌ Password validation error: {e}")

    print("\n🎉 Authentication testing complete!")


if __name__ == "__main__":
    test_authentication()
