# SBMS Backend Repair - Design & Strategy

## Overview

This document outlines the comprehensive strategy for diagnosing and repairing the SMBS FastAPI backend. The repair process follows a systematic diagnostic → repair → verification workflow.

## Diagnostic Strategy

### Error 1: Pydantic/pydantic-core Import Error

**Diagnostic Approach:**

1. **Python Version Check**
   - Execute: `python --version`
   - Verify: 3.10.x, 3.11.x, or 3.12.x
   - Issue: pydantic-core has binary wheels only for these versions
   - If different: May need to reinstall Python or create new venv

2. **Current Environment Status**
   - Check venv activation: `where python` should show venv path
   - Check site-packages: `pip show pydantic`
   - Expected output: Version 2.5.0

3. **pydantic-core Binary Status**
   - Execute: `python -c "from pydantic_core import core"`
   - Check file system: Look for `.pyd` (Windows), `.so` (Linux), `.dylib` (macOS)
   - Expected location: `venv/lib/python3.x/site-packages/pydantic_core`
   - Missing: Indicates installation issue

4. **Dependency Chain Verification**
   - Check: `pip list | grep pydantic`
   - Should show:
     - pydantic 2.5.0
     - pydantic-core 2.10.1
     - pydantic-settings 2.1.0
   - If missing: Installation incomplete

5. **Virtual Environment Integrity**
   - Check: `pip list` output
   - Verify: No duplicate packages
   - Verify: All dependencies present
   - If corrupted: May need to recreate venv

**Root Causes by Scenario:**

| Scenario | Cause | Fix |
|----------|-------|-----|
| Python wrong version | venv created with Python 3.9 or 3.13 | Recreate venv with Python 3.10/3.11/3.12 |
| Binary not found | pydantic-core not installed | Reinstall: `pip install --force-reinstall pydantic-core==2.10.1` |
| Binary mismatch | Wrong Python architecture (32-bit vs 64-bit) | Reinstall Python (64-bit recommended) |
| Corrupted venv | Multiple installations or cache issues | Delete venv, recreate from scratch |
| Windows specific | Missing build tools for compilation | Install Visual C++ build tools |

### Error 2: Celery Module Not Found

**Diagnostic Approach:**

1. **Check if celery_app.py Exists**
   - Path: `backend/app/celery_app.py`
   - Status: File missing or present
   - Action: If missing, create based on Celery + FastAPI pattern

2. **Module Path Verification**
   - Execute from backend directory: `python -c "from app.celery_app import celery_app"`
   - Expected: No error, module imports
   - If error: Check __init__.py files

3. **Check __init__.py Files**
   - Required: `backend/app/__init__.py` must exist
   - Must contain: Any required imports for module initialization
   - Issue: If missing, app becomes non-importable package

4. **PYTHONPATH Verification**
   - Execute: `python -c "import sys; print(sys.path)"`
   - Should contain: Current directory, backend directory, site-packages
   - Issue: If backend not in path, relative imports fail

5. **Current Celery Configuration**
   - Check: Does app/config.py load CELERY_BROKER_URL?
   - Check: Is Redis connection string valid?
   - Check: Is CELERY_RESULT_BACKEND configured?

**Root Causes by Scenario:**

| Scenario | Cause | Fix |
|----------|-------|-----|
| File missing | celery_app.py never created | Create celery_app.py in app/ |
| Import path wrong | PYTHONPATH not set correctly | Ensure running from backend dir, or set PYTHONPATH |
| __init__.py missing | app/ not a package | Create app/__init__.py (can be empty) |
| Module structure wrong | celery_app in wrong location | Move to app/ directory |
| Redis not running | Celery can't connect to broker | Start Redis server |

### Error 3: Full Backend System Scan

**Components to Scan:**

1. **Module Import Chain**
   - Trace: app/main.py → all routers → all models → all schemas → all core modules
   - Test: Can each module import without errors?
   - Detect: Any circular imports?

2. **Router Loading**
   - Verify: Each router file imports successfully
   - Verify: Router objects properly defined
   - Verify: Routes registered in main.py

3. **Database Connectivity**
   - Test: SQLAlchemy engine initialization
   - Test: Async connection pool creation
   - Test: Schema creation or migration

4. **Redis Connectivity**
   - Test: redis-py connection
   - Test: Can ping Redis server
   - Test: Can set/get values

5. **Pydantic Models**
   - Test: Each model can be instantiated
   - Test: Validation works correctly
   - Test: Serialization works

6. **Configuration**
   - Test: Settings load from .env
   - Test: All required settings present
   - Test: Settings have correct types

## Dependency Compatibility Matrix

### Core Framework Stack

```
Python 3.10+ 
  ↓
FastAPI 0.109.2 (requires: starlette, pydantic)
  ├─ Starlette 0.37.0 (requires: httpx, anyio)
  ├─ Pydantic 2.5.0 (requires: pydantic-core, typing-extensions)
  │   └─ pydantic-core 2.10.1 (BINARY EXTENSION - CRITICAL)
  └─ pydantic-settings 2.1.0
```

### Database Stack

```
SQLAlchemy 2.0.30
  ├─ asyncpg 0.31.0 (PostgreSQL async driver - Windows needs Visual C++)
  ├─ greenlet 3.3.2 (greenlet support)
  └─ sqlalchemy-utils (optional, for type utilities)
```

### Async Task Queue Stack

```
Celery 5.6.2
  ├─ Redis 7.2.1 (Redis client - requires Redis server 6.2+)
  ├─ kombu 5.6.2 (message passing)
  ├─ billiard 4.2.4 (process pooling)
  └─ vine 5.1.0 (data structures)
```

### Authentication & Security

```
bcrypt 4.1.3 (password hashing)
python-jose 3.5.0 (JWT tokens)
  ├─ cryptography
  ├─ pyasn1
  ├─ rsa
  └─ ecdsa
email-validator 2.3.0 (email validation)
passlib 1.7.4 (password utilities)
```

### API Server

```
Uvicorn 0.27.0 (ASGI server)
  ├─ h11 0.16.0 (HTTP protocol)
  ├─ httptools (optional, for speed)
  └─ uvloop (optional, for speed)
```

### Database Migration

```
Alembic 1.14.0 (migration framework)
  ├─ SQLAlchemy 2.0.30
  ├─ Mako 1.3.10 (SQL templates)
  └─ python-dateutil 2.9.0
```

### Python Version Compatibility

**pydantic-core 2.10.1 availability by Python version:**

| Python Version | pydantic-core Status | Notes |
|----------------|----------------------|-------|
| 3.9 | ❌ Not Available | Too old, no wheels |
| 3.10 | ✅ Available | Wheels: cp310 |
| 3.11 | ✅ Available | Wheels: cp311 |
| 3.12 | ✅ Available | Wheels: cp312 |
| 3.13 | ⚠️ Limited | May require compilation |

**Fix Strategy:** If Python version incompatible, recreate venv with compatible version.

## Step-by-Step Repair Procedures

### Procedure 1: Environment Cleanup

**Purpose:** Remove corrupted installations before reinstalling

**Steps:**

1. Deactivate virtual environment
   ```bash
   deactivate
   ```

2. Backup current requirements (optional)
   ```bash
   pip freeze > requirements_old.txt
   ```

3. Delete virtual environment
   ```bash
   rmdir /s /q venv  # Windows
   rm -rf venv        # macOS/Linux
   ```

4. Verify deletion
   ```bash
   dir venv  # Should show: The system cannot find the path specified
   ```

5. Clear pip cache (optional but recommended)
   ```bash
   pip cache purge
   ```

**Verification:** venv directory no longer exists

### Procedure 2: Virtual Environment Recreation

**Purpose:** Create fresh, clean Python environment

**Steps:**

1. Verify Python version
   ```bash
   python --version
   # Expected: Python 3.10.x, 3.11.x, or 3.12.x
   ```

2. Create virtual environment
   ```bash
   python -m venv venv
   ```

3. Activate virtual environment
   ```bash
   # Windows Command Prompt
   venv\Scripts\activate
   
   # Windows PowerShell
   venv\Scripts\Activate.ps1
   
   # macOS/Linux
   source venv/bin/activate
   ```

4. Verify activation
   ```bash
   # Should show (venv) in prompt
   where python  # Windows - should show venv path
   which python  # macOS/Linux - should show venv path
   ```

**Verification:** Prompt shows (venv) prefix, python points to venv directory

### Procedure 3: Dependency Reinstallation

**Purpose:** Install all dependencies with correct versions

**Steps:**

1. Upgrade pip first
   ```bash
   python -m pip install --upgrade pip
   ```

2. Install requirements
   ```bash
   pip install -r requirements.txt
   ```

3. Verify critical packages
   ```bash
   pip show pydantic
   # Version: 2.5.0
   
   pip show pydantic-core
   # Version: 2.10.1
   
   pip show fastapi
   # Version: 0.109.2
   ```

4. Test imports
   ```bash
   python -c "import pydantic; print(f'pydantic {pydantic.__version__}')"
   python -c "from pydantic_core import core; print('pydantic-core OK')"
   python -c "import fastapi; print('fastapi OK')"
   ```

**Verification:** All packages installed, imports succeed

### Procedure 4: Create celery_app.py

**Purpose:** Create missing Celery application module

**Location:** `backend/app/celery_app.py`

**Content:**

```python
from celery import Celery
from app.config import settings

# Initialize Celery app
celery_app = Celery(
    'app',
    broker=settings.CELERY_BROKER_URL or settings.REDIS_URL,
    backend=settings.CELERY_RESULT_BACKEND or settings.REDIS_URL,
)

# Configuration
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

# Auto-discover tasks from app.tasks module if it exists
celery_app.autodiscover_tasks(['app.tasks'], force=True)
```

**Steps:**

1. Navigate to backend directory
2. Create file: `app/celery_app.py`
3. Add content from template above
4. Verify import: `python -c "from app.celery_app import celery_app"`

**Verification:** File created, import succeeds

### Procedure 5: Verify app/__init__.py

**Purpose:** Ensure app directory is a proper Python package

**Location:** `backend/app/__init__.py`

**Content:**

```python
# App package initialization
```

**Steps:**

1. Check if file exists: `dir app/__init__.py`
2. If missing, create with content: `echo. > app/__init__.py` (Windows) or `touch app/__init__.py` (macOS/Linux)
3. Verify: `python -c "import app; print('app package OK')"`

**Verification:** File exists, app imports as package

### Procedure 6: Database Migration

**Purpose:** Ensure database schema is up-to-date

**Prerequisites:**
- PostgreSQL running on localhost:5432
- Database `sbms_db` exists
- .env contains correct DATABASE_URL

**Steps:**

1. Check current migration status
   ```bash
   alembic current
   ```

2. Show migration history
   ```bash
   alembic history
   ```

3. Run all pending migrations
   ```bash
   alembic upgrade head
   ```

4. Verify tables created
   ```bash
   # Using psql
   psql -U sbms_user -d sbms_db -c "\dt"
   
   # Should show tables:
   # - users
   # - buildings
   # - complaints
   # - notifications
   # - ticket_log
   # - token_blacklist
   # - email_verification_token
   ```

**Verification:** All migrations applied, all tables exist

### Procedure 7: Configuration Validation

**Purpose:** Ensure all required configuration present and correct

**Steps:**

1. Check .env file exists
   ```bash
   cat .env  # macOS/Linux
   type .env  # Windows
   ```

2. Verify required variables
   ```bash
   # Check each of these exists in .env:
   # DATABASE_URL
   # SECRET_KEY
   # ALGORITHM
   # ACCESS_TOKEN_EXPIRE_MINUTES
   # REFRESH_TOKEN_EXPIRE_DAYS
   # REDIS_URL
   # CELERY_BROKER_URL
   # CELERY_RESULT_BACKEND
   # CORS_ALLOWED_ORIGINS
   ```

3. Test configuration loading
   ```bash
   python -c "from app.config import settings; print(f'Secret key set: {bool(settings.SECRET_KEY)}')"
   ```

**Verification:** All required vars set, configuration loads

## Verification Checklist

### Level 1: Import Verification

- [ ] `python -c "import pydantic"` → Success
- [ ] `python -c "from pydantic_core import core"` → Success
- [ ] `python -c "import fastapi"` → Success
- [ ] `python -c "import sqlalchemy"` → Success
- [ ] `python -c "import celery"` → Success
- [ ] `python -c "import redis"` → Success
- [ ] `python -c "import uvicorn"` → Success
- [ ] `python -c "from app.config import settings"` → Success
- [ ] `python -c "from app.celery_app import celery_app"` → Success

### Level 2: Module Structure Verification

- [ ] `python -c "from app import config"` → Success
- [ ] `python -c "from app.database import engine"` → Success
- [ ] `python -c "from app.models import User, Building, Complaint"` → Success
- [ ] `python -c "from app.routes import auth, users, complaints"` → Success
- [ ] `python -c "from app.core.security import create_access_token"` → Success

### Level 3: Server Startup Verification

- [ ] `uvicorn app.main:app --help` → Shows options (no import error)
- [ ] `uvicorn app.main:app --reload` → Server starts, shows "Uvicorn running on"
- [ ] Server remains running for 5+ seconds without crashing
- [ ] No import errors in output
- [ ] No red error messages in startup logs

### Level 4: Health Check Verification

- [ ] Open http://localhost:8000/docs → Swagger UI loads
- [ ] GET http://localhost:8000/health → Returns 200 with JSON response
- [ ] Response contains: `"status": "ok"`
- [ ] All endpoints visible in Swagger UI

### Level 5: Database Verification

- [ ] PostgreSQL running: `netstat -an | findstr 5432`
- [ ] Database exists: `psql -d sbms_db -c "SELECT 1"`
- [ ] Tables exist: `psql -d sbms_db -c "\dt"`
- [ ] Migrations current: `alembic current` returns version
- [ ] Test query: `psql -d sbms_db -c "SELECT COUNT(*) FROM buildings"`

### Level 6: Redis Verification

- [ ] Redis running: `netstat -an | findstr 6379`
- [ ] Ping Redis: `redis-cli ping` → Returns PONG
- [ ] Test set/get: `redis-cli SET test value && redis-cli GET test`
- [ ] Connection from Python: `python -c "import redis; redis.Redis().ping()"`

### Level 7: Celery Worker Verification

- [ ] Start worker: `celery -A app.celery_app worker --loglevel=info`
- [ ] Worker shows startup messages
- [ ] Worker shows "ready" message
- [ ] Worker accepts connections from broker
- [ ] Can see task discovery output

## Full System Verification Procedure

### Pre-Verification Checklist

- [ ] Backend directory is current working directory
- [ ] Virtual environment activated
- [ ] PostgreSQL service running
- [ ] Redis service running
- [ ] .env file configured correctly
- [ ] Port 8000 available (no other process)

### Verification Sequence

1. **Clear Environment** (5 min)
   - [ ] Deactivate venv
   - [ ] Delete venv
   - [ ] Delete __pycache__ directories
   - [ ] Clear pip cache

2. **Setup Fresh Environment** (10 min)
   - [ ] Create venv
   - [ ] Activate venv
   - [ ] Install dependencies
   - [ ] Run migration

3. **Test Imports** (2 min)
   - [ ] Run all Level 1 import tests
   - [ ] Run all Level 2 module tests

4. **Start Server** (2 min)
   - [ ] Start FastAPI with uvicorn
   - [ ] Observe startup logs
   - [ ] Verify no errors

5. **Test Endpoints** (5 min)
   - [ ] Open Swagger UI
   - [ ] Test health endpoint
   - [ ] Test unauthenticated request
   - [ ] Check response format

6. **Database Verification** (3 min)
   - [ ] Query tables
   - [ ] Check migration status
   - [ ] Verify sample data

7. **Redis Verification** (2 min)
   - [ ] Test Redis connection
   - [ ] Test set/get operations

8. **Celery Worker** (3 min)
   - [ ] Start Celery worker
   - [ ] Observe worker startup
   - [ ] Check broker connection

**Total Time:** ~32 minutes for full verification

---

**Document Status:** Design Complete  
**Last Updated:** Current Session  
**Spec:** SBMS Backend Repair
