# SBMS Backend Repair - Task Breakdown

## Task Dependency Graph (DAG)

```
Task 1: Diagnose Pydantic Error
    ↓
Task 2: Repair Pydantic Dependencies
    ↓
Task 3: Diagnose Celery Module Error
    ↓
Task 4: Repair Celery Configuration
    ↓
Task 5: Full Backend System Scan
    ↓
Task 6: Dependency Verification & Reconciliation
    ↓
Task 7: Final Verification & Validation
    ↓
Task 8: Generate Final Report
```

## Task Descriptions

### Task 1: Diagnose Pydantic/pydantic-core Import Error

**Dependencies:** None (Initial task)

**Objective:** Identify root cause of ModuleNotFoundError: No module named 'pydantic_core._pydantic_core'

**Subtasks:**

1.1 Check Python Version
- Execute: `python --version`
- Requirement: Python 3.10.x, 3.11.x, or 3.12.x
- Document: Actual version found
- If wrong: Identify path to correct Python installation

1.2 Verify Virtual Environment
- Check: `where python` (Windows) or `which python` (macOS/Linux)
- Requirement: Path contains "venv"
- Document: Actual Python path
- If wrong: Need to activate correct venv or recreate

1.3 List Installed Pydantic Packages
- Execute: `pip list | findstr pydantic` (Windows) or `pip list | grep pydantic` (macOS/Linux)
- Document: All pydantic packages and versions
- Expected: pydantic 2.5.0 and pydantic-core 2.10.1
- If missing: Installation incomplete

1.4 Check pydantic-core Binary Extension
- Execute: `python -c "from pydantic_core import core"`
- Expected: No error output
- If error: Binary extension not found or corrupt
- Check file: `venv/lib/python3.x/site-packages/pydantic_core/_pydantic_core.pyd` (Windows)

1.5 Test Pydantic Import
- Execute: `python -c "import pydantic; print(pydantic.__version__)"`
- Expected: Output: 2.5.0
- If error: Pydantic package not installed or corrupt

1.6 Test FastAPI Import
- Execute: `python -c "import fastapi; print('OK')"`
- Expected: Output: OK
- If error: FastAPI can't import due to pydantic issue

1.7 Document Findings
- Document: Python version, venv status, package versions
- Document: Which imports work and which fail
- Identify: Is it missing package, version mismatch, or binary issue?
- Recommend: Specific action for Task 2


### Task 2: Repair Pydantic Dependencies

**Dependencies:** Task 1 (must complete diagnostics first)

**Objective:** Fix pydantic and pydantic-core installation to enable FastAPI startup

**Subtasks:**

2.1 Prepare Environment
- Navigate to backend directory: `cd backend`
- Verify venv is activated: `where python` shows venv path
- Backup requirements: `pip freeze > requirements_backup.txt`

2.2 Clear Corrupted Installation (if needed)
- If diagnostics show corruption:
  - Deactivate venv: `deactivate`
  - Delete venv: `rmdir /s /q venv` (Windows) or `rm -rf venv` (macOS/Linux)
  - Clear pip cache: `pip cache purge`
  - Recreate venv: `python -m venv venv`
  - Activate venv: `venv\Scripts\activate` (Windows)

2.3 Upgrade pip
- Execute: `python -m pip install --upgrade pip`
- Expected: pip updated to latest version

2.4 Reinstall Pydantic Core
- Execute: `pip install --force-reinstall pydantic-core==2.10.1`
- Expected: Successfully installed pydantic-core
- Action: If Windows and build error, may need Visual C++ build tools

2.5 Reinstall Pydantic
- Execute: `pip install --force-reinstall pydantic==2.5.0`
- Expected: Successfully installed pydantic
- Should pull: pydantic-core 2.10.1 as dependency

2.6 Verify Pydantic Imports
- Execute: `python -c "from pydantic_core import core; print('OK')"`
- Expected: Output OK with no errors
- If error: Issue persists, may need Python reinstall
- Execute: `python -c "import pydantic; print(pydantic.__version__)"`
- Expected: Output 2.5.0

2.7 Reinstall All Requirements
- Execute: `pip install -r requirements.txt`
- Expected: All packages installed successfully
- Duration: 3-5 minutes
- Watch for: Any build errors or warnings

2.8 Verify FastAPI Can Start
- Execute: `uvicorn app.main:app --help`
- Expected: Help output with no import errors
- If error: FastAPI still has issues, debug further
- If success: Proceed to Task 3

2.9 Document Changes
- Document: Any modifications made to requirements.txt
- Document: Any build tools installed
- Document: Final pip list output
- Document: Which procedures were needed (cleanup, reinstall, etc.)


### Task 3: Diagnose Celery Module Not Found Error

**Dependencies:** Task 2 (must have working FastAPI/Pydantic first)

**Objective:** Identify root cause of ModuleNotFoundError: No module named 'app.celery_app'

**Subtasks:**

3.1 Check if celery_app.py Exists
- File path: `backend/app/celery_app.py`
- Command: `dir app\celery_app.py` (Windows) or `ls -la app/celery_app.py` (macOS/Linux)
- Document: File exists or missing
- If missing: Will need to create in Task 4

3.2 Verify Python Path
- Execute: `python -c "import sys; print('\n'.join(sys.path))"`
- Requirement: Current directory and backend/app should be in path
- Document: Actual sys.path output
- Expected: Includes empty string (current dir) and site-packages

3.3 Check app Package Structure
- Check: `dir app/__init__.py` (Windows) or `ls app/__init__.py` (macOS/Linux)
- Document: File exists or missing
- If missing: Need to create (even if empty)

3.4 Verify Working Directory
- Execute: `cd backend && pwd` (macOS/Linux) or `cd backend && echo %cd%` (Windows)
- Requirement: Current directory is backend directory
- Document: Current working directory
- If wrong: All import tests will fail

3.5 Test App Import
- Execute: `python -c "import app; print('app package OK')"`
- Expected: Output OK with no error
- If error: app/__init__.py missing or has errors

3.6 Test Config Import
- Execute: `python -c "from app.config import settings; print('config OK')"`
- Expected: Output OK with no error
- If error: Config has import issues or missing dependencies

3.7 Test Celery Import (Expected to Fail)
- Execute: `python -c "from app.celery_app import celery_app; print('OK')"`
- Expected to fail if file missing
- Document: Exact error message
- If succeeds: celery_app.py already exists
- If fails with ModuleNotFoundError: File missing (expected)

3.8 Check Redis Configuration
- Execute: `python -c "from app.config import settings; print(settings.REDIS_URL)"`
- Expected: Output like redis://localhost:6379/0
- If empty: May need to set in .env or config

3.9 Document Findings
- Document: Which files exist/missing (celery_app.py, app/__init__.py)
- Document: Python path status
- Document: Redis configuration
- Recommend: Specific actions for Task 4


### Task 4: Repair Celery Configuration

**Dependencies:** Task 3 (must have diagnosed the issue first)

**Objective:** Create/fix Celery configuration to enable Celery worker startup

**Subtasks:**

4.1 Create app/__init__.py (if missing)
- Location: `backend/app/__init__.py`
- Action: If file doesn't exist, create empty file or with minimal content:
  ```python
  # App package initialization
  ```
- Verify: `python -c "import app; print('OK')"`

4.2 Create or Fix celery_app.py
- Location: `backend/app/celery_app.py`
- Content: Create Celery application module with correct configuration
- Should include:
  - Import Celery from celery package
  - Load settings from app.config
  - Create celery_app = Celery(...) with broker/backend from settings
  - Configure task serialization to JSON
  - Autodiscover tasks from app.tasks if exists

4.3 Verify Settings Load Correctly
- Execute: `python -c "from app.config import settings; print('REDIS_URL:', settings.REDIS_URL)"`
- Expected: REDIS_URL is set correctly
- If not: Check .env file and update if needed

4.4 Test Celery Import
- Execute: `python -c "from app.celery_app import celery_app; print('celery_app OK')"`
- Expected: Output OK with no error
- If error: Check celery_app.py content

4.5 Verify Redis Configuration
- Check .env for: CELERY_BROKER_URL and CELERY_RESULT_BACKEND
- If missing: Set in .env to match REDIS_URL
- Expected: Both point to redis://localhost:6379/0 (or similar)

4.6 Test Celery Worker Import
- Execute: `python -c "from celery import Celery; print('celery OK')"`
- Expected: Celery package imports successfully

4.7 Verify Celery App Configuration
- Execute in Python:
  ```python
  from app.celery_app import celery_app
  print(f"Broker: {celery_app.conf.broker_connection_retry_on_startup}")
  print(f"Broker URL: {celery_app.conf.get('broker_url')}")
  ```
- Document: Configuration values

4.8 Document Changes
- Document: Files created (celery_app.py, app/__init__.py)
- Document: Configuration values set
- Document: Any modifications to requirements or setup


### Task 5: Full Backend System Scan

**Dependencies:** Task 4 (must have basic infrastructure working)

**Objective:** Comprehensive scan for additional startup errors and configuration issues

**Subtasks:**

5.1 Scan All Router Imports
- Test: `python -c "from app.routes import auth, users, admin, complaints, building, health, websocket_route, notifications"`
- If AI module optional: `python -c "from app.routes import ai"` (may fail if optional)
- Document: Which routers import successfully
- If any fail: Debug that specific route file

5.2 Scan All Model Imports
- Test: `python -c "from app.models import User, Building, Complaint, TicketLog, Notification, TokenBlacklist, EmailVerificationToken"`
- Document: Which models import successfully
- If any fail: Check that model and its dependencies

5.3 Scan All Schema Imports
- Test: `python -c "from app.schemas import auth_schema, building_schema, complaint_schema, notification_schema"`
- Document: Which schemas import successfully
- If any fail: Check schema file for import errors

5.4 Scan All Core Module Imports
- Test: `python -c "from app.core import api_gateway, error_handler, logger, rate_limit, security, permissions, rbac_decorator"`
- Also test: security_headers_middleware, token_blacklist_middleware, login_rate_limiter
- Document: Which core modules import successfully
- If any fail: Check that specific core module

5.5 Scan Database Connectivity
- Execute: Test database connection:
  ```python
  import asyncio
  from app.database import engine
  
  async def test_db():
      try:
          async with engine.connect() as conn:
              result = await conn.execute('SELECT 1')
              print('DB Connection OK')
      except Exception as e:
          print(f'DB Error: {e}')
  
  asyncio.run(test_db())
  ```
- Expected: Output DB Connection OK
- If error: Database not running or connection string wrong

5.6 Scan Redis Connectivity
- Execute:
  ```python
  import redis
  try:
      r = redis.Redis(host='localhost', port=6379, db=0)
      r.ping()
      print('Redis Connection OK')
  except Exception as e:
      print(f'Redis Error: {e}')
  ```
- Expected: Output Redis Connection OK
- If error: Redis not running or configuration wrong

5.7 Scan Pydantic Models Validation
- Test creating instances of major schemas:
  ```python
  from app.schemas.auth_schema import UserSchema
  user = UserSchema(email="test@test.com", full_name="Test User")
  print(f'User schema OK: {user.email}')
  ```
- Test each schema: auth, building, complaint, notification
- Document: Which schemas validate successfully
- If any fail: Schema has pydantic configuration issue

5.8 Scan JWT Configuration
- Execute:
  ```python
  from app.config import settings
  print(f"SECRET_KEY set: {bool(settings.SECRET_KEY)}")
  print(f"ALGORITHM: {settings.ALGORITHM}")
  print(f"ACCESS_TOKEN_EXPIRE: {settings.ACCESS_TOKEN_EXPIRE_MINUTES}")
  ```
- Expected: All values set correctly
- If missing: .env configuration incomplete

5.9 Scan Alembic Migrations
- Execute: `alembic current`
- Expected: Output showing current migration version
- If error: Alembic misconfigured or migrations corrupted

5.10 Scan for Circular Imports
- Execute: `python -c "import app.main; print('Main module OK')"`
- Expected: No circular import errors
- If error: Debug import chain to find circular dependency

5.11 Document All Findings
- Document: Each scan result (pass/fail)
- Document: Any errors encountered
- Document: Recommendations for fixes


### Task 6: Dependency Verification & Reconciliation

**Dependencies:** Task 5 (must have completed system scan first)

**Objective:** Verify all dependencies are compatible and correct, update requirements if needed

**Subtasks:**

6.1 Verify Pydantic Compatibility
- Current: pydantic 2.5.0, pydantic-core 2.10.1
- Execute: `pip list | findstr pydantic`
- Document: All pydantic-related packages and versions
- Verify: Versions match requirements.txt exactly

6.2 Verify FastAPI Compatibility
- Current: fastapi 0.109.2
- Execute: `pip show fastapi`
- Check: Required dependency versions (starlette, pydantic)
- Document: fastapi version and dependencies

6.3 Verify SQLAlchemy Compatibility
- Current: SQLAlchemy 2.0.30, asyncpg 0.31.0
- Execute: `pip show sqlalchemy && pip show asyncpg`
- Verify: Async driver compatibility
- Document: Versions

6.4 Verify Celery Compatibility
- Current: celery 5.6.2, kombu 5.6.2, redis 7.2.1
- Execute: `pip list | findstr -E "celery|kombu|redis"`
- Verify: All celery dependencies present
- Document: Versions

6.5 Check for Dependency Conflicts
- Execute: `pip check`
- Expected: No broken requirements message
- If conflicts: Document conflicting packages
- Action: Resolve by updating requirements.txt if necessary

6.6 Verify Python Version Compatibility
- Execute: `python --version`
- Requirement: 3.10.x, 3.11.x, or 3.12.x
- All packages must support this version
- Document: Python version

6.7 Verify No Duplicate Packages
- Execute: `pip list | sort` and check for duplicates
- If duplicates: Uninstall and reinstall cleanly
- Document: Any duplicates found and resolved

6.8 Check for Deprecated APIs
- Review: Any warnings in FastAPI/Pydantic startup
- Scan: Code for use of deprecated functions
- Document: Any deprecations found

6.9 Update requirements.txt (if needed)
- If changes made: Freeze current requirements
- Execute: `pip freeze > requirements_current.txt`
- Compare: Against current requirements.txt
- Update: If versions differ and are compatible
- Document: Any changes made

6.10 Final Dependency List
- Execute: `pip list > dependency_list.txt`
- Document: Complete list of installed packages
- Archive: For reference


### Task 7: Final Verification & Validation

**Dependencies:** Task 6 (must have resolved all dependency issues)

**Objective:** Complete end-to-end system verification with all components running

**Subtasks:**

7.1 Start FastAPI Server
- Navigate: to backend directory
- Activate: venv if not already
- Execute: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`
- Expected: Server starts with "Uvicorn running on" message
- Document: Any warnings or errors in startup logs
- Keep running: For subsequent tests

7.2 Verify Swagger UI
- Open: http://localhost:8000/docs in browser
- Expected: Swagger UI page loads
- Check: All endpoints visible in API documentation
- Document: Endpoints count and status

7.3 Test Health Endpoint
- Method: GET
- URL: http://localhost:8000/health
- Expected: 200 response with JSON
- Expected JSON: `{"success": true, "data": {"status": "ok"}, "message": "..."`
- Document: Response

7.4 Test Unauthenticated Request
- Method: GET
- URL: http://localhost:8000/buildings
- Expected: 401 Unauthorized (requires auth)
- Document: Response status and headers

7.5 Verify Database Connection
- From Python in venv:
  ```python
  import asyncio
  from app.database import AsyncSessionLocal
  
  async def test():
      async with AsyncSessionLocal() as session:
          from app.models import Building
          result = await session.query(Building).count()
          print(f'Buildings in DB: {result}')
  
  asyncio.run(test())
  ```
- Expected: Query runs successfully, shows count
- Document: Row counts in each table

7.6 Verify Redis Connection
- From Python in venv:
  ```python
  import redis
  r = redis.Redis(host='localhost', port=6379, db=0)
  pong = r.ping()
  print(f'Redis: {pong}')
  
  # Test set/get
  r.set('test_key', 'test_value')
  value = r.get('test_key')
  print(f'Redis value: {value}')
  ```
- Expected: PONG response and value retrieval works
- Document: Redis operational status

7.7 Start Celery Worker
- In separate terminal, activate venv
- Navigate: to backend directory
- Execute: `celery -A app.celery_app worker --loglevel=info`
- Expected: Worker initialization logs and "ready" message
- Document: Worker startup logs
- Keep running: For integration tests

7.8 Verify Celery Broker Connection
- Worker logs should show:
  - Broker connection established
  - Broker type (Redis)
  - Broker URL
  - Number of workers ready
- Document: Worker status

7.9 Test All Routers Load
- From running FastAPI server logs:
  - Verify: All router inclusion messages
  - Expected: No import errors in logs
- From Swagger UI: Verify all endpoints tagged correctly:
  - Authentication endpoints
  - Users endpoints
  - Admin endpoints
  - Complaints endpoints
  - Buildings endpoints
  - Notifications endpoints
  - Health endpoints
- Document: Router count and tags

7.10 Test JWT Authentication (if needed)
- If possible with unauthenticated endpoint:
  - Test: JWT token generation
  - Test: Token validation
  - Document: Auth flow works

7.11 Verify No Startup Warnings
- Review: Both server and worker logs
- Expected: No critical warnings or errors
- Document: Any warnings found (some warnings acceptable)

7.12 Load Test Quick Endpoints
- Test several quick endpoints to verify stability:
  - GET /health
  - GET /docs (redirects)
  - Any public endpoints
- Document: Response times and status

7.13 Final Verification Checklist
- [~] FastAPI server running on port 8000
- [~] Swagger UI accessible and complete
- [~] Health endpoint responds 200
- [~] Database connection works
- [~] Redis connection works
- [~] Celery worker running and ready
- [~] All routers loaded
- [~] No critical errors in logs


### Task 8: Generate Final Report

**Dependencies:** Task 7 (must have completed all verification)

**Objective:** Document all findings, changes, and procedures for future reference

**Deliverables:**

8.1 Root Cause Analysis Document
- Document each error found:
  1. Pydantic/pydantic-core import error
     - Root cause identified
     - Why it occurred
     - How it was fixed
  2. Celery module not found error
     - Root cause identified
     - Why it occurred
     - How it was fixed
  3. Any additional errors found in system scan
     - Each described with root cause and fix

8.2 List of Modified Files
- Files created:
  - app/celery_app.py (if created)
  - app/__init__.py (if created)
- Files modified:
  - requirements.txt (if updated)
  - .env (if updated)
  - Any other modified files
- For each: Document what changed and why

8.3 List of Dependency Changes
- If any packages updated:
  - Old version → New version
  - Reason for change
  - Compatibility verified
- If no changes: Confirm current versions compatible

8.4 Updated requirements.txt
- Provide: Current requirements.txt content
- Document: Any changes from original
- Include: Python version requirement comment
- Include: Notes about critical dependencies (pydantic-core)

8.5 Virtual Environment Recreation Commands
- Provide complete commands to recreate environment:
  ```bash
  # For Windows
  python -m venv venv
  venv\Scripts\activate
  python -m pip install --upgrade pip
  pip install -r requirements.txt
  
  # For macOS/Linux
  python3 -m venv venv
  source venv/bin/activate
  python -m pip install --upgrade pip
  pip install -r requirements.txt
  ```

8.6 Installation & Setup Commands
- Database setup:
  ```bash
  # Migrations
  alembic upgrade head
  ```
- Configuration:
  - .env setup
  - Required environment variables

8.7 Service Startup Commands
- FastAPI:
  ```bash
  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
  ```
- Celery Worker:
  ```bash
  celery -A app.celery_app worker --loglevel=info
  ```
- Redis (if needed):
  ```bash
  redis-server
  ```
- PostgreSQL:
  - Start command for system

8.8 Verification Results Summary
- All Level 1-7 verification checks: Pass/Fail/Warning
- Any failed verifications: Why and how fixed
- System stability: Any concerns noted

8.9 Known Limitations or Issues
- Any unresolved warnings
- Platform-specific issues (Windows/macOS/Linux)
- Optional dependencies not installed (if any)
- Future improvements recommended

8.10 Breaking Changes
- Any changes that affect:
  - API endpoints
  - Configuration
  - Database schema
  - Dependencies versions
- Migration path if applicable

8.11 Testing Recommendations
- Suggested tests to run:
  - Unit test suite (if exists)
  - Integration tests (if exists)
  - Manual API tests
  - Load testing

8.12 Future Maintenance
- Document any special considerations:
  - When updating dependencies
  - When adding new packages
  - Platform-specific setup requirements
  - Performance tuning options

8.13 Support Documentation
- Quick reference for common issues
- Command cheat sheet
- Troubleshooting guide
- Contact information for questions


## Execution Notes

### Prerequisites Before Starting

- [~] Located in correct directory: `c:\Users\kevin\OneDrive\Desktop\SMBS-PEP\backend`
- [~] PostgreSQL server running: Check with `netstat -an | findstr "5432"`
- [~] Redis server running: Check with `netstat -an | findstr "6379"` or `redis-cli ping`
- [~] .env file exists and configured
- [~] Python 3.10+ installed: Verify with `python --version`
- [~] Sufficient disk space for venv and packages (~500MB)

### Task Execution Guidelines

1. **Execute tasks in order** - Dependencies must be completed first
2. **Document everything** - Keep record of findings and changes
3. **Test frequently** - Don't wait until end to discover issues
4. **Stop on errors** - Don't skip errors, diagnose before proceeding
5. **Back up before major changes** - Save requirements.txt before modifications

### Expected Timeline

- Task 1 (Diagnosis): 5 minutes
- Task 2 (Pydantic Repair): 10-15 minutes (includes package installation)
- Task 3 (Celery Diagnosis): 5 minutes
- Task 4 (Celery Repair): 5 minutes
- Task 5 (System Scan): 10 minutes
- Task 6 (Dependency Check): 10 minutes
- Task 7 (Final Verification): 15-20 minutes
- Task 8 (Report): 15 minutes

**Total Estimated Time: 75-100 minutes**

### Risk Assessment

**Low Risk:**
- Diagnostic commands (read-only)
- Import testing
- Log review

**Medium Risk:**
- Dependency reinstallation (reversible)
- .env modifications
- celery_app.py creation (new file)

**No High-Risk Operations:**
- No destructive database operations
- No production systems affected
- All changes reversible

---

**Document Status:** Tasks Complete  
**Last Updated:** Current Session  
**Spec:** SBMS Backend Repair  
**Total Tasks:** 8 Main Tasks with 65+ Subtasks  
**Estimated Execution:** 75-100 minutes
