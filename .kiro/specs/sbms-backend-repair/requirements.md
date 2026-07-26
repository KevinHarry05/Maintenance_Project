# SBMS Backend Repair - Requirements

## Overview

The SMBS FastAPI backend has encountered multiple critical failures after security improvements were implemented. The backend is unable to start due to dependency conflicts and missing module configurations. This document outlines all requirements for diagnosing and repairing the backend to full operational status.

## Error Documentation

### Error 1: Pydantic/pydantic-core Import Error

**Error Message:**
```
ModuleNotFoundError: No module named 'pydantic_core._pydantic_core'
```

**When Occurs:**
- Running: `uvicorn app.main:app --reload`
- During import of FastAPI application

**Root Cause Category:**
- Dependency version mismatch between pydantic and pydantic-core
- Virtual environment corruption or incomplete installation
- Incompatible Python version with installed pydantic-core binary

**Affected Components:**
- FastAPI application startup
- Pydantic model validation system
- All route initialization

### Error 2: Celery Module Not Found

**Error Message:**
```
ModuleNotFoundError: No module named 'app.celery_app'
```

**When Occurs:**
- Running: `celery -A app.celery_app worker --loglevel=info`
- During celery worker startup

**Root Cause Category:**
- celery_app.py does not exist in app directory
- Module path configuration issue
- __init__.py files missing or incorrectly configured
- PYTHONPATH not including backend directory

**Affected Components:**
- Celery worker startup
- Background task processing (email, notifications)
- Asynchronous job queue

### Error 3: Full Backend System Scan Requirements

**Scope:**
- All module imports and dependencies
- Circular import detection
- Router loading verification
- Database connectivity
- Redis connectivity
- Configuration file loading
- Pydantic model validation
- Logging system initialization
- Security middleware initialization
- WebSocket configuration
- JWT token configuration
- Alembic migration status

## Dependency Verification Requirements

### Core Dependencies

#### Python Version
- **Minimum Version:** 3.10
- **Recommended Version:** 3.11.x or 3.12.x
- **Verification:** Check using `python --version`
- **Critical:** pydantic-core binary wheels only available for specific Python versions

#### FastAPI
- **Current Version:** 0.109.2
- **Compatibility Check:** Must work with Pydantic 2.5.0+
- **Verification:** Can import fastapi and FastAPI class
- **Dependency Chain:** FastAPI → Starlette 0.37.0 → pydantic

#### Pydantic
- **Current Version:** 2.5.0
- **Dependency:** pydantic-core 2.10.1 (CRITICAL)
- **Verification:** Import pydantic successfully, check version with `pydantic.__version__`
- **Known Issue:** pydantic-core binary may not be installed correctly
- **Fix Path:** May require wheel file or recompilation

#### pydantic-core
- **Current Version:** 2.10.1
- **Critical:** Binary extension module (_pydantic_core.pyd on Windows)
- **Verification:** `python -c "from pydantic_core import core"`
- **Platform Specific:** .pyd file for Windows, .so for Linux, .dylib for macOS
- **Fix Strategy:** Reinstall with pip or install prebuilt wheel

#### SQLAlchemy
- **Current Version:** 2.0.30
- **Driver:** asyncpg (0.31.0) for async PostgreSQL
- **Verification:** Import sqlalchemy successfully
- **Database Support:** PostgreSQL with asyncpg driver

#### asyncpg
- **Current Version:** 0.31.0
- **Purpose:** Async PostgreSQL driver
- **Verification:** `python -c "import asyncpg"`
- **Windows Note:** Requires Visual C++ build tools

#### Redis Client
- **Current Version:** 7.2.1 (redis-py)
- **Server Version:** Redis 6.2+ required
- **Verification:** `python -c "import redis"` and `redis.Redis().ping()`
- **Connectivity:** Must connect to localhost:6379

#### Celery
- **Current Version:** 5.6.2
- **Broker:** Redis (configured via CELERY_BROKER_URL)
- **Verification:** Import celery successfully, celery worker can start
- **Dependencies:** kombu 5.6.2, vine 5.1.0, billiard 4.2.4

#### Uvicorn
- **Current Version:** 0.27.0
- **Purpose:** ASGI server for FastAPI
- **Verification:** `uvicorn app.main:app --help` works
- **Startup:** Must start without import errors

### Supporting Dependencies

#### Authentication & Security
- **bcrypt:** 4.1.3 (password hashing)
- **python-jose:** 3.5.0 (JWT tokens)
- **email-validator:** 2.3.0 (email validation)
- **passlib:** 1.7.4 (password utilities)
- **ecdsa:** 0.19.1 (cryptographic signatures)
- **rsa:** 4.9.1 (RSA encryption)

#### Database Migrations
- **alembic:** 1.14.0 (database schema management)
- **Mako:** 1.3.10 (SQL template engine)

#### HTTP & Web
- **httpx:** 0.28.1 (async HTTP client)
- **httpcore:** 1.0.9 (HTTP core library)
- **requests:** 2.32.5 (HTTP requests)
- **starlette:** 0.37.0 (ASGI framework base)

#### Data & Science
- **pandas:** 3.0.1 (data processing)
- **numpy:** 2.2.0 (numerical computing)
- **matplotlib:** 3.10.8 (plotting)
- **sympy:** 1.14.0 (symbolic math)
- **scikit-learn:** (pandas dependency, via joblib)

#### Utilities
- **python-dotenv:** 1.2.1 (.env file loading)
- **loguru:** 0.7.3 (advanced logging)
- **pydantic-settings:** 2.1.0 (settings management)
- **slowapi:** 0.1.9 (rate limiting)
- **click:** 8.3.1 (CLI utilities)

## Project Verification Requirements

### FastAPI Server Startup

**Requirement 1: uvicorn app.main:app Starts Successfully**
- No import errors during initialization
- All routers load without issues
- Security middleware initializes
- Error handlers register
- CORS middleware initializes
- Rate limiter initializes
- Server listens on port 8000
- Expected output: `INFO:     Uvicorn running on http://0.0.0.0:8000`

**Requirement 2: Swagger UI Accessible**
- Navigate to http://localhost:8000/docs
- Page loads without 404 or network errors
- All endpoints displayed in OpenAPI schema
- Try-it-out functionality works
- Expected response: Valid HTML with Swagger UI

**Requirement 3: Health Check Endpoint Responds**
- GET http://localhost:8000/health returns 200
- Response JSON: `{"success": true, "data": {"status": "ok"}, "message": "Service is healthy"}`
- Verify health check endpoint exists in routes/health.py

### Database Connectivity

**Requirement 4: Database Connection Works**
- PostgreSQL server running on localhost:5432
- Database `sbms_db` exists
- User can authenticate with credentials from .env
- asyncpg driver can connect
- Connection string from DATABASE_URL is valid
- Async connection pool initializes correctly

**Requirement 5: Database Tables Created**
- Alembic migrations run successfully: `alembic upgrade head`
- All required tables exist:
  - users
  - buildings
  - complaints
  - notifications
  - ticket_log
  - token_blacklist
  - email_verification_token
- All indexes created as per migration scripts
- Sample data (buildings) seeded on startup

**Requirement 6: ORM Models Import Correctly**
- All SQLAlchemy models in app/models/ import successfully
- Pydantic schemas in app/schemas/ validate correctly
- Model relationships defined correctly
- No circular import issues

### Redis Connectivity

**Requirement 7: Redis Connection Works**
- Redis server running on localhost:6379
- Connection string from REDIS_URL is valid
- redis-py client can connect and ping server
- Connection pool initializes correctly
- Expected output: `PONG` response from ping

**Requirement 8: Redis Cache Accessible**
- Can set/get values in Redis
- Token blacklist operations work
- Cache TTL settings apply
- Session data persists correctly

### Celery Worker Startup

**Requirement 9: Celery Worker Starts Successfully**
- Command `celery -A app.celery_app worker --loglevel=info` executes
- Module app.celery_app imports correctly
- Redis broker connection established
- Worker ready message displayed
- Expected output: `celery@HOSTNAME ready.`

**Requirement 10: Celery Tasks Can Be Imported**
- Tasks from app.tasks directory (if exists) import without errors
- Celery decorators (@app.task) work correctly
- Task registry populated with available tasks

### Application Module Structure

**Requirement 11: All Routers Load Successfully**
- app/routes/auth.py loads
- app/routes/users.py loads
- app/routes/admin.py loads
- app/routes/complaints.py loads
- app/routes/building.py loads
- app/routes/health.py loads
- app/routes/websocket_route.py loads
- app/routes/notifications.py loads
- app/routes/ai.py loads (if exists)
- Routers included in main.py properly

**Requirement 12: Core Modules Initialize**
- app/core/api_gateway.py - Request ID and gateway logic
- app/core/error_handler.py - Error handlers register
- app/core/logger.py - Logging initializes
- app/core/rate_limit.py - Rate limiter configures
- app/core/security.py - JWT and security functions
- app/core/permissions.py - Permission checks work
- app/core/rbac_decorator.py - RBAC decorator functions
- app/core/security_headers_middleware.py - Security headers
- app/core/token_blacklist_middleware.py - Token blacklist
- app/core/login_rate_limiter.py - Login rate limiting

**Requirement 13: Dependencies Modules Work**
- app/dependencies/auth_dependency.py - Auth dependency functions
- app/dependencies/role_dependency.py - Role-based dependency functions

### Authentication & Security

**Requirement 14: JWT Configuration Works**
- SECRET_KEY loaded from .env
- ALGORITHM is HS256 or RS256
- ACCESS_TOKEN_EXPIRE_MINUTES set correctly
- REFRESH_TOKEN_EXPIRE_DAYS set correctly
- Token generation and validation work
- Token blacklist functionality works

**Requirement 15: Password Validation Works**
- PASSWORD_MIN_LENGTH enforced (12 characters)
- PASSWORD_COMPLEXITY_REQUIRED enforced
- bcrypt hashing works correctly
- passlib utilities function correctly

**Requirement 16: Email Verification Works**
- EMAIL_VERIFICATION_ENABLED setting loads
- VERIFICATION_TOKEN_EXPIRY_HOURS set correctly
- Email validation with email-validator
- Verification token generation works
- Token expiry enforcement works

### Configuration & Environment

**Requirement 17: Settings Load Correctly**
- .env file loads without errors
- All required settings present
- Settings values are correct type
- Environment variable substitution works
- Pydantic validation of settings succeeds
- settings.cors_origins_list property works

**Requirement 18: Upload Directory Configured**
- COMPLAINT_UPLOAD_DIR setting loads
- Directory exists or gets created
- File upload path is valid
- MAX_UPLOAD_SIZE_MB enforced

### Advanced Features

**Requirement 19: WebSocket Configuration**
- WebSocket routes initialize
- Socket connection handlers work
- Message handling functions correctly

**Requirement 20: Pydantic Models Validate**
- UserSchema models validate correctly
- ComplaintSchema models validate correctly
- BuildingSchema models validate correctly
- NotificationSchema models validate correctly
- Custom validators execute without error

**Requirement 21: Logging Configuration**
- loguru logger initializes
- Log output appears in console
- Log levels respected (DEBUG, INFO, WARNING, ERROR)
- Structured logging works
- Request logging middleware functions

### Compatibility Matrix

**Python × FastAPI × Pydantic × pydantic-core**

| Python | FastAPI | Pydantic | pydantic-core | Status |
|--------|---------|----------|---------------|--------|
| 3.10.x | 0.109.2 | 2.5.0    | 2.10.1        | Current |
| 3.11.x | 0.109.2 | 2.5.0    | 2.10.1        | Current |
| 3.12.x | 0.109.2 | 2.5.0    | 2.10.1        | Current |
| 3.13.x | 0.109.2 | 2.5.0    | 2.10.1        | Untested |

**Key Constraint:** pydantic-core 2.10.1 requires compiled binary extension. Must match Python version exactly (3.10, 3.11, 3.12).

## Items to Check and Verify

### System & Environment

- [ ] Python version is 3.10, 3.11, or 3.12
- [ ] Virtual environment activated and contains Python from correct location
- [ ] PYTHONPATH includes backend directory
- [ ] Working directory is backend directory
- [ ] All environment variables loaded from .env file
- [ ] No conflicting Python installations or virtual environments

### Dependency Installation

- [ ] All packages in requirements.txt installed
- [ ] pip list shows pydantic 2.5.0 and pydantic-core 2.10.1
- [ ] pydantic-core binary extension file exists (.pyd/.so/.dylib)
- [ ] No duplicate packages with different versions
- [ ] No cached wheels causing issues (try pip cache purge)
- [ ] Installation used pip (not conda if venv created with venv)

### Import Verification

- [ ] `python -c "import pydantic"` succeeds
- [ ] `python -c "from pydantic_core import core"` succeeds
- [ ] `python -c "import fastapi"` succeeds
- [ ] `python -c "import sqlalchemy"` succeeds
- [ ] `python -c "import celery"` succeeds
- [ ] `python -c "import redis"` succeeds
- [ ] `python -c "import uvicorn"` succeeds
- [ ] `python -c "from app import config"` succeeds
- [ ] `python -c "from app.database import engine"` succeeds

### Module Structure

- [ ] app/__init__.py exists
- [ ] app/models/__init__.py exists
- [ ] app/routes/__init__.py exists (if exists)
- [ ] app/schemas/__init__.py exists (if exists)
- [ ] app/core/__init__.py exists (if exists)
- [ ] app/dependencies/__init__.py exists (if exists)
- [ ] No __pycache__ corruption (safe to delete)

### Configuration Files

- [ ] backend/.env exists
- [ ] .env contains all required variables
- [ ] DATABASE_URL is valid PostgreSQL connection string
- [ ] SECRET_KEY set (not empty)
- [ ] REDIS_URL set correctly (localhost:6379)
- [ ] CELERY_BROKER_URL set (same as REDIS_URL)
- [ ] CELERY_RESULT_BACKEND set (same as REDIS_URL)

### External Services

- [ ] PostgreSQL running on localhost:5432
- [ ] Database `sbms_db` created
- [ ] Database user can authenticate
- [ ] Redis running on localhost:6379
- [ ] Both services accessible before starting backend

### Celery Configuration

- [ ] app/celery_app.py exists (or celery_app module accessible)
- [ ] Celery app properly configured with broker and backend
- [ ] CELERY_BROKER_URL points to running Redis
- [ ] Task discovery configured
- [ ] app/tasks/ directory exists if tasks defined

### Migration Status

- [ ] alembic.ini exists in backend directory
- [ ] alembic/versions/ directory exists
- [ ] Migrations can be discovered: `alembic current`
- [ ] No pending migrations: `alembic current` == latest version

## Success Criteria

### Phase 1: Diagnostic Success
- Root cause of each error identified and documented
- Dependency compatibility verified
- Module path issues resolved
- Configuration validated

### Phase 2: Repair Success
- FastAPI server starts without errors
- Celery worker starts without errors
- No import errors or warnings
- All routers initialized
- Health check responds

### Phase 3: Full Verification Success
- Database connection established and tested
- Redis connection established and tested
- All models and schemas validate
- Authentication system functional
- All endpoints accessible
- Swagger UI loads and displays all endpoints
- Alembic migrations run successfully
- No startup warnings or errors

### Phase 4: System Integration Success
- Backend and frontend can communicate
- WebSocket connections work
- Background tasks queue properly
- Notifications system functions
- Rate limiting works
- Token blacklist operations work

## Documentation Outputs

### Required Documentation
- Root cause analysis for each error
- List of all modified files
- List of all dependency changes
- Updated requirements.txt with verified versions
- Commands to recreate virtual environment
- Commands to reinstall dependencies
- Commands to start all services
- Verification checklist results
- Any breaking changes documented

### Deliverables
1. requirements.md (this file)
2. design.md (repair approach and strategy)
3. tasks.md (executable tasks in DAG format)
4. Updated requirements.txt (if changes needed)
5. Verification report (after implementation)
6. Final repair summary document

---

**Status:** Requirements Definition Complete  
**Last Updated:** Current Session  
**Spec:** SBMS Backend Repair
