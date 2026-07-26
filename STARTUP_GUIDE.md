# SMBS Frontend & Backend Startup Guide

This document provides complete instructions for running the Smart Building Management System (SBMS) locally with both frontend and backend.

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Prerequisites](#prerequisites)
3. [Environment Setup](#environment-setup)
4. [Backend Startup](#backend-startup)
5. [Frontend Startup](#frontend-startup)
6. [Startup Verification](#startup-verification)
7. [Troubleshooting](#troubleshooting)
8. [Quick Start Commands](#quick-start-commands)

---

## System Requirements

### Hardware
- **RAM**: Minimum 4GB (8GB+ recommended)
- **Disk Space**: 2GB minimum
- **CPU**: Dual-core processor

### Operating Systems
- Windows 10/11
- macOS 12+
- Linux (Ubuntu 20.04+)

---

## Prerequisites

### Required Software

#### 1. **Python 3.10+**
```bash
# Windows
Download from https://www.python.org/downloads/
# Check installation
python --version
```

#### 2. **Node.js 18+ & npm/pnpm**
```bash
# Windows - Download from https://nodejs.org/
# Or use Chocolatey
choco install nodejs

# Verify installation
node --version
npm --version

# (Optional) Install pnpm for faster builds
npm install -g pnpm
pnpm --version
```

#### 3. **PostgreSQL 14+**
```bash
# Windows - Download from https://www.postgresql.org/download/windows/
# Or use Chocolatey
choco install postgresql

# Verify installation
psql --version
```

#### 4. **Redis 6.2+**
```bash
# Windows - Download from https://github.com/microsoftarchive/redis/releases
# Or use Chocolatey
choco install redis

# Verify installation
redis-cli --version
```

#### 5. **Git** (for version control)
```bash
# Windows - Download from https://git-scm.com/
choco install git

# Verify installation
git --version
```

---

## Environment Setup

### Step 1: Clone or Navigate to Project

```bash
cd c:\Users\kevin\OneDrive\Desktop\SMBS-PEP
```

### Step 2: Backend Environment Configuration

1. **Navigate to backend directory:**
```bash
cd backend
```

2. **Copy the environment template:**
```bash
# Windows
copy .env.example .env
```

3. **Edit `.env` with your configuration:**

```bash
# Database Configuration
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/sbms_db

# Security (generate strong secret)
SECRET_KEY=your-super-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# Redis Configuration (local development)
REDIS_URL=redis://localhost:6379/0

# Celery Configuration
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Frontend CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000

# File Upload
COMPLAINT_UPLOAD_DIR=uploads/complaints
MAX_UPLOAD_SIZE_MB=10

# Rate Limiting
GLOBAL_RATE_LIMIT_PER_MINUTE=200
LOGIN_RATE_LIMIT_PER_MINUTE=5
LOGIN_RATE_LIMIT_WINDOW_SECONDS=60
MAX_LOGIN_ATTEMPTS=5

# Token Blacklist
TOKEN_BLACKLIST_CLEANUP_HOUR=2
TOKEN_BLACKLIST_CACHE_TTL_SECONDS=300

# Email Verification
EMAIL_VERIFICATION_ENABLED=true
VERIFICATION_TOKEN_EXPIRY_HOURS=24
RESEND_EMAIL_RATE_LIMIT=3
RESEND_EMAIL_RATE_LIMIT_WINDOW_MINUTES=60

# Password Validation
PASSWORD_MIN_LENGTH=12
PASSWORD_COMPLEXITY_REQUIRED=true

# Domain
DOMAIN=localhost:8000

# SMTP Configuration (for email notifications)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-specific-password
SMTP_FROM_EMAIL=noreply@sbms.app
SMTP_FROM_NAME=SBMS

# Health Check
ENABLE_CELERY_HEALTH_CHECK=false
```

### Step 3: Create PostgreSQL Database

**Option A: Using psql CLI**

```bash
# Connect to PostgreSQL
psql -U postgres

# In psql prompt, create database and user
CREATE USER sbms_user WITH PASSWORD 'sbms_password';
CREATE DATABASE sbms_db OWNER sbms_user;

# Update .env with:
# DATABASE_URL=postgresql+asyncpg://sbms_user:sbms_password@localhost:5432/sbms_db

\q  # Quit psql
```

**Option B: Using pgAdmin (GUI)**
1. Open pgAdmin
2. Connect to local server
3. Right-click "Databases" → Create → Database
4. Set name to `sbms_db`
5. Create user `sbms_user` with password `sbms_password`

### Step 4: Verify Services Are Running

```bash
# Check PostgreSQL (should see "listening on port 5432")
netstat -an | findstr "5432"

# Check Redis (should see "The server is now ready to accept connections on port 6379")
netstat -an | findstr "6379"

# Or start Redis if not running
redis-server
```

---

## Backend Startup

### Step 1: Create Python Virtual Environment

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows (Command Prompt)
venv\Scripts\activate

# Windows (PowerShell)
venv\Scripts\Activate.ps1

# macOS/Linux
source venv/bin/activate
```

**Expected output after activation:**
```
(venv) C:\Users\kevin\OneDrive\Desktop\SMBS-PEP\backend>
```

### Step 2: Install Python Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install dependencies from requirements.txt
pip install -r requirements.txt
```

**This installs:**
- FastAPI web framework
- SQLAlchemy ORM
- PostgreSQL async driver (asyncpg)
- Redis client
- Celery task queue
- JWT authentication
- Pydantic validation
- And 70+ other packages

**Expected installation time:** 3-5 minutes

### Step 3: Run Database Migrations

```bash
# Navigate to backend directory (if not already there)
cd backend

# Run Alembic migrations (creates tables, indexes, token blacklist storage)
alembic upgrade head
```

**Expected output:**
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl
INFO  [alembic.runtime.migration] Will assume transactional DDL is supported
INFO  [alembic.runtime.migration] Running upgrade -> [version], add_xxxx
...
INFO  [alembic.runtime.migration] Running upgrade [version] -> [version], add_xxxx
```

**Migrations applied:**
- Initial schema (users, buildings, complaints, etc.)
- Token blacklist table (persistent storage)
- Email verification tokens table
- Database indexes for performance
- Notification and workflow fields

### Step 4: Start Redis Server (if not running)

**In a new terminal:**

```bash
# Windows - If installed via Redis project
redis-server

# Or if installed via WSL
wsl redis-server
```

**Expected output:**
```
[2024-01-15 14:30:45] * Ready to accept connections on port 6379
```

### Step 5: Start Backend Server

**Terminal where venv is activated:**

```bash
# Navigate to backend directory
cd backend

# Start FastAPI server with uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started server process [12345]
INFO:     Waiting for applications startup.
INFO:     Application startup complete.
```

**Access points:**
- API: `http://localhost:8000`
- API Documentation: `http://localhost:8000/docs` (Swagger UI)
- Alternative Docs: `http://localhost:8000/redoc` (ReDoc)

### Step 6: (Optional) Start Celery Worker for Background Tasks

**In another new terminal:**

```bash
# Navigate to backend directory
cd backend

# Activate venv if needed
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# Start Celery worker (for async tasks like email, notifications)
celery -A app.celery_app worker --loglevel=info
```

**Expected output:**
```
 -------------- celery@HOSTNAME v5.6.2 (emerald-rush)
--- ***** -----
-- ******* ----
- *** --- * ---
- ** ---------- [config]
- ** ---------- .
- ** ---------- broker:   redis://localhost:6379/0
- ** ---------- app:      app:0x...
- *** --- * --- .
-- ******* ---- [queues]
---  ***** -----
 -------------- celery@HOSTNAME ready.
```

---

## Frontend Startup

### Step 1: Navigate to Frontend Directory

```bash
cd frontend
```

### Step 2: Install Dependencies

**Using pnpm (recommended):**
```bash
pnpm install
```

**Or using npm:**
```bash
npm install
```

**This installs:**
- Next.js 16.1
- React 19
- TypeScript
- TanStack Query (React Query)
- Axios HTTP client
- Radix UI components
- Tailwind CSS
- Form validation libraries
- And 30+ other packages

**Expected installation time:** 2-3 minutes

### Step 3: Configure Frontend Environment (Optional)

If needed, create `.env.local` in frontend directory:

```bash
# Backend API endpoint
NEXT_PUBLIC_API_URL=http://localhost:8000

# Optional: Analytics
NEXT_PUBLIC_ANALYTICS_ID=your-analytics-id
```

### Step 4: Start Frontend Development Server

**Using pnpm:**
```bash
pnpm dev
```

**Or using npm:**
```bash
npm run dev
```

**Expected output:**
```
  ▲ Next.js 16.1.6
  - Local:        http://localhost:3000
  - Environments: .env.local

✓ Ready in 3.2s
```

**Access points:**
- Frontend: `http://localhost:3000`
- Build optimization: `http://localhost:3000/_next/static/...`

---

## Startup Verification

### Verify Backend is Running

**Test 1: Health Check Endpoint**
```bash
curl http://localhost:8000/health
```

**Expected response:**
```json
{
  "success": true,
  "data": {
    "status": "ok",
    "timestamp": "2024-01-15T14:30:45.123Z"
  },
  "message": "Service is healthy"
}
```

**Test 2: Access Swagger UI**
- Open browser: `http://localhost:8000/docs`
- You should see the API documentation with all endpoints

**Test 3: Test Unauthenticated Request**
```bash
curl http://localhost:8000/buildings
```

**Expected response:** Should require authentication (401 Unauthorized)

**Test 4: Test Login Endpoint**
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"TestPassword123!"}'
```

### Verify Frontend is Running

**Test 1: Access Frontend**
- Open browser: `http://localhost:3000`
- You should see the SBMS dashboard/login page

**Test 2: Check Console**
- Open browser DevTools (F12)
- Go to Console tab
- Should see no critical errors (warnings are okay)

### Verify Database Connection

```bash
# From backend directory with venv activated
python -c "
from app.database import engine
import asyncio

async def test_db():
    try:
        async with engine.connect() as conn:
            result = await conn.execute('SELECT 1')
            print('✓ Database connection successful')
    except Exception as e:
        print(f'✗ Database connection failed: {e}')

asyncio.run(test_db())
"
```

### Verify Redis Connection

```bash
# From backend directory with venv activated
python -c "
import redis

try:
    r = redis.Redis(host='localhost', port=6379, db=0)
    r.ping()
    print('✓ Redis connection successful')
except Exception as e:
    print(f'✗ Redis connection failed: {e}')
"
```

---

## Troubleshooting

### Backend Issues

#### Port 8000 Already in Use
```bash
# Find process using port 8000
netstat -ano | findstr :8000

# Kill process (replace PID with the number found)
taskkill /PID <PID> /F

# Or use different port
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

#### Database Connection Error
```
Error: could not translate host name "localhost" to address
```

**Solutions:**
1. Verify PostgreSQL is running: `netstat -an | findstr "5432"`
2. Check DATABASE_URL in .env is correct
3. Verify database and user exist: `psql -U postgres -l`
4. Restart PostgreSQL service

#### Redis Connection Error
```
Error: ConnectionError: cannot connect to Redis
```

**Solutions:**
1. Verify Redis is running: `netstat -an | findstr "6379"`
2. Check REDIS_URL in .env is correct
3. Start Redis: `redis-server`
4. Verify Redis config: `redis-cli config get port`

#### Module Import Errors
```
ModuleNotFoundError: No module named 'app'
```

**Solutions:**
1. Make sure venv is activated
2. Verify you're in backend directory: `pwd` or `cd backend`
3. Reinstall dependencies: `pip install -r requirements.txt`
4. Check PYTHONPATH: `echo $PYTHONPATH`

#### Migration Errors
```
AlembicError: No version identifiers resolved
```

**Solutions:**
1. Verify alembic.ini exists in backend directory
2. Reset migrations: `alembic downgrade base` then `alembic upgrade head`
3. Check database exists and is accessible
4. View migration history: `alembic history`

### Frontend Issues

#### Port 3000 Already in Use
```bash
# Find process using port 3000
netstat -ano | findstr :3000

# Kill process (replace PID)
taskkill /PID <PID> /F

# Or use different port
pnpm dev -- -p 3001
```

#### Dependencies Installation Error
```bash
# Clear node_modules and cache
rm -rf node_modules
rm -rf .next

# Reinstall
pnpm install
# or
npm install
```

#### Backend API Not Reachable
```
Failed to fetch http://localhost:8000/...
```

**Solutions:**
1. Verify backend is running on port 8000
2. Check NEXT_PUBLIC_API_URL in .env.local
3. Check CORS configuration in backend .env
4. Verify firewall isn't blocking port 8000

#### TypeScript Compilation Error
```bash
# Clear Next.js cache and rebuild
rm -rf .next
pnpm build
```

### Common Issues Across Both

#### Port Conflicts
Use different ports:
- Backend: `uvicorn app.main:app --port 8001`
- Frontend: `pnpm dev -- -p 3001`

#### Environment Variables Not Loading
```bash
# Verify .env files exist:
# Backend: backend/.env
# Frontend: frontend/.env.local

# Restart server after changing .env
# Kill existing process and restart
```

#### Slow Startup
- First startup is slower (builds next.js, compiles code)
- Subsequent startups are faster (~1-2 seconds)
- If consistently slow (>30s), check:
  - Disk speed (SSD recommended)
  - RAM available (close other applications)
  - Antivirus scanning (add project to exclusions)

---

## Quick Start Commands

### All-in-One Quick Start (After First Setup)

**Terminal 1 - Backend:**
```bash
cd backend
venv\Scripts\activate  # Windows
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
pnpm dev
```

**Terminal 3 - Redis (if needed):**
```bash
redis-server
```

### Minimal Setup (First Time Only)

```bash
# Backend setup
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head

# Frontend setup
cd ../frontend
pnpm install
# or npm install
```

### Stop All Services

```bash
# Terminal 1: Press Ctrl+C (Backend)
# Terminal 2: Press Ctrl+C (Frontend)
# Terminal 3: Press Ctrl+C (Redis)

# Deactivate venv
deactivate
```

### Rebuild Everything

```bash
# Backend
cd backend
rm -rf venv
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
alembic downgrade base
alembic upgrade head

# Frontend
cd ../frontend
rm -rf node_modules .next pnpm-lock.yaml
pnpm install
pnpm build
```

---

## Environment Variables Reference

### Backend (.env)

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | - | PostgreSQL connection string |
| `SECRET_KEY` | - | JWT secret key |
| `ALGORITHM` | HS256 | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 30 | Access token validity |
| `REFRESH_TOKEN_EXPIRE_DAYS` | 7 | Refresh token validity |
| `REDIS_URL` | redis://localhost:6379/0 | Redis connection |
| `CORS_ALLOWED_ORIGINS` | http://localhost:3000 | CORS allowed origins |
| `MAX_UPLOAD_SIZE_MB` | 10 | File upload limit |
| `LOGIN_RATE_LIMIT_PER_MINUTE` | 5 | Login attempts per minute |
| `PASSWORD_MIN_LENGTH` | 12 | Minimum password length |
| `EMAIL_VERIFICATION_ENABLED` | true | Require email verification |

### Frontend (.env.local)

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | http://localhost:8000 | Backend API endpoint |

---

## API Endpoints Checklist

### Health & Status
- [ ] `GET /health` - Health check
- [ ] `GET /` - Root endpoint

### Authentication
- [ ] `POST /auth/register` - Register new user
- [ ] `POST /auth/login` - Login
- [ ] `POST /auth/refresh` - Refresh token
- [ ] `POST /auth/logout` - Logout
- [ ] `POST /auth/verify-email` - Verify email
- [ ] `POST /auth/resend-verification` - Resend verification

### Buildings
- [ ] `GET /buildings` - List buildings (authenticated)
- [ ] `GET /buildings/{id}` - Get building details (RBAC)
- [ ] `POST /buildings` - Create building (Admin only)
- [ ] `PUT /buildings/{id}` - Update building (Admin only)
- [ ] `DELETE /buildings/{id}` - Delete building (Admin only)

### Complaints
- [ ] `GET /complaints` - List complaints (RBAC filtered)
- [ ] `GET /complaints/{id}` - Get complaint details
- [ ] `POST /complaints` - Create complaint (Student)
- [ ] `PUT /complaints/{id}` - Update complaint
- [ ] `POST /complaints/{id}/assign` - Assign complaint (Admin)
- [ ] `POST /complaints/{id}/resolve` - Resolve complaint (Worker)
- [ ] `POST /complaints/{id}/feedback` - Add feedback (Student)

### Users
- [ ] `GET /users/profile` - Current user profile
- [ ] `PUT /users/profile` - Update profile
- [ ] `POST /users/change-password` - Change password
- [ ] `GET /admin/users` - List users (Admin)

### Notifications
- [ ] `GET /notifications` - Get notifications
- [ ] `GET /notifications/unread-count` - Unread count
- [ ] `PUT /notifications/{id}/read` - Mark as read

---

## Production Deployment Notes

This guide covers local development. For production:

1. Use production database (AWS RDS, etc.)
2. Use production Redis (AWS ElastiCache, etc.)
3. Use production secret keys (generate with `secrets.token_urlsafe()`)
4. Configure proper CORS origins
5. Set up SSL/TLS certificates
6. Use environment-specific configs
7. Enable comprehensive logging
8. Set up monitoring and alerting
9. Configure automated backups
10. Use production SMTP provider

See deployment documentation for detailed instructions.

---

## Support & Documentation

- **API Docs:** `http://localhost:8000/docs`
- **Backend Logs:** Check terminal output
- **Frontend Logs:** Browser DevTools Console
- **Database Logs:** PostgreSQL log file
- **Redis Logs:** Redis terminal output
- **Project Structure:** See `README.md` in project root
- **Spec Documentation:** See `.kiro/specs/sbms-security-hardening/`

---

**Last Updated:** January 2024  
**Version:** 1.0.0
