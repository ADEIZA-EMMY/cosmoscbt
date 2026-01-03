Deployment checklist for Heroku (Postgres + S3)

1) Add required env vars on Heroku
- DATABASE_URL (Heroku sets this automatically when you add the Postgres addon)
- SECRET_KEY (set a secure random secret)
- S3_BUCKET, AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION
- Optional: S3_PREFIX or other settings

2) Provision Postgres on Heroku
- heroku addons:create heroku-postgresql:hobby-dev --app YOUR_APP_NAME

3) Add dependencies and push
- Ensure `requirements.txt` contains `psycopg2-binary`, `boto3`, `pandas`, etc.
- git add . && git commit -m "prepare for heroku: postgres + s3" && git push heroku main

4) Run DB migrations / create tables
- heroku run python -c "from code1 import db; db.create_all()" --app YOUR_APP_NAME

5) Migrate existing sqlite data (optional)
- Locally, create dump or use helper script: `python scripts/migrate_sqlite_to_postgres.py --source cbt.db --dest $DATABASE_URL`

6) Move uploads to S3 (optional, recommended)
- Run: AWS_* env vars set, then:
  python scripts/upload_to_s3.py --prefix community
- Verify attachments updated in DB to S3 URLs

7) Verify
- Visit your app, test posting and attachments, ensure data persists after dyno restart.

Notes & security
- Do NOT store credentials in repo. Use Heroku config vars.
- Consider enabling SSL enforcement and Postgres credentials rotation.
- For production, convert runtime ALTERs into Alembic migrations.
