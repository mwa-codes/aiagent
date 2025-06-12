import requests
import os

API_URL = "http://localhost:8000/gpt/summarize"
TOKEN = os.getenv("TEST_USER_TOKEN")  # Or set manually if needed

# Example: get a token (if you want to automate)


def get_token():
    resp = requests.post(
        "http://localhost:8000/auth/login",
        json={"email": "test@example.com", "password": "TestPass123!"}
    )
    return resp.json().get("access_token")


def test_summarize_short():
    token = TOKEN or get_token()
    headers = {"Authorization": f"Bearer {token}"}
    data = {"text": "OpenAI develops advanced AI models. Their GPT-4.1 model is state-of-the-art for summarization."}
    resp = requests.post(API_URL, json=data, headers=headers)
    print("Short text summary:", resp.json())


def test_summarize_long():
    token = TOKEN or get_token()
    headers = {"Authorization": f"Bearer {token}"}
    # Generate a long text (simulate >2000 words)
    long_text = ("This is a sentence about AI. " * 500).strip()
    data = {"text": long_text}
    resp = requests.post(API_URL, json=data, headers=headers)
    print("Long text summary:", resp.json())


if __name__ == "__main__":
    print("Testing /gpt/summarize endpoint...")
    test_summarize_short()
    test_summarize_long()
