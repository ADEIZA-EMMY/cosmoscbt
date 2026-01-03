#!/usr/bin/env python3
"""Cross-platform helper to commit and push changes to GitHub and Heroku.
Usage:
  python tools/push_changes.py --message "Your commit message"
"""
import argparse
import subprocess
import sys
import os

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def run(cmd, check=True):
    print('> ' + ' '.join(cmd))
    r = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True)
    if r.stdout:
        print(r.stdout.strip())
    if r.returncode != 0:
        if r.stderr:
            print(r.stderr.strip(), file=sys.stderr)
        if check:
            raise SystemExit(r.returncode)
    return r


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--message', '-m', default='Update: pushed changes')
    p.add_argument('--force', action='store_true')
    args = p.parse_args()

    print('Repository root:', ROOT)

    # detect branch
    r = run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], check=True)
    branch = r.stdout.strip() if r.stdout else None
    if not branch:
        print('Failed to detect git branch', file=sys.stderr); sys.exit(1)
    print('Current branch:', branch)

    # stage all
    run(['git', 'add', '-A'])

    # commit if changes
    status = subprocess.run(['git', 'status', '--porcelain'], cwd=ROOT, text=True, capture_output=True)
    if not status.stdout.strip():
        print('No changes to commit.')
    else:
        run(['git', 'commit', '-m', args.message])

    # push to origin
    print(f'Pushing to origin/{branch}...')
    run(['git', 'push', 'origin', branch])

    # check for heroku remote
    remotes = subprocess.run(['git', 'remote'], cwd=ROOT, text=True, capture_output=True).stdout
    if 'heroku' in remotes.split():
        print('Heroku remote found — pushing to heroku (deploying HEAD to main)')
        try:
            run(['git', 'push', 'heroku', 'HEAD:main'])
        except SystemExit:
            print('Push to Heroku failed. Please check Heroku remote and authentication.', file=sys.stderr)
    else:
        print('No Heroku remote found — skipping Heroku push.')

    print('All done.')

if __name__ == '__main__':
    main()
