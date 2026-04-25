# Docker Not Installed - Use Local Installation Instead

Docker is not installed. Let's use the pip installation method instead.

## Quick Start: Local Installation (No Docker Needed)

### Option A: With PostgreSQL (Production Setup)

You need PostgreSQL installed locally first:
1. Download: https://www.postgresql.org/download/windows/
2. Install with default settings
3. Remember the password you set

Then run:
```bash
python -m pip install --upgrade pip setuptools wheel
pip install --only-binary :all: psycopg2-binary>=2.9
pip install -r requirements.txt
python setup.py
copy .env.example .env
alembic upgrade head
uvicorn app.main:app --reload
```

### Option B: With SQLite (Development Setup - EASIEST)

No additional installation needed! SQLite is built-in.

**Step 1:** Update app config to use SQLite

Edit `app/config.py` and change the DATABASE_URL:

```python
DATABASE_URL: str = "sqlite:///./smart_learning.db"
```

**Step 2:** Install dependencies (without psycopg2):

```bash
python -m pip install --upgrade pip setuptools wheel
pip install fastapi uvicorn sqlalchemy alembic pydantic pydantic-settings python-jose passlib python-dotenv aiohttp openai pytest pytest-asyncio httpx
```

**Step 3:** Setup project

```bash
python setup.py
```

**Step 4:** Run migrations

```bash
alembic upgrade head
```

**Step 5:** Start server

```bash
uvicorn app.main:app --reload
```

**Step 6:** Access API

```
http://localhost:8000/docs
```

---

## Recommendation

Use **Option B (SQLite)** for:
- ✅ Quick local development
- ✅ Testing
- ✅ Learning the system

Use **Option A (PostgreSQL)** for:
- ✅ Production deployment
- ✅ Multiple concurrent users
- ✅ Advanced features

---

## Which Option?

**For now, recommend Option B (SQLite) - fastest way to get running!**

Just run:
```bash
python -m pip install --upgrade pip setuptools wheel
pip install fastapi uvicorn sqlalchemy alembic pydantic pydantic-settings python-jose passlib python-dotenv aiohttp openai pytest pytest-asyncio httpx
python setup.py
alembic upgrade head
uvicorn app.main:app --reload
```

Then open: http://localhost:8000/docs
