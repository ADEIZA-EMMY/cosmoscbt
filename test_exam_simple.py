#!/usr/bin/env python
"""Simple test - logs to file instead of stdout"""
import requests
import sys

# Log to file
logfile = open('test_exam_flow.log', 'w', encoding='utf-8')

def log(msg):
    print(msg, file=logfile)
    logfile.flush()

try:
    BASE_URL = "http://127.0.0.1:5000"
    session = requests.Session()
    
    log("=== STARTING TEST ===")
    
    # Test 1: Login
    log("\n1. Testing login...")
    resp = session.post(f"{BASE_URL}/login", data={
        'username': '100001',
        'password': '100001',
        'user_type': 'student'
    })
    log(f"   Login status: {resp.status_code}")
    log(f"   Final URL: {resp.url}")
    
    # Test 2: Try exam endpoint
    log("\n2. Testing exam endpoint...")
    resp = session.get(f"{BASE_URL}/student/exam/1", allow_redirects=True)
    log(f"   Exam status: {resp.status_code}")
    log(f"   Final URL: {resp.url}")
    
    # Check if session_id is in response
    if 'examSessionId' in resp.text:
        log("   ✓ examSessionId found in response")
        # Extract it
        import re
        match = re.search(r'const examSessionId = (\d+)', resp.text)
        if match:
            session_id = match.group(1)
            log(f"   ✓ Extracted session_id: {session_id}")
            
            # Test 3: Get first question
            log(f"\n3. Testing question fetch (session {session_id})...")
            resp = session.get(f"{BASE_URL}/api/exam/{session_id}/question/0")
            data = resp.json()
            log(f"   Response: {data}")
            
            if 'error' in data:
                log(f"   ✗ ERROR: {data['error']}")
            else:
                log(f"   ✓ SUCCESS: Got {data.get('total_questions', '?')} questions")
        else:
            log("   ✗ Could not extract session_id")
    else:
        log("   ✗ examSessionId NOT in response")
        log(f"   Response text (first 500 chars): {resp.text[:500]}")
    
    log("\n=== TEST COMPLETE ===")
    
except Exception as e:
    log(f"ERROR: {type(e).__name__}: {e}")
    import traceback
    log(traceback.format_exc())

finally:
    logfile.close()
    print("Log written to test_exam_flow.log")
