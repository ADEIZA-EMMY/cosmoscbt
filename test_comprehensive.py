 #!/usr/bin/env python
"""Comprehensive end-to-end test of exam flow"""
import requests
import re

BASE_URL = "http://127.0.0.1:5000"
session = requests.Session()

def main():
    print("=" * 60)
    print("END-TO-END EXAM FLOW TEST")
    print("=" * 60)

    try:
        # 1. Login as student
        print("\n1. Student Login...")
        resp = session.post(f"{BASE_URL}/login", data={
            'username': '100002',
            'password': '100002',
            'user_type': 'student',
            'school_id': '1'
        })
        assert resp.status_code == 200
        print("   OK - Logged in")
        
        # 2. View dashboard
        print("\n2. Student Dashboard...")
        resp = session.get(f"{BASE_URL}/student/dashboard")
        assert resp.status_code == 200
        assert 'exam' in resp.text.lower()
        print("   OK - Dashboard loaded")
        
        # 3. Start exam
        print("\n3. Start Exam...")
        resp = session.get(f"{BASE_URL}/student/exam/1")
        assert resp.status_code == 200
        
        match = re.search(r'const examSessionId = (\d+)', resp.text)
        assert match, "Could not find examSessionId in page"
        session_id = match.group(1)
        print(f"   OK - Exam started (session {session_id})")
        
        # 4. Get first question
        print("\n4. Fetch First Question...")
        resp = session.get(f"{BASE_URL}/api/exam/{session_id}/question/0")
        data = resp.json()
        
        assert 'error' not in data, f"Got error: {data['error']}"
        assert data['total_questions'] == 155, f"Expected 155 questions, got {data['total_questions']}"
        assert data['question_index'] == 0
        assert 'text' in data['question']
        assert 'options' in data['question']
        assert len(data['question']['options']) > 0
        
        q_text = data['question']['text'][:50]
        print(f"   OK - Got 155 total questions")
        print(f"   Question: {q_text}...")
        print(f"   Options: {len(data['question']['options'])}")
        
        # 5. Save an answer
        print("\n5. Save Answer to First Question...")
        resp = session.post(f"{BASE_URL}/api/exam/{session_id}/answer", 
            json={
                'question_index': 0,
                'answer': 'A'
            }
        )
        assert resp.status_code == 200
        print("   OK - Answer saved")
        
        # 6. Get another question
        print("\n6. Fetch Question 10...")
        resp = session.get(f"{BASE_URL}/api/exam/{session_id}/question/10")
        data = resp.json()
        
        assert data['question_index'] == 10
        assert data['total_questions'] == 155
        print(f"   OK - Got question 10 of 155")
        
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED!")
        print("Students can now access all exam questions!")
        print("=" * 60)
        return 0

    except AssertionError as e:
        print(f"\n  FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n  ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
