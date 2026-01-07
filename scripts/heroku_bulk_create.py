#!/usr/bin/env python3
"""
Bulk-create students by POSTing to the app's /heroku/save_student endpoint.

CSV format: username,password,full_name,student_class,school_id
JSON format: array of objects with the same keys.

Usage examples:
  python scripts/heroku_bulk_create.py --file students.csv --url https://<app>.herokuapp.com/heroku/save_student --token YOUR_TOKEN
  python scripts/heroku_bulk_create.py --file students.json --url https://<app>.herokuapp.com/heroku/save_student --token YOUR_TOKEN

The script prints per-row status and returns non-zero if any failure occurred.
"""
import argparse
import csv
import json
import os
import sys
import time

try:
    import requests
except Exception:
    print('This script requires the requests library. Install with: pip install requests')
    sys.exit(2)


def post_student(url, token, payload, timeout=10):
    headers = {'X-HEROKU-TOKEN': token, 'Content-Type': 'application/json'}
    try:
        r = requests.post(url, json=payload, headers=headers, timeout=timeout)
        try:
            body = r.json()
        except Exception:
            body = r.text
        return r.status_code, body
    except Exception as e:
        return None, str(e)


def load_csv(path):
    rows = []
    with open(path, newline='', encoding='utf-8') as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            rows.append({k.strip(): (v.strip() if isinstance(v, str) else v) for k, v in row.items()})
    return rows


def load_json(path):
    with open(path, 'r', encoding='utf-8') as fh:
        data = json.load(fh)
    if isinstance(data, dict):
        # assume top-level object contains list under 'students' or similar
        if 'students' in data and isinstance(data['students'], list):
            return data['students']
        # otherwise wrap single item
        return [data]
    return data


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--file', '-f', required=True, help='CSV or JSON file with student records')
    p.add_argument('--url', '-u', required=True, help='Full URL to /heroku/save_student on your app')
    p.add_argument('--token', '-t', required=False, help='HEROKU API token (or set HEROKU_API_TOKEN env var)')
    p.add_argument('--delay', type=float, default=0.15, help='Delay between requests in seconds')
    args = p.parse_args()

    token = args.token or os.environ.get('HEROKU_API_TOKEN')
    if not token:
        print('Error: provide --token or set HEROKU_API_TOKEN environment variable')
        return 2

    path = args.file
    if not os.path.exists(path):
        print('File not found:', path)
        return 2

    if path.lower().endswith('.csv'):
        rows = load_csv(path)
    elif path.lower().endswith('.json'):
        rows = load_json(path)
    else:
        print('Unsupported file type; provide .csv or .json')
        return 2

    if not isinstance(rows, list):
        print('No records found in file')
        return 2

    failures = 0
    total = 0
    for i, r in enumerate(rows, start=1):
        total += 1
        username = (r.get('username') or r.get('user') or '').strip()
        if not username:
            print(f'Row {i}: missing username — skipped')
            failures += 1
            continue
        payload = {
            'username': username,
            'password': (r.get('password') or username),
            'full_name': r.get('full_name') or r.get('name') or '',
            'student_class': r.get('student_class') or r.get('class') or '',
        }
        if r.get('school_id'):
            payload['school_id'] = r.get('school_id')

        status, body = post_student(args.url, token, payload)
        if status is None:
            print(f'Row {i} [{username}]: request failed — {body}')
            failures += 1
        elif status in (200, 201):
            print(f'Row {i} [{username}]: OK — {body}')
        else:
            print(f'Row {i} [{username}]: ERROR {status} — {body}')
            failures += 1

        time.sleep(args.delay)

    print(f"\nFinished: {total} rows, failures: {failures}")
    return (1 if failures else 0)


if __name__ == '__main__':
    sys.exit(main())
