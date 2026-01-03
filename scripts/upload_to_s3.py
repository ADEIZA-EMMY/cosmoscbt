"""
Upload files from local `uploads/` to S3 and update DB `CommunityPost.attachment` values to the S3 URL.

Usage examples:
  # Dry run (lists files and matching DB rows)
  python scripts/upload_to_s3.py --prefix community --dry-run

  # Real run using env vars for AWS and DATABASE_URL
  AWS_ACCESS_KEY_ID=... AWS_SECRET_ACCESS_KEY=... S3_BUCKET=your-bucket AWS_REGION=us-east-1 python scripts/upload_to_s3.py --prefix community

Notes:
- Script looks at files under local `uploads/` by default and uploads them preserving relative path.
- It updates `CommunityPost.attachment` to the public S3 URL (https://{bucket}.s3.{region}.amazonaws.com/{key}).
- If your bucket is private, you may prefer to store the S3 key in the DB and serve via presigned URLs.
- Requires `boto3` and access to your DB (uses `DATABASE_URL` or sqlite `cbt.db`).
"""

import os
import sys
import argparse
import mimetypes
from urllib.parse import quote_plus

try:
    import boto3
    from botocore.exceptions import ClientError
except Exception:
    boto3 = None

# We'll reuse the application's models if possible
try:
    from code1 import app, db, CommunityPost
    USE_APP_MODELS = True
except Exception:
    USE_APP_MODELS = False


def parse_args():
    p = argparse.ArgumentParser(description='Upload local uploads/ files to S3 and update DB attachment URLs')
    p.add_argument('--uploads-dir', default=os.environ.get('UPLOAD_FOLDER', 'uploads'), help='Local uploads directory (default: uploads)')
    p.add_argument('--prefix', default='community', help='Subfolder under uploads to process (default: community)')
    p.add_argument('--bucket', default=os.environ.get('S3_BUCKET'), help='S3 bucket name (can be set via S3_BUCKET env)')
    p.add_argument('--region', default=os.environ.get('AWS_REGION') or os.environ.get('S3_REGION'), help='AWS region (used to build public URLs)')
    p.add_argument('--dry-run', action='store_true', help='Do not upload or update DB; print actions')
    p.add_argument('--skip-db', action='store_true', help='Upload files but do not update DB')
    p.add_argument('--profile', help='Use AWS profile (boto3)')
    return p.parse_args()


def build_s3_url(bucket, key, region=None):
    # Use virtual-hosted-style URL; note region-specific endpoints
    key_quoted = quote_plus(key)
    if region and region != 'us-east-1':
        return f'https://{bucket}.s3.{region}.amazonaws.com/{key}'
    return f'https://{bucket}.s3.amazonaws.com/{key}'


def main():
    args = parse_args()

    uploads_dir = args.uploads_dir
    subdir = args.prefix.strip('/')
    target_dir = os.path.join(uploads_dir, subdir) if subdir else uploads_dir

    if not os.path.isdir(target_dir):
        print('Uploads subdirectory not found:', target_dir)
        sys.exit(1)

    if boto3 is None:
        print('boto3 is required. Install with pip install boto3')
        sys.exit(1)

    if not args.bucket and not args.dry_run:
        print('S3 bucket not specified. Use --bucket or set S3_BUCKET env var')
        sys.exit(1)

    session_kwargs = {}
    if args.profile:
        session_kwargs['profile_name'] = args.profile
    aws_session = boto3.Session(**session_kwargs) if session_kwargs else boto3.Session()
    s3 = aws_session.client('s3')

    # Walk files under target_dir
    files = []
    for root, dirs, filenames in os.walk(target_dir):
        for fn in filenames:
            full = os.path.join(root, fn)
            rel = os.path.relpath(full, uploads_dir).replace('\\', '/')
            files.append((full, rel))

    if not files:
        print('No files found under', target_dir)
        return

    print(f'Found {len(files)} files under {target_dir}')

    if args.dry_run:
        print('Dry-run: listing files and any matching DB rows (no uploads or DB changes)')

    # If using app models, we can lookup CommunityPost rows that reference the local rel path
    if USE_APP_MODELS and not args.skip_db:
        app_ctx = app.app_context()
        app_ctx.push()

    for full, rel in files:
        print('File:', rel)
        if args.dry_run:
            if USE_APP_MODELS and not args.skip_db:
                rows = CommunityPost.query.filter(CommunityPost.attachment == rel).all()
                print('  matched CommunityPost rows:', len(rows))
                for r in rows:
                    print('   - id=', r.id)
            continue

        # Upload to S3 under the same key as rel
        key = rel
        ctype, _ = mimetypes.guess_type(full)
        extra_args = {}
        if ctype:
            extra_args['ContentType'] = ctype
        try:
            print(f'  uploading to s3://{args.bucket}/{key} ...', end=' ')
            with open(full, 'rb') as fh:
                s3.upload_fileobj(fh, args.bucket, key, ExtraArgs=extra_args)
            url = build_s3_url(args.bucket, key, args.region)
            print('done. URL=', url)
        except ClientError as e:
            print('FAILED to upload:', e)
            continue
        except Exception as e:
            print('FAILED to upload:', e)
            continue

        # Update DB rows that referenced the local relative path
        if USE_APP_MODELS and not args.skip_db:
            try:
                rows = CommunityPost.query.filter(CommunityPost.attachment == rel).all()
                if not rows:
                    # also try matching without the subdir (older records might have just filename)
                    rows = CommunityPost.query.filter(CommunityPost.attachment == os.path.basename(rel)).all()
                for r in rows:
                    print('   updating post id', r.id)
                    r.attachment = url
                db.session.commit()
            except Exception as e:
                try:
                    db.session.rollback()
                except Exception:
                    pass
                print('   Failed to update DB for', rel, '-', e)

    if USE_APP_MODELS and not args.skip_db:
        app_ctx.pop()

    print('Done.')


if __name__ == '__main__':
    main()
