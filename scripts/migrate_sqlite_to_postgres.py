"""
Simple helper to copy data from a local SQLite file into a Postgres database (e.g. Heroku Postgres).

Usage:
  python scripts/migrate_sqlite_to_postgres.py --source cbt.db --dest $DATABASE_URL --dry-run
  python scripts/migrate_sqlite_to_postgres.py --source cbt.db --dest postgresql://... --clear

Notes:
- This script uses pandas to read tables from SQLite and write to Postgres. It preserves row data but not
  advanced constraints, triggers or indexes. Use proper migration tooling (Alembic) for production schema migrations.
- Ensure `psycopg2-binary` is in your `requirements.txt` and `pandas` is installed.
"""

import os
import argparse
import sys
import sqlalchemy as sa
import pandas as pd
from sqlalchemy import inspect


def parse_args():
    p = argparse.ArgumentParser(description='Migrate sqlite to Postgres (simple row copy)')
    p.add_argument('--source', '-s', default='cbt.db', help='Path to sqlite file (default: cbt.db)')
    p.add_argument('--dest', '-d', default=os.environ.get('DATABASE_URL'), help='Destination SQLAlchemy URL (default: env DATABASE_URL)')
    p.add_argument('--tables', '-t', help='Comma-separated list of tables to migrate (default: all)')
    p.add_argument('--dry-run', action='store_true', help='Only show tables and row counts, do not copy')
    p.add_argument('--clear', action='store_true', help='Truncate destination tables before copying')
    p.add_argument('--chunksize', type=int, default=1000, help='Rows per insert chunk')
    return p.parse_args()


def main():
    args = parse_args()

    if not os.path.exists(args.source):
        print('Source sqlite file not found:', args.source)
        sys.exit(2)

    if not args.dest and not args.dry_run:
        print('No destination provided. Set --dest or DATABASE_URL env var. Use --dry-run to inspect source.')
        sys.exit(2)

    src_url = f"sqlite:///{os.path.abspath(args.source)}"
    print('Source:', src_url)
    if args.dest:
        print('Destination:', args.dest)

    src_engine = sa.create_engine(src_url)
    inspector = inspect(src_engine)
    tables = inspector.get_table_names()
    # Filter out sqlite internal tables
    tables = [t for t in tables if not t.startswith('sqlite_')]

    if args.tables:
        wanted = [t.strip() for t in args.tables.split(',') if t.strip()]
        tables = [t for t in tables if t in wanted]

    if not tables:
        print('No tables found to migrate.')
        return

    print('Found tables:', ', '.join(tables))

    # Dry-run: show row counts
    if args.dry_run:
        for t in tables:
            try:
                c = src_engine.execute(sa.text(f"SELECT COUNT(1) as cnt FROM \"{t}\""))
                cnt = c.scalar()
            except Exception:
                # fallback using pandas
                df = pd.read_sql_table(t, src_engine)
                cnt = len(df)
            print(f'Table {t}: {cnt} rows')
        print('Dry-run complete.')
        return

    # connect to destination
    dest_engine = sa.create_engine(args.dest)

    # Optionally clear destination tables
    if args.clear:
        with dest_engine.begin() as conn:
            for t in tables:
                try:
                    conn.execute(sa.text(f'TRUNCATE TABLE "{t}" RESTART IDENTITY CASCADE'))
                    print('Truncated', t)
                except Exception as e:
                    print('Failed to truncate', t, '-', e)

    # Copy tables
    for t in tables:
        print('Migrating table', t)
        try:
            # read in chunks to avoid memory spikes
            offset = 0
            total = 0
            # use pandas.read_sql_query with limit/offset if supported
            # but sqlite supports LIMIT/OFFSET; we'll stream with chunksize
            for chunk in pd.read_sql_table(t, src_engine, chunksize=args.chunksize):
                # write to dest
                chunk.to_sql(t, dest_engine, if_exists='append', index=False, method='multi', chunksize=args.chunksize)
                total += len(chunk)
            print(f'  completed: {total} rows')
        except ValueError as ve:
            # pandas may fail to reflect table dtypes; fallback to read_sql with query
            try:
                df = pd.read_sql_query(f'SELECT * FROM "{t}"', src_engine)
                df.to_sql(t, dest_engine, if_exists='append', index=False, method='multi', chunksize=args.chunksize)
                print('  completed (fallback):', len(df), 'rows')
            except Exception as e:
                print('  FAILED to migrate table', t, e)
        except Exception as e:
            print('  FAILED to migrate table', t, e)

    print('\nMigration finished. Verify your destination DB schema and indexes.')


if __name__ == '__main__':
    main()
