# Backend Startup Repair Guide

## Root Causes Identified

### Error 1: `ModuleNotFoundError: No module named 'pydantic_core._pydantic_core'`
**Root Cause**: Python 3.14.3 incompatibility
- pydantic-core 2.41.5 has no pre-built wheels for Python 3.14
- Current .venv created for Python 3.14 but packages compiled for 3.13
- Need either Python 3.13 or update requirements to compatible versions

### Error 2: `Unable to load celery application. The module app.celery_app was not found`
**Root Cause**: Incorrect Celery module path
- Celery is defined in `celery_worker.py` at project root, not `app/celery_app.py`
- Command should be: `celery -A celery_worker worker` not `celery -A app.celery_app worker`

### Error 3: Multiple venvs causing confusion
**Root Cause**: Two virtual environments (.venv and venv) with different Python versions
- `.venv`: Python 3.14 (incompatible)
- `venv`: Python 3.13 (compatible)
- Should consolidate to single venv

## Solution Strategy

1. Remove incompatible .venv (Python 3.14)
2. Use venv with Python 3.13
3. Update requirements for Python 3.13 compatibility
4. Fix pydantic-core installation
5. Verify all imports and dependencies
6. Test all startup scenarios

## Implementation Steps

### Step 1: Clean Up and Consolidate
```bash
# Remove the incompatible .venv
rmdir /s /q ".venv"

# Keep only venv (Python 3.13 compatible)
# Verify venv Python version
venv\Scripts\python.exe --version
```

### Step 2: Update Requirements for Python 3.13
- Downgrade pydantic==2.12.5 to pydantic==2.5.0 (more stable)
- Keep pydantic-core==2.10.1 (compatible with Python 3.13)
- Update FastAPI/Starlette versions for better compatibility

### Step 3: Reinstall Dependencies
```bash
venv\Scripts\pip.exe uninstall -y pydantic pydantic-core pydantic-settings
venv\Scripts\pip.exe install -r requirements.txt
```

### Step 4: Verify Installation
```bash
venv\Scripts\python.exe -c "from fastapi import FastAPI; print('✓ FastAPI OK')"
venv\Scripts\python.exe -c "import pydantic_core; print('✓ pydantic-core OK')"
venv\Scripts\python.exe -c "from celery_worker import celery; print('✓ Celery OK')"
```

### Step 5: Start Services
```bash
# Redis (required)
redis-server

# FastAPI
venv\Scripts\uvicorn.exe app.main:app --reload --host 0.0.0.0 --port 8000

# Celery Worker (in new terminal)
venv\Scripts\celery.exe -A celery_worker worker --loglevel=info

# Celery Beat (in new terminal, if needed)
venv\Scripts\celery.exe -A celery_worker beat --loglevel=info
```

## Expected Outcomes
- ✔ FastAPI server starts without pydantic errors
- ✔ Swagger UI opens at http://localhost:8000/docs
- ✔ Celery worker starts and connects to Redis
- ✔ All models import correctly
- ✔ No startup warnings
- ✔ Database migrations can run

## Troubleshooting

### If still getting pydantic errors:
1. Check Python version: `python --version` should show 3.13.x
2. Check pydantic install: `pip show pydantic pydantic-core`
3. Rebuild venv completely if needed

### If Celery still fails:
1. Verify celery_worker.py exists at project root
2. Test import: `python -c "from celery_worker import celery; print(celery)"`
3. Check Redis is running: `redis-cli ping` should return PONG

### If database errors:
1. Verify DATABASE_URL in .env
2. Run migrations: `alembic upgrade head`
3. Check PostgreSQL is running

### If WebSocket errors:
1. Check websocket routes are properly imported in main.py
2. Verify async context in WebSocket handlers
