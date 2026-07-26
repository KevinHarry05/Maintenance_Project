# Backend Startup Verification Checklist

Use this checklist to verify everything is working after repair.

## Pre-Startup Requirements

- [ ] PostgreSQL running on localhost:5432
- [ ] Redis running on localhost:6379
- [ ] Backend directory: `C:\Users\kevin\OneDrive\Desktop\SMBS-PEP\backend`
- [ ] `.venv` directory deleted (Python 3.14 incompatible)
- [ ] `venv` directory exists with Python 3.13
- [ ] `requirements.txt` updated with new versions

## Installation Verification

### 1. Python Version Check
```powershell
cd "C:\Users\kevin\OneDrive\Desktop\SMBS-PEP\backend"
.\venv\Scripts\python.exe --version
```
- [ ] Should output: `Python 3.13.x` (NOT 3.14.x)
- [ ] If wrong version, delete venv and create new one with Python 3.13

### 2. Pip Version
```powershell
.\venv\Scripts\pip.exe --version
```
- [ ] Should show pip version
- [ ] If error, run: `.\venv\Scripts\python.exe -m pip install --upgrade pip`

### 3. Key Package Versions
```powershell
.\venv\Scripts\pip.exe show pydantic fastapi starlette
```
- [ ] pydantic: 2.5.0
- [ ] fastapi: 0.109.2
- [ ] starlette: 0.37.0

## Import Verification

### 4. FastAPI Import Test
```powershell
.\venv\Scripts\python.exe << 'EOF'
from fastapi import FastAPI
print("✓ FastAPI imports successfully")
EOF
```
- [ ] Should print: `✓ FastAPI imports successfully`

### 5. Pydantic Core Import Test
```powershell
.\venv\Scripts\python.exe << 'EOF'
import pydantic_core
print("✓ pydantic_core imports successfully")
EOF
```
- [ ] Should print: `✓ pydantic_core imports successfully`
- [ ] If error "No module named 'pydantic_core._pydantic_core'", reinstall pydantic

### 6. Celery Import Test
```powershell
.\venv\Scripts\python.exe << 'EOF'
from celery_worker import celery
print(f"✓ Celery loaded: {celery}")
EOF
```
- [ ] Should print: `✓ Celery loaded: <Celery ...>`
- [ ] File location: `backend/celery_worker.py` (should exist)

### 7. App Module Import Test
```powershell
.\venv\Scripts\python.exe << 'EOF'
from app.main import app
print("✓ app.main imports successfully")
print(f"✓ FastAPI app: {app.title}")
EOF
```
- [ ] Should print app title: "SBMS Backend"

### 8. Model Imports Test
```powershell
.\venv\Scripts\python.exe << 'EOF'
from app.models import (
    User, Building, Complaint, 
    TokenBlacklist, EmailVerificationToken
)
print("✓ All models import successfully")
EOF
```
- [ ] Should print: `✓ All models import successfully`

### 9. Tasks Import Test
```powershell
.\venv\Scripts\python.exe << 'EOF'
from app.tasks.notification_tasks import send_notification_task
from app.tasks.ai_tasks import calculate_priority_task
print("✓ All Celery tasks import successfully")
EOF
```
- [ ] Should print: `✓ All Celery tasks import successfully`

## Database Verification

### 10. Database Connection Test
```powershell
.\venv\Scripts\python.exe << 'EOF'
import asyncio
from app.database import AsyncSessionLocal

async def test_db():
    try:
        async with AsyncSessionLocal() as session:
            print("✓ Database connection successful")
    except Exception as e:
        print(f"✗ Database connection failed: {e}")

asyncio.run(test_db())
EOF
```
- [ ] Should print: `✓ Database connection successful`
- [ ] If failed, check PostgreSQL running and DATABASE_URL in .env

### 11. Database Migrations Check
```powershell
.\venv\Scripts\alembic.exe current
```
- [ ] Should show migration revision (not empty)
- [ ] If empty, run: `.\venv\Scripts\alembic.exe upgrade head`

### 12. Run Migrations
```powershell
.\venv\Scripts\alembic.exe upgrade head
```
- [ ] Should show: "Running upgrade..."
- [ ] Should complete without errors
- [ ] If already up to date, shows: "INFO: already at head"

## Redis Verification

### 13. Redis Connection Test
```powershell
.\venv\Scripts\python.exe << 'EOF'
import redis
from app.config import settings

try:
    redis_client = redis.from_url(settings.REDIS_URL)
    result = redis_client.ping()
    print(f"✓ Redis connection successful: {result}")
except Exception as e:
    print(f"✗ Redis connection failed: {e}")
EOF
```
- [ ] Should print: `✓ Redis connection successful: True`
- [ ] If failed, check Redis is running: `redis-cli ping`

## Service Startup Verification

### 14. Start FastAPI (Terminal 1)
```powershell
cd "C:\Users\kevin\OneDrive\Desktop\SMBS-PEP\backend"
.\venv\Scripts\uvicorn.exe app.main:app --reload --host 0.0.0.0 --port 8000
```

Expected output:
```
INFO:     Will watch for changes in these directories: ['...']
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started server process [pid]
```

- [ ] Server starts without errors
- [ ] Port 8000 is listening
- [ ] No pydantic errors
- [ ] No import errors
- [ ] No startup warnings

### 15. Test FastAPI Health Endpoint
```powershell
# In new PowerShell window
curl http://localhost:8000/health | ConvertFrom-Json | Format-List
```

Expected:
```
success       : True
message       : Healthy
data          : {database: connected, redis: connected, celery: skipped, timestamp: ...}
```

- [ ] Response code: 200
- [ ] database: connected
- [ ] redis: connected
- [ ] celery: skipped (until worker starts)

### 16. Test FastAPI Root Endpoint
```powershell
curl http://localhost:8000/ | ConvertFrom-Json
```

Expected:
```
message : Smart Building Management API
```

- [ ] Response code: 200
- [ ] Message is correct

### 17. Swagger UI Verification
```
Open browser: http://localhost:8000/docs
```

- [ ] Page loads
- [ ] Swagger UI visible
- [ ] All endpoints listed
- [ ] No JavaScript errors in console

### 18. Start Celery Worker (Terminal 2)
```powershell
cd "C:\Users\kevin\OneDrive\Desktop\SMBS-PEP\backend"
.\venv\Scripts\celery.exe -A celery_worker worker --loglevel=info
```

Expected output:
```
celery@HOSTNAME v5.6.2 (opalescent)
... Connected to redis://localhost:6379/0
celery@HOSTNAME ready.
```

- [ ] Worker starts without errors
- [ ] Connected to Redis broker
- [ ] Shows "ready" status
- [ ] No import errors
- [ ] Correct module: celery_worker (NOT app.celery_app)

### 19. Verify Celery Worker is Processing
```powershell
# Back in FastAPI terminal, check logs for Celery task handling
# Or run a test task and check worker terminal for processing
```

- [ ] Worker receives tasks
- [ ] No task import errors
- [ ] Can process notification tasks
- [ ] Can process AI tasks

### 20. Start Celery Beat (Terminal 3) - Optional
```powershell
cd "C:\Users\kevin\OneDrive\Desktop\SMBS-PEP\backend"
.\venv\Scripts\celery.exe -A celery_worker beat --loglevel=info
```

Expected:
```
celery beat v5.6.2 is starting.
LocalTime -> 2024-... ...
```

- [ ] Beat starts successfully (if desired)
- [ ] Schedules show in output
- [ ] No errors

## API Endpoint Verification

### 21. Test Auth Endpoint
```powershell
$body = @{
    email = "test@example.com"
    password = "TestPassword123!"
} | ConvertTo-Json

curl -X POST http://localhost:8000/auth/login `
     -H "Content-Type: application/json" `
     -d $body | ConvertFrom-Json
```

- [ ] Endpoint responds (200 or 401, not 500)
- [ ] No import errors
- [ ] Error message is descriptive

### 22. Test Buildings Endpoint
```powershell
curl http://localhost:8000/buildings | ConvertFrom-Json
```

- [ ] Endpoint responds
- [ ] Returns list or empty array
- [ ] No 500 errors

### 23. Test Health Check from Swagger
```
1. Open http://localhost:8000/docs
2. Find GET /health endpoint
3. Click "Try it out"
4. Click "Execute"
```

- [ ] Response code: 200
- [ ] Response body shows healthy status

## Performance Verification

### 24. FastAPI Response Time
```powershell
Measure-Command {
    curl http://localhost:8000/health | Out-Null
} | Select-Object TotalMilliseconds
```

- [ ] Response time < 100ms
- [ ] Indicates good performance

### 25. Celery Task Processing Time
```powershell
# Send a task and measure completion
# Check in Celery worker terminal for processing time
```

- [ ] Tasks process without delay
- [ ] No backlog of pending tasks

## Error Checking

### 26. Check for Startup Warnings
In FastAPI terminal, look for:
- [ ] No DeprecationWarnings
- [ ] No FutureWarnings
- [ ] No RuntimeWarnings
- [ ] No ImportWarnings

### 27. Check Celery Worker for Errors
In Celery terminal, look for:
- [ ] No ERROR level logs
- [ ] No exception traces
- [ ] No failed task attempts

### 28. Check Application Logs
```powershell
# In FastAPI terminal, make API requests and check logs
curl http://localhost:8000/health
```

- [ ] Logs show request received
- [ ] Logs show response sent
- [ ] No ERROR or CRITICAL logs

## Database State Verification

### 29. Check Database has Tables
```powershell
.\venv\Scripts\python.exe << 'EOF'
import asyncio
from app.database import engine
from sqlalchemy import inspect

async def check():
    async with engine.connect() as conn:
        inspector = inspect(conn)
        tables = inspector.get_table_names()
        print(f"Tables in database: {tables}")

asyncio.run(check())
EOF
```

- [ ] Lists table names (not empty)
- [ ] Contains: users, buildings, complaints, etc.

### 30. Check Migrations are Applied
```powershell
.\venv\Scripts\python.exe << 'EOF'
from sqlalchemy import text
import asyncio
from app.database import engine

async def check():
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT COUNT(*) FROM alembic_version"))
        count = result.scalar()
        print(f"Applied migrations: {count}")

asyncio.run(check())
EOF
```

- [ ] Shows migration count > 0
- [ ] Indicates migrations are applied

## Shutdown Verification

### 31. Stop Services Gracefully
```powershell
# Terminal 1 (FastAPI)
# Press Ctrl+C
# Should see:
#   INFO:     Shutdown complete.

# Terminal 2 (Celery Worker)
# Press Ctrl+C
# Should see:
#   KeyboardInterrupt: Worker shutdown

# Terminal 3 (Celery Beat) if running
# Press Ctrl+C
# Should see:
#   KeyboardInterrupt
```

- [ ] FastAPI stops cleanly
- [ ] Celery worker stops cleanly
- [ ] Beat stops cleanly (if running)
- [ ] No unhandled exceptions

## Final Summary

### All Checks Passed? ✅
If all 31 checks pass:
- ✅ Backend is fully functional
- ✅ Ready for development
- ✅ All services communicating
- ✅ Database connected
- ✅ Redis cache operational
- ✅ Celery tasks available

### Failed Checks?
If any checks fail:
1. Note the check number and error
2. See COMPLETE_REPAIR_INSTRUCTIONS.md for troubleshooting
3. Check specific section for that component

## Shortcuts

**Verify Everything in 5 Minutes:**
```powershell
# Run all critical tests
.\venv\Scripts\python.exe -c "from fastapi import FastAPI; print('✓ FastAPI')"
.\venv\Scripts\python.exe -c "import pydantic_core; print('✓ pydantic-core')"
.\venv\Scripts\python.exe -c "from celery_worker import celery; print('✓ Celery')"
.\venv\Scripts\python.exe -c "from app.main import app; print('✓ app.main')"

# Start FastAPI
.\venv\Scripts\uvicorn.exe app.main:app --reload --host 0.0.0.0 --port 8000
# Then in another terminal:
curl http://localhost:8000/health

# Start Celery Worker (in third terminal)
.\venv\Scripts\celery.exe -A celery_worker worker --loglevel=info
```

If all above complete without errors → ✅ System is working!

---

**Status**: Use this checklist after repair to verify complete functionality
