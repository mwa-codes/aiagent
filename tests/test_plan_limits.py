#!/usr/bin/env python3
"""
Test script for plan limits enforcement in the API endpoints.
Tests upload and summarize endpoints with different user scenarios.
"""

import requests
import json
import io
import os
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000"
TEST_USER_EMAIL = "testuser@example.com"
TEST_USER_PASSWORD = "TestPassword123!"


class PlanLimitsTestSuite:
    def __init__(self):
        self.access_token = None
        self.user_id = None

    def authenticate(self):
        """Authenticate and get access token"""
        try:
            response = requests.post(
                f"{BASE_URL}/auth/login",
                json={
                    "email": TEST_USER_EMAIL,
                    "password": TEST_USER_PASSWORD
                }
            )
            if response.status_code == 200:
                data = response.json()
                self.access_token = data["access_token"]
                print(f"✅ Authentication successful")
                return True
            else:
                print(f"❌ Authentication failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False

    def get_headers(self):
        """Get headers with authentication"""
        return {"Authorization": f"Bearer {self.access_token}"}

    def get_user_info(self):
        """Get current user information"""
        try:
            response = requests.get(
                f"{BASE_URL}/users/me/profile",
                headers=self.get_headers()
            )
            if response.status_code == 200:
                user_data = response.json()
                self.user_id = user_data["id"]
                print(
                    f"✅ User info retrieved: {user_data['email']}, plan: {user_data.get('plan_name', 'Unknown')}")
                return user_data
            else:
                print(f"❌ Failed to get user info: {response.status_code}")
                print(f"Response: {response.text}")
                return None
        except Exception as e:
            print(f"❌ Error getting user info: {e}")
            return None

    def create_test_file(self, size_mb=1, content_type="text"):
        """Create a test file of specified size"""
        if content_type == "text":
            # Create a text file
            content = "This is a test file for plan limits testing.\n" * \
                (size_mb * 1024 * 50)  # Approximate size
            return io.BytesIO(content.encode()), "test_file.txt", "text/plain"
        elif content_type == "large":
            # Create a larger file
            content = "A" * (size_mb * 1024 * 1024)  # Exact size in MB
            return io.BytesIO(content.encode()), f"large_test_{size_mb}mb.txt", "text/plain"

    def test_file_upload(self, file_size_mb=1):
        """Test file upload with plan limits"""
        print(f"\n🧪 Testing file upload ({file_size_mb}MB)...")

        try:
            file_obj, filename, content_type = self.create_test_file(
                file_size_mb, "large")

            files = {
                "file": (filename, file_obj, content_type)
            }

            response = requests.post(
                f"{BASE_URL}/files/upload",
                headers=self.get_headers(),
                files=files
            )

            print(f"Upload response status: {response.status_code}")
            print(f"Upload response: {response.text}")

            if response.status_code == 200:
                print(f"✅ File uploaded successfully")
                return True
            elif response.status_code == 402:
                print(f"⚠️ Upload blocked by plan limits (expected for large files)")
                return False
            else:
                print(f"❌ Upload failed with status {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Upload error: {e}")
            return False

    def test_summarize_endpoint(self):
        """Test summarize endpoint with plan limits"""
        print(f"\n🧪 Testing summarize endpoint...")

        try:
            # First, we need to upload a file to summarize
            file_obj, filename, content_type = self.create_test_file(1, "text")

            files = {
                "file": (filename, file_obj, content_type)
            }

            upload_response = requests.post(
                f"{BASE_URL}/files/upload",
                headers=self.get_headers(),
                files=files
            )

            if upload_response.status_code != 200:
                print(
                    f"❌ Cannot test summarize - upload failed: {upload_response.status_code}")
                return False

            file_data = upload_response.json()
            file_id = file_data["id"]

            # Now test summarize
            summarize_response = requests.post(
                f"{BASE_URL}/files/summarize/{file_id}",
                headers=self.get_headers()
            )

            print(
                f"Summarize response status: {summarize_response.status_code}")
            print(f"Summarize response: {summarize_response.text}")

            if summarize_response.status_code == 200:
                print(f"✅ Summarize completed successfully")
                return True
            elif summarize_response.status_code == 402:
                print(f"⚠️ Summarize blocked by plan limits")
                return False
            else:
                print(
                    f"❌ Summarize failed with status {summarize_response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Summarize error: {e}")
            return False

    def test_plan_limits_scenarios(self):
        """Test various plan limit scenarios"""
        print(f"\n🧪 Testing plan limits scenarios...")

        # Test 1: Small file upload (should work for Free plan)
        print("\n--- Test 1: Small file upload (1MB) ---")
        self.test_file_upload(1)

        # Test 2: Medium file upload (might be blocked for Free plan)
        print("\n--- Test 2: Medium file upload (5MB) ---")
        self.test_file_upload(5)

        # Test 3: Large file upload (should be blocked for Free plan)
        print("\n--- Test 3: Large file upload (20MB) ---")
        self.test_file_upload(20)

        # Test 4: Summarize endpoint
        print("\n--- Test 4: Summarize endpoint ---")
        self.test_summarize_endpoint()

    def get_user_usage_stats(self):
        """Get user usage statistics"""
        print(f"\n📊 Getting user usage statistics...")

        try:
            response = requests.get(
                f"{BASE_URL}/users/me/usage",
                headers=self.get_headers()
            )

            if response.status_code == 200:
                usage_data = response.json()
                print(f"✅ Usage stats retrieved:")
                print(json.dumps(usage_data, indent=2))
                return usage_data
            else:
                print(f"❌ Failed to get usage stats: {response.status_code}")
                print(f"Response: {response.text}")
                return None

        except Exception as e:
            print(f"❌ Error getting usage stats: {e}")
            return None

    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting Plan Limits Test Suite")
        print("=" * 50)

        # Step 1: Authenticate
        if not self.authenticate():
            print("❌ Cannot proceed without authentication")
            return

        # Step 2: Get user info
        user_info = self.get_user_info()
        if not user_info:
            print("❌ Cannot proceed without user info")
            return

        # Step 3: Get usage stats
        self.get_user_usage_stats()

        # Step 4: Run plan limits tests
        self.test_plan_limits_scenarios()

        # Step 5: Get final usage stats
        print("\n📊 Final usage statistics:")
        self.get_user_usage_stats()

        print("\n✅ Test suite completed!")


if __name__ == "__main__":
    test_suite = PlanLimitsTestSuite()
    test_suite.run_all_tests()
