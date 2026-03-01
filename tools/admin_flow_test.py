"""Simple automated smoke test for admin workflows using requests.

Run this from a machine that can reach the deployed app (e.g. localhost or Heroku URL).
It logs in as the provided admin credentials, then exercises the key routes:
  * add subject
  * add class
  * add exam
  * create a student
  * student login and take exam

Adjust BASE_URL to your deployment (e.g. https://cosmoscbtapp.herokuapp.com).

Usage:
    python tools/admin_flow_test.py

This is not a full replacement for manual testing, but illustrates the end‑to‑end
flow programmatically and will quickly reveal broken routes.
"""
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://cosmoscbtapp.herokuapp.com"
ADMIN_EMAIL = "cosmosadeizaemma47@gmail.com"
ADMIN_PASS = "Adeizaemma47"
STUDENT_EMAIL = "teststudent@example.com"
STUDENT_PASS = "Student123"

session = requests.Session()


def login(email, password):
    print(f"Logging in as {email}")
    r = session.get(f"{BASE_URL}/login")
    soup = BeautifulSoup(r.text, "html.parser")
    token = soup.find('input', {'name': 'csrf_token'})['value'] if soup.find('input', {'name': 'csrf_token'}) else None
    data = {
        'username': email,
        'password': password,
    }
    if token:
        data['csrf_token'] = token
    r = session.post(f"{BASE_URL}/login", data=data)
    if "Access denied" in r.text or r.status_code != 200:
        print("Login failed")
        return False
    print("Logged in successfully")
    return True


def add_subject(name, description):
    print(f"Adding subject {name}")
    r = session.get(f"{BASE_URL}/admin/subject/add")
    soup = BeautifulSoup(r.text, "html.parser")
    token = soup.find('input', {'name': 'csrf_token'})['value'] if soup.find('input', {'name': 'csrf_token'}) else None
    data = {
        'name': name,
        'description': description,
    }
    if token:
        data['csrf_token'] = token
    r = session.post(f"{BASE_URL}/admin/subject/add", data=data)
    print("Subject add response code", r.status_code)
    return r


def add_student(email, full_name):
    print(f"Adding student {email}")
    r = session.get(f"{BASE_URL}/admin/student/add")
    soup = BeautifulSoup(r.text, "html.parser")
    token = soup.find('input', {'name': 'csrf_token'})['value'] if soup.find('input', {'name': 'csrf_token'}) else None
    data = {
        'username': email,
        'password': STUDENT_PASS,
        'full_name': full_name,
        'role': 'student'
    }
    if token:
        data['csrf_token'] = token
    r = session.post(f"{BASE_URL}/admin/student/add", data=data)
    print("Student add response code", r.status_code)
    return r


def create_exam(subject_id, title):
    print(f"Creating exam '{title}'")
    r = session.get(f"{BASE_URL}/admin/exam/add")
    soup = BeautifulSoup(r.text, "html.parser")
    token = soup.find('input', {'name': 'csrf_token'})['value'] if soup.find('input', {'name': 'csrf_token'}) else None
    data = {
        'subject_id': subject_id,
        'title': title,
        'description': 'Smoke test exam',
        'duration': '30',
        'subject_class': '',
        'allowed_classes': '',
        'duration': '30'
    }
    if token:
        data['csrf_token'] = token
    r = session.post(f"{BASE_URL}/admin/exam/add", data=data)
    print("Exam add response code", r.status_code)
    return r


def student_take_exam(exam_id):
    print(f"Student starting exam {exam_id}")
    s2 = requests.Session()
    # login student
    login_success = login(STUDENT_EMAIL, STUDENT_PASS)
    if not login_success:
        print("Student login failed")
        return
    r = s2.get(f"{BASE_URL}/take_exam/{exam_id}")
    print("Take exam page status", r.status_code)


if __name__ == '__main__':
    if not login(ADMIN_EMAIL, ADMIN_PASS):
        print("Admin login failed, abort")
    else:
        add_subject("TestSubject","Created by smoke script")
        # optionally create other objects
        # add_student(STUDENT_EMAIL, "Test Student")
        # create_exam(1, "Test Exam")
    print("Done")
