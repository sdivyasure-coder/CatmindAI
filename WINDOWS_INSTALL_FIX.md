# Windows Installation Issues - Workarounds

## Issue: psycopg2-binary installation fails

### Solution 1: Use pre-built wheels (RECOMMENDED)
```bash
pip install --only-binary psycopg2-binary -r requirements.txt
```

### Solution 2: Install PostgreSQL first (if not installed)
Download and install PostgreSQL from: https://www.postgresql.org/download/windows/

Then retry:
```bash
pip install -r requirements.txt
```

### Solution 3: Use alternative database (SQLite for development)
Edit `app/config.py` and change:
```python
DATABASE_URL: str = "sqlite:///./test.db"
```

Then install without psycopg2:
```bash
pip install fastapi uvicorn sqlalchemy alembic pydantic pydantic-settings python-jose passlib python-dotenv aiohttp openai pytest pytest-asyncio httpx
```

### Solution 4: Use Docker (no local dependencies needed)
```bash
docker-compose up --build
```

---

## If Installation Still Fails

Try upgrading pip:
```bash
python -m pip install --upgrade pip
```

Then try again:
```bash
pip install -r requirements.txt
```

---

## For Production: Use PostgreSQL

You'll need PostgreSQL installed locally or use Docker/Cloud hosted PostgreSQL.

Docker option (easiest):
```bash
docker-compose up
```

This starts both PostgreSQL and FastAPI automatically.
