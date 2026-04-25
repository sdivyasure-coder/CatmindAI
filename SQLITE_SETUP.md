# SQLite Installation - Step by Step

## Quick Setup (Copy & Paste Commands)

### Step 1: Install Dependencies
```bash
python -m pip install --upgrade pip setuptools wheel

pip install fastapi==0.104.1 uvicorn==0.24.0 sqlalchemy==2.0.23 alembic==1.12.1 pydantic==2.5.0 pydantic-settings==2.1.0 python-jose[cryptography]==3.3.0 passlib[bcrypt]==1.7.4 python-dotenv==1.0.0 aiohttp==3.9.1 openai==1.3.9 pytest==7.4.3 pytest-asyncio==0.21.1 httpx==0.25.2
```

### Step 2: Setup SQLite
```bash
python setup_sqlite.py
```

### Step 3: Create Project Files
```bash
python setup.py
```

### Step 4: Initialize Database
```bash
alembic upgrade head
```

### Step 5: Start Server
```bash
uvicorn app.main:app --reload
```

### Step 6: Access API
Open in browser:
```
http://localhost:8000/docs
```

---

## What This Does

✅ Uses **SQLite** instead of PostgreSQL (no DB server needed)
✅ Creates database file: `smart_learning.db`
✅ Generates all API endpoints
✅ Creates authentication system
✅ Sets up analytics & leaderboard
✅ Configures AI integration

---

## Database File

The database will be created at:
```
d:\codemindai\smart_learning.db
```

You can view/edit it with any SQLite viewer:
- DB Browser for SQLite (free): https://sqlitebrowser.org/
- VS Code extension: SQLite (by alexcvzz)

---

## To Reset Database

Delete the file and re-run migrations:
```bash
del smart_learning.db
alembic upgrade head
```

---

## Issues?

If you get errors, make sure:
1. ✅ You're in `d:\codemindai` directory
2. ✅ Python 3.9+ installed: `python --version`
3. ✅ All dependencies installed: `pip list | findstr sqlalchemy`

---

## Ready? Run these commands:

```bash
python -m pip install --upgrade pip setuptools wheel
pip install fastapi==0.104.1 uvicorn==0.24.0 sqlalchemy==2.0.23 alembic==1.12.1 pydantic==2.5.0 pydantic-settings==2.1.0 python-jose[cryptography]==3.3.0 passlib[bcrypt]==1.7.4 python-dotenv==1.0.0 aiohttp==3.9.1 openai==1.3.9 pytest==7.4.3 pytest-asyncio==0.21.1 httpx==0.25.2
python setup_sqlite.py
python setup.py
alembic upgrade head
uvicorn app.main:app --reload
```

Then open: http://localhost:8000/docs
