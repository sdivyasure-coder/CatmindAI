# Windows Installation Guide - Option 1

## Step-by-Step Installation

### 1. Fix psycopg2 Installation
Run this command first:
```bash
pip install --only-binary :all: psycopg2-binary>=2.9
```

### 2. Install All Requirements
```bash
pip install -r requirements.txt
```

### 3. If Still Getting Errors
Try upgrading pip first:
```bash
python -m pip install --upgrade pip
python -m pip install --upgrade setuptools wheel
```

Then retry:
```bash
pip install --only-binary :all: psycopg2-binary>=2.9
pip install -r requirements.txt
```

---

## Complete Setup Sequence

Copy and paste these commands in order:

```bash
# 1. Upgrade pip
python -m pip install --upgrade pip setuptools wheel

# 2. Install psycopg2 with binary wheels
pip install --only-binary :all: psycopg2-binary>=2.9

# 3. Install all requirements
pip install -r requirements.txt

# 4. Create project files
python setup.py

# 5. Copy environment file
copy .env.example .env

# 6. Run migrations
alembic upgrade head

# 7. Start server
uvicorn app.main:app --reload
```

---

## Access API

Once running, open in browser:
```
http://localhost:8000/docs
```

This opens the interactive API documentation.

---

## Troubleshooting

**If you still get errors:**

1. Make sure you're in the `d:\codemindai` directory
2. Verify Python is installed: `python --version`
3. Verify pip: `pip --version`
4. Try using: `pip install -r requirements.txt --upgrade`

**If psycopg2 still fails:**

Use Docker instead:
```bash
docker-compose up --build
```

---

## PostgreSQL Note

You'll need PostgreSQL installed locally OR use:
- Docker (recommended - no local install needed)
- Cloud PostgreSQL (RDS, Azure Database, etc.)

For local PostgreSQL:
https://www.postgresql.org/download/windows/
