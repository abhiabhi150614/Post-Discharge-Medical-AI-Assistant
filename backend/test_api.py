import requests
import uuid
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

def test_chat():
    session_id = str(uuid.uuid4())
    print(f"Testing with Session ID: {session_id}")

    # 1. Test Receptionist - Patient Lookup
    print("\n1. Testing Patient Lookup (Abhishek B Shetty)...")
    payload = {
        "session_id": session_id,
        "message": "Hi, I'm Abhishek B Shetty"
    }
    try:
        res = requests.post(f"{BASE_URL}/chat", json=payload, timeout=30)
        if res.status_code != 200:
            print(f"FAILED: {res.status_code} - {res.text}")
            return
        data = res.json()
        print(f"Response: {data['reply']}")
        if "Abhishek" not in data['reply'] and "found your file" not in data['reply']:
             print("WARNING: Patient might not have been found.")
        else:
             print("SUCCESS: Patient found.")
    except Exception as e:
        print(f"ERROR: {e}")
        return

    # 2. Test Handoff - Medical Query
    print("\n2. Testing Handoff (Medical Query)...")
    payload = {
        "session_id": session_id,
        "message": "I have swelling in my legs. What should I do?"
    }
    try:
        res = requests.post(f"{BASE_URL}/chat", json=payload, timeout=30)
        if res.status_code != 200:
            print(f"FAILED: {res.status_code} - {res.text}")
            return
        data = res.json()
        print(f"Response: {data['reply']}")
        print(f"Agent: {data['agent']}")
        
        if data['agent'] == 'clinical':
            print("SUCCESS: Handed off to Clinical Agent.")
        else:
            print("WARNING: Still with Receptionist (or agent name not updated).")
            
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_chat()
