# CBT App

Simple Flask CBT application. This repository is configured for deployment to Heroku.

Local setup

1. Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate
pip install -r requirements.txt
```

Run locally:

```powershell
python -u code1.py
```

GitHub and Heroku

- Ensure you have `git`, the GitHub CLI `gh`, and the Heroku CLI installed and authenticated.
- To create a GitHub repo and push:

```powershell
git init
git add .
git commit -m "Initial commit"
gh repo create <your-username>/<repo-name> --public --source . --remote origin --push
```

- To create a Heroku app and deploy:

```powershell
heroku login
heroku create
git push heroku main
```
# CBT App (FastAPI) — Run Instructions

Quick steps to set up and run the FastAPI app on Windows (PowerShell).

Prerequisites
- Python 3.10+ installed and available on PATH.

1) Create and activate a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2) Install dependencies

```powershell
pip install -r requirements.txt
```

3) (Optional) Set email credentials as environment variables (recommended)

```powershell
# Temporary for current session
$env:EMAIL_ADDRESS = 'you@example.com'
$env:EMAIL_PASSWORD = 'your_email_password'

# Or create a .env file and use python-dotenv in app if you modify the code
```

4) Run the app (development)

```powershell
# preferred: use uvicorn from the venv
uvicorn app:app --reload --host 0.0.0.0 --port 8000

# alternative (runs the module entrypoint that calls uvicorn)
python app.py

# if uvicorn isn't available directly
python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

5) Open in browser

Visit http://127.0.0.1:8000/login

Notes
- The app uses SQLite at `sqlite:///./test.db`; the file will be created automatically.
- `app.py` currently contains hard-coded email credentials — use environment variables or update the code before deploying.
- If Excel uploads fail, ensure `openpyxl` is installed (`pip install openpyxl`).
- If you want, I can start the venv installation and launch the server for you now.
