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

Heroku / SQLite notes
- Heroku dyno filesystem is ephemeral: any files written at runtime (including a SQLite
  database file) will be lost after a dyno restart or deploy. For reliable persistence on
  Heroku use the Heroku Postgres add-on or another external database (RDS, Cloud SQL).
- If you intend to keep using a local SQLite file and want to include it in the GitHub
  repo for deployment/testing, remove or negate the `*.db` ignore and commit the file
  (this repo includes `!cbt.db` in `.gitignore` to allow that). Be cautious: committing
  DB files can leak sensitive data and increase repo size.
- To force the app to use SQLite even when `DATABASE_URL` is present, set env var
  `FORCE_SQLITE=1` (the app also supports `SQLITE_URL` if you want a custom SQLAlchemy URL).

Recommended workflow to preserve data when moving between environments
- Backup your SQLite file before deploy:

```bash
# locally
cp cbt.db cbt.db.backup
git add cbt.db && git commit -m "include sqlite DB for deployment"
git push origin main
```

- Better: upload the DB to durable object storage (S3) and restore it on the target host,
  or migrate to Postgres using the helper script:

```bash
python scripts/migrate_sqlite_to_postgres.py --source cbt.db --dest $DATABASE_URL
```

If you'd like, I can:
- remove the `*.db` rule and commit a current `cbt.db` for you,
- or add an automated S3 backup/restore script for Heroku releases.
