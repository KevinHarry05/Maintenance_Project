# Complete Backend Startup Repair Instructions

## Executive Summary

The backend has 3 critical issues that prevent startup:

1. **Pydantic Core Mismatch** - Python 3.14 venv using packages compiled for Python 3.13
2. **Celery Module Path Error** - Incorrect module path (should be `celery_worker`, not `app.celery_app`)
3. **Dependency Version Incompatibilities** - Some packages have no Python 3.14 wheels

## Step-by-Step Repair Process

### Phase 1: Environment Cleanup and Setup

#### 1.1 Remove Incompatible Virtual Environment
```powershell
# Navigate to backend directory
cd "C:\Users\kevin\OneDrive\Desktop\SMBS-PEP\backend"

# Remove .venv (Python 3.14 - incompatible)
Remove-Item -Recurse -Force ".venv"
```

#### 1.2 Verify Compatible Virtual Environment
The `venv` folder should use Python 3.13. Verify:
```powershell
# Check Python version in venv
.\venv\Scripts\python.exe --version
# Should output: Python 3.13.x (not 3.14.x)
```

### Phase 2: Fix Dependency Incompatibilities

#### 2.1 Update requirements.txt
The requirements.txt has been updated with Python 3.13 compatible versions:
- ✓ pydantic==2.5.0 (downgraded from 2.12.5)
- ✓ pydantic-core==2.10.1 (compatible with 3.13)
- ✓ fastapi==0.109.2 (compatible version)
- ✓ starlette==0.37.0 (matching FastAPI 0.109.2)
- ✓ uvicorn==0.27.0 (compatible)
- ✓ Removed AI/ML packages that cause wheel issues

#### 2.2 Clean Install Dependencies
```powershell
# Uninstall problematic packages
.\venv\Scripts\pip.exe uninstall -y pydantic pydantic-core pydantic-settings

# Upgrade pip first
.\venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel

# Install all dependencies
.\venv\Scripts\pip.exe install -r requirements.txt

# Verify installation
.\venv\Scripts\python.exe -c "from fastapi import FastAPI; print('✓ FastAPI OK')"
.\venv\Scripts\python.exe -c "import pydantic_core; print('✓ pydantic-core OK')"
.\venv\Scripts\python.exe -c "from celery_worker import celery; print('✓ Celery OK')"
```

### Phase 3: Fix Celery Configuration

#### 3.1 Understand Current Celery Setup
Celery is configured in `celery_worker.py` at project root (NOT as app.celery_app):
- **File**: `backend/celery_worker.py`
- **Import Path**: `from celery_worker import celery`
- **Correct Command**: `celery -A celery_worker worker`

#### 3.2 Verify Celery Tasks Are Importable
```powershell
# Test Celery import
.\venv\Scripts\python.exe -c "from celery_worker import celery; print(celery); print('✓ Celery loaded')"

# Test task imports
.\venv\Scripts\python.exe -c "from app.tasks.notification_tasks import send_notification_task; print('✓ Tasks OK')"
```

### Phase 4: Database and Services Setup

#### 4.1 Ensure Redis is Running
```powershell
# Start Redis (in separate terminal or as service)
redis-server

# Test Redis connection
redis-cli ping
# Should return: PONG
```

#### 4.2 Ensure PostgreSQL is Running and Database Exists
```powershell
# Connect to PostgreSQL
psql -U postgres -d postgres

# In psql console, ensure database exists:
CREATE DATABASE "smbs-pep" OWNER postgres;
\l  # List databases to verify

# Exit psql
\q
```

#### 4.3 Run Alembic Migrations
```powershell
# Navigate to backend directory
cd "C:\Users\kevin\OneDrive\Desktop\SMBS-PEP\backend"

# Run migrations
.\venv\Scripts\alembic.exe upgrade head

# Verify migration success (should see "Running upgrade...")
```

### Phase 5: Verify All Imports Work

#### 5.1 Test Import Chain
```powershell
# Test each major component
.\venv\Scripts\python.exe << 'EOF'
print("Testing imports...")
from fastapi import FastAPI
print("✓ FastAPI")
from pydantic import BaseModel
print("✓ Pydantic")
import pydantic_core
print("✓ pydantic-core")
from app.config import settings
print("✓ app.config")
from app.database import engine, AsyncSessionLocal
print("✓ app.database")
from app.models import User, Building, Complaint
print("✓ app.models")
from celery_worker import celery
print("✓ celery_worker")
from app.tasks.notification_tasks import send_notification_task
print("✓ app.tasks")
print("\n✓ All imports successful!")
EOF
```

#### 5.2 Test FastAPI Application Initialization
```powershell
.\venv\Scripts\python.exe << 'EOF'
from app.main import app
from fastapi.testclient import TestClient
print("✓ FastAPI app initialized")
client = TestClient(app)
response = client.get("/")
print(f"✓ GET / returns {response.status_code}: {response.json()}")
print("✓ FastAPI is working!")
EOF
```

### Phase 6: Start Services

#### 6.1 Start FastAPI Server
```powershell
# Terminal 1 - FastAPI
cd "C:\Users\kevin\OneDrive\Desktop\SMBS-PEP\backend"
.\venv\Scripts\uvicorn.exe app.main:app --reload --host 0.0.0.0 --port 8000
```

Expected output:
```
Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
Started reloader process
Started server process
```

#### 6.2 Start Celery Worker
```powershell
# Terminal 2 - Celery Worker
cd "C:\Users\kevin\OneDrive\Desktop\SMBS-PEP\backend"
.\venv\Scripts\celery.exe -A celery_worker worker --loglevel=info
```

Expected output:
```
celery@HOSTNAME ready.
Connected to redis://localhost:6379/0
```

#### 6.3 Start Celery Beat (Optional)
```powershell
# Terminal 3 - Celery Beat (optional, for periodic tasks)
cd "C:\Users\kevin\OneDrive\Desktop\SMBS-PEP\backend"
.\venv\Scripts\celery.exe -A celery_worker beat --loglevel=info
```

### Phase 7: Verification Tests

#### 7.1 Test FastAPI Endpoints
```powershell
# In new terminal, test API
$BASE_URL = "http://localhost:8000"

# Test health endpoint
curl "$BASE_URL/health" | ConvertFrom-Json | Format-List

# Test root endpoint
curl "$BASE_URL/" | ConvertFrom-Json

# Test Swagger documentation
Start-Process "http://localhost:8000/docs"
```

#### 7.2 Verify Database Connection
```powershell
.\venv\Scripts\python.exe << 'EOF'
import asyncio
from app.database import AsyncSessionLocal
from app.models import User
from sqlalchemy import select

async def test_db():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        print(f"✓ Database connected. Found {len(users)} users")

asyncio.run(test_db())
EOF
```

#### 7.3 Verify Redis Connection
```powershell
.\venv\Scripts\python.exe << 'EOF'
import redis
from app.config import settings

redis_client = redis.from_url(settings.REDIS_URL)
ping_result = redis_client.ping()
print(f"✓ Redis connected: {ping_result}")
EOF
```

#### 7.4 Verify Celery Connection
```powershell
.\venv\Scripts\python.exe << 'EOF'
from celery_worker import celery

inspect = celery.control.inspect(timeout=0.5)
if inspect:
    ping_result = inspect.ping()
    if ping_result:
        print(f"✓ Celery workers online: {list(ping_result.keys())}")
    else:
        print("⚠ Celery worker not responding (may not be started)")
else:
    print("⚠ Could not connect to Celery workers")
EOF
```

## Troubleshooting

### Error: "ModuleNotFoundError: No module named 'pydantic_core._pydantic_core'"
**Solution:**
1. Verify Python version: `python --version` should show 3.13.x
2. Reinstall pydantic-core: `pip uninstall pydantic-core && pip install pydantic-core==2.10.1`
3. If still failing, rebuild venv completely (see "Complete Rebuild" below)

### Error: "Unable to load celery application. The module app.celery_app was not found"
**Solution:**
- Command should be: `celery -A celery_worker worker` NOT `celery -A app.celery_app worker`
- Verify `celery_worker.py` exists in project root

### Error: "redis.exceptions.ConnectionError"
**Solution:**
1. Ensure Redis is running: `redis-cli ping` should return PONG
2. Check .env REDIS_URL: should be `redis://localhost:6379/0`
3. Start Redis: `redis-server`

### Error: "could not connect to server"
**Solution:**
1. Verify PostgreSQL is running
2. Verify DATABASE_URL in .env is correct
3. Verify database exists: `psql -U postgres -l | grep smbs-pep`
4. Run migrations: `alembic upgrade head`

## Complete Environment Rebuild (Nuclear Option)

If issues persist:

```powershell
# 1. Remove both venvs
Remove-Item -Recurse -Force ".\venv"
Remove-Item -Recurse -Force ".\.venv"

# 2. Create new venv with Python 3.13
python -m venv venv

# 3. Activate and upgrade pip
.\venv\Scripts\python.exe -m pip install --upgrade pip setuptools wheel

# 4. Install requirements
.\venv\Scripts\pip.exe install -r requirements.txt

# 5. Test
.\venv\Scripts\python.exe -c "from fastapi import FastAPI; print('✓ OK')"
```

## Automated Repair Script

Save as `repair.ps1`:

```powershell
$VenvPath = ".\venv"
$PythonExe = "$VenvPath\Scripts\python.exe"
$PipExe = "$VenvPath\Scripts\pip.exe"

Write-Host "🔧 Backend Repair Script" -ForegroundColor Cyan
Write-Host ""

# Step 1: Remove incompatible .venv
if (Test-Path ".\.venv") {
    Write-Host "🗑️  Removing incompatible .venv..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force ".\.venv"
}

# Step 2: Verify venv
Write-Host "✓ Checking venv..." -ForegroundColor Green
& $PythonExe --version

# Step 3: Clean install
Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
& $PipExe uninstall -y pydantic pydantic-core pydantic-settings
& $PythonExe -m pip install --upgrade pip setuptools wheel
& $PipExe install -r requirements.txt

# Step 4: Test imports
Write-Host "🧪 Testing imports..." -ForegroundColor Yellow
& $PythonExe -c "from fastapi import FastAPI; print('  ✓ FastAPI')"
& $PythonExe -c "import pydantic_core; print('  ✓ pydantic-core')"
& $PythonExe -c "from celery_worker import celery; print('  ✓ Celery')"

Write-Host ""
Write-Host "✅ Repair complete! Ready to start services." -ForegroundColor Green
Write-Host ""
Write-Host "To start services, run in separate terminals:" -ForegroundColor Cyan
Write-Host "  1. uvicorn app.main:app --reload --host 0.0.0.0 --port 8000" -ForegroundColor White
Write-Host "  2. celery -A celery_worker worker --loglevel=info" -ForegroundColor White
Write-Host "  3. celery -A celery_worker beat --loglevel=info (optional)" -ForegroundColor White
```

Run it:
```powershell
.\repair.ps1
```

## Summary of Changes

### Modified Files
1. ✓ `requirements.txt` - Updated with Python 3.13 compatible versions

### Configuration Files (No changes needed, existing configs are correct)
- `celery_worker.py` - Correctly defines Celery
- `app/config.py` - Correctly loads from .env
- `app/main.py` - Correctly imports all modules
- `.env` - Already has correct REDIS_URL and CELERY configuration

### Deleted/Removed
- `.venv` directory (incompatible Python 3.14)

## Key Takeaways

1. **Use Python 3.13** - Remove .venv with Python 3.14
2. **Celery Command** - Use `celery -A celery_worker` not `celery -A app.celery_app`
3. **Updated Requirements** - Use new requirements.txt with compatible versions
4. **Services Order** - Start Redis → FastAPI → Celery Worker → (Celery Beat)

## Support Commands

```powershell
# Check Python version
.\venv\Scripts\python.exe --version

# Check installed packages
.\venv\Scripts\pip.exe list | findstr pydantic

# Run app with diagnostics
.\venv\Scripts\python.exe -c "import app.main; print('App loads successfully')"

# Check database connection
.\venv\Scripts\alembic.exe current

# Check Redis
redis-cli ping

# Check Celery
.\venv\Scripts\celery.exe -A celery_worker inspect active_queues
```
