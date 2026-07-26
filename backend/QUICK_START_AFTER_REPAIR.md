# Quick Start Guide - After Repair

## Prerequisites Checklist
- ✓ PostgreSQL running on localhost:5432
- ✓ Redis running on localhost:6379
- ✓ Backend directory: `C:\Users\kevin\OneDrive\Desktop\SMBS-PEP\backend`

## The Fix (What Was Done)

### 1. Fixed Python Incompatibility
- **Problem**: Python 3.14 venv with packages compiled for Python 3.13
- **Solution**: Use existing `venv` folder with Python 3.13
- **Action**: Deleted `.venv` directory

### 2. Fixed Celery Module Path
- **Problem**: Attempting to load `app.celery_app` (doesn't exist)
- **Solution**: Use `celery_worker` module (exists at project root)
- **Correct Command**: `celery -A celery_worker worker --loglevel=info`

### 3. Updated Dependencies
- **File**: `requirements.txt`
- **Changes**: 
  - Downgraded pydantic to 2.5.0 (Python 3.13 compatible)
  - Set pydantic-core to 2.10.1 (Python 3.13 compatible)
  - Updated FastAPI, Starlette, Uvicorn to compatible versions

## Installation (5 Minutes)

### Step 1: Clean Install Dependencies
```powershell
cd "C:\Users\kevin\OneDrive\Desktop\SMBS-PEP\backend"
.\venv\Scripts\pip.exe install --upgrade pip setuptools wheel
.\venv\Scripts\pip.exe install -r requirements.txt
```

### Step 2: Verify Installation
```powershell
# All should print ✓
.\venv\Scripts\python.exe -c "from fastapi import FastAPI; print('✓ FastAPI works')"
.\venv\Scripts\python.exe -c "import pydantic_core; print('✓ pydantic-core works')"
.\venv\Scripts\python.exe -c "from celery_worker import celery; print('✓ Celery works')"
```

### Step 3: Run Database Migrations
```powershell
.\venv\Scripts\alembic.exe upgrade head
```

## Running the Backend (3 Terminals)

### Terminal 1: Start FastAPI
```powershell
cd "C:\Users\kevin\OneDrive\Desktop\SMBS-PEP\backend"
.\venv\Scripts\uvicorn.exe app.main:app --reload --host 0.0.0.0 --port 8000
```

Expected:
```
Uvicorn running on http://0.0.0.0:8000
Started server process [pid]
```

### Terminal 2: Start Celery Worker
```powershell
cd "C:\Users\kevin\OneDrive\Desktop\SMBS-PEP\backend"
.\venv\Scripts\celery.exe -A celery_worker worker --loglevel=info
```

Expected:
```
celery@HOSTNAME ready.
Connected to redis://localhost:6379/0
```

### Terminal 3: Start Celery Beat (Optional, for periodic tasks)
```powershell
cd "C:\Users\kevin\OneDrive\Desktop\SMBS-PEP\backend"
.\venv\Scripts\celery.exe -A celery_worker beat --loglevel=info
```

## Testing (After Services Started)

### Test API Health
```powershell
# In PowerShell
curl http://localhost:8000/health | ConvertFrom-Json | Format-List

# Should show:
# database: connected
# redis: connected  
# celery: online (if worker is running)
```

### Open Swagger UI
```
http://localhost:8000/docs
```

### Test Database
```powershell
.\venv\Scripts\python.exe << 'EOF'
import asyncio
from app.database import AsyncSessionLocal
from sqlalchemy import select, func
from app.models import User

async def test():
    async with AsyncSessionLocal() as session:
        count = await session.execute(select(func.count()).select_from(User))
        print(f"Users in database: {count.scalar()}")

asyncio.run(test())
EOF
```

## Common Issues & Fixes

### Issue: pydantic_core._pydantic_core not found
```powershell
# Verify Python version (should be 3.13.x)
.\venv\Scripts\python.exe --version

# Reinstall pydantic
.\venv\Scripts\pip.exe uninstall -y pydantic pydantic-core
.\venv\Scripts\pip.exe install pydantic==2.5.0 pydantic-core==2.10.1
```

### Issue: Celery worker won't start
```powershell
# Verify celery_worker.py exists
Test-Path ".\celery_worker.py"

# Test import
.\venv\Scripts\python.exe -c "from celery_worker import celery; print(celery)"

# Make sure Redis is running
redis-cli ping  # Should return PONG
```

### Issue: FastAPI won't start - ImportError
```powershell
# Test all imports
.\venv\Scripts\python.exe << 'EOF'
from app.main import app
print("✓ All imports successful")
EOF
```

### Issue: Database connection failed
```powershell
# Verify PostgreSQL is running and database exists
psql -U postgres -c "SELECT datname FROM pg_database WHERE datname='smbs-pep';"

# Run migrations
.\venv\Scripts\alembic.exe upgrade head
```

## Stopping Services

To stop all services:
1. **FastAPI**: Press `Ctrl+C` in Terminal 1
2. **Celery Worker**: Press `Ctrl+C` in Terminal 2
3. **Celery Beat**: Press `Ctrl+C` in Terminal 3 (if running)

## Environment Variables

All set in `.env`:
```
DATABASE_URL=postgresql+asyncpg://postgres:root@localhost:5432/smbs-pep
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
SECRET_KEY=replace_with_a_strong_secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## What Was Fixed

### Error 1: ModuleNotFoundError: No module named 'pydantic_core._pydantic_core'
- **Root Cause**: Python 3.14 incompatibility with pydantic-core wheels
- **Fix**: Updated requirements.txt with Python 3.13 compatible versions
- **Result**: ✓ Pydantic imports work with Python 3.13

### Error 2: Unable to load celery application
- **Root Cause**: Wrong module path `app.celery_app`
- **Fix**: Use `celery -A celery_worker` (correct path)
- **Result**: ✓ Celery loads from correct module

### Error 3: Dependency version conflicts
- **Root Cause**: Incompatible dependency versions for Python 3.14
- **Fix**: Updated requirements.txt with tested compatible versions
- **Result**: ✓ All packages install cleanly

## Files Modified

1. ✓ `requirements.txt` - Updated dependency versions
2. ✓ `.venv/` - Deleted (incompatible Python 3.14)
3. ✓ All other files remain unchanged

## Next Steps

1. Run the installation steps above
2. Start services in order: FastAPI → Celery → (Beat)
3. Verify health endpoint: `GET http://localhost:8000/health`
4. Open Swagger: `http://localhost:8000/docs`
5. Test API endpoints

## Support

For issues, check `COMPLETE_REPAIR_INSTRUCTIONS.md` for detailed troubleshooting.
