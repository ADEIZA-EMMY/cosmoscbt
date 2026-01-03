#!/usr/bin/env python
"""Test the exam/question flow without browser."""
import requests
import json

BASE_URL = "http://127.0.0.1:5000"
session = requests.Session()

def main():
    print("=== TEST STUDENT EXAM FLOW ===\n")

    # Step 1: Login as student
    print("1. Logging in as student (code 100001)...")
    resp = session.post(f"{BASE_URL}/login", data={
        'username': '100002',
        'password': '100002',
        'user_type': 'student',
        'school_id': '1'
    })
    if resp.status_code == 200:
        print("✓ Login successful")
    else:
        print(f"✗ Login failed: {resp.status_code}")
        print(resp.text[:200])
        return 1

    # Step 2: Get student dashboard to find exam
    print("\n2. Getting student dashboard...")
    resp = session.get(f"{BASE_URL}/student/dashboard")
    if "exam" in resp.text.lower():
        print("✓ Dashboard loaded with exam")
    else:
        print("✗ No exam found on dashboard")

    # Step 3: Start exam
    print("\n3. Starting exam (exam_id=1)...")
    resp = session.get(f"{BASE_URL}/student/exam/1")
    if resp.status_code == 200:
        # Extract session_id from template
        import re
        match = re.search(r'const examSessionId = (\d+)', resp.text)
        if match:
            session_id = match.group(1)
            print(f"✓ Exam started, session_id={session_id}")
        else:
            print(f"✗ Could not extract session_id from page")
            print("Response contains:", resp.text[1000:2000])
            return 1
    else:
        print(f"✗ Failed to start exam: {resp.status_code}")
        print(resp.text[:500])
        return 1

    # Step 4: Fetch first question via API
    print(f"\n4. Fetching first question (session_id={session_id})...")
    resp = session.get(f"{BASE_URL}/api/exam/{session_id}/question/0")
    data = resp.json()

    if "error" in data:
        print(f"✗ Error fetching question: {data['error']}")
        return 1

    if "question" in data:
        q = data["question"]
        print(f"✓ Question loaded!")
        print(f"  - Total questions: {data['total_questions']}")
        print(f"  - Question index: {data['question_index']}")
        print(f"  - Text: {q['text'][:60]}...")
        print(f"  - Options: {len(q['options'])} options")
        print(f"  - Marks: {q['marks']}")
    else:
        print(f"✗ Unexpected response: {data}")
        return 1

    print("\n=== TEST COMPLETE ===")
    print("✓ All checks passed! Questions are now accessible to students.")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
