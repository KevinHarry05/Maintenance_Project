# SBMS Quick Startup - Cheat Sheet

## TL;DR - Start Everything in 60 Seconds

### Prerequisites (One-time setup - 5 minutes)

```bash
# Backend environment
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head

# Frontend dependencies
cd ../frontend
pnpm install  # or: npm install
```

### Start All Services (Every time)

**Terminal 1 - Backend:**
```bash
cd backend
venv\Scripts\activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
pnpm dev  # or: npm run dev
```

**Terminal 3 - Redis (optional, for background tasks):**
```bash
redis-server
```

---

## URLs After Startup

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:3000 | Web application |
| Backend API | http://localhost:8000 | REST API |
| Swagger Docs | http://localhost:8000/docs | Interactive API documentation |
| ReDoc | http://localhost:8000/redoc | Alternative API documentation |

---

## First Time Login

1. Go to **http://localhost:3000**
2. Click **Register**
3. Create account:
   - Email: `student@example.com`
   - Password: `SecurePassword123!` (12+ chars, mixed case, numbers, symbols)
4. **Verify Email** (check output or use admin endpoint)
5. Login and explore!

---

## Environment Files

### Backend `.env` (copy from `.env.example`)

```
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/sbms_db
SECRET_KEY=your-super-secret-key-change-in-production
REDIS_URL=redis://localhost:6379/0
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

### Frontend `.env.local` (optional)

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Common Commands Reference

### Backend

| Command | Purpose |
|---------|---------|
| `venv\Scripts\activate` | Activate Python environment (Windows) |
| `source venv/bin/activate` | Activate Python environment (macOS/Linux) |
| `pip install -r requirements.txt` | Install dependencies |
| `uvicorn app.main:app --reload` | Start dev server |
| `alembic upgrade head` | Apply database migrations |
| `alembic downgrade base` | Revert all migrations |
| `celery -A app.celery_app worker` | Start task worker |
| `deactivate` | Exit Python environment |

### Frontend

| Command | Purpose |
|---------|---------|
| `pnpm install` | Install dependencies |
| `pnpm dev` | Start dev server (watch mode) |
| `pnpm build` | Build for production |
| `pnpm start` | Start production build |
| `pnpm lint` | Run linter |

### Database (PostgreSQL)

| Command | Purpose |
|---------|---------|
| `psql -U postgres` | Connect to PostgreSQL |
| `\l` | List databases |
| `\du` | List users |
| `\dt` | List tables |
| `\q` | Quit psql |

### Redis

| Command | Purpose |
|---------|---------|
| `redis-server` | Start Redis |
| `redis-cli` | Connect to Redis CLI |
| `redis-cli FLUSHALL` | Clear all data |
| `redis-cli PING` | Test connection |

---

## Troubleshooting

### Backend won't start

```bash
# Port already in use?
uvicorn app.main:app --reload --port 8001

# Database won't connect?
# Check: DATABASE_URL in .env is correct
# Verify: PostgreSQL is running
# Test: psql -U postgres -d sbms_db

# Module not found?
# Check: venv is activated
# Verify: pip install -r requirements.txt
```

### Frontend won't start

```bash
# Port already in use?
pnpm dev -- -p 3001

# Dependencies error?
rm -rf node_modules && pnpm install

# API not reachable?
# Check: Backend is running on port 8000
# Verify: CORS config in backend .env
```

### Can't connect to database

```bash
# Start PostgreSQL service
# Windows: net start postgresql-x64-14
# macOS: brew services start postgresql

# Create database if missing
psql -U postgres
CREATE DATABASE sbms_db;
\q
```

### Can't connect to Redis

```bash
# Start Redis
redis-server

# Check connection
redis-cli PING
# Should return: PONG
```

---

## Test the System

### Test Backend Health

```bash
curl http://localhost:8000/health
# Should return: {"success": true, "data": {"status": "ok"}, ...}
```

### Test Frontend Loading

- Open http://localhost:3000 in browser
- Should see login/register page
- Check DevTools Console (F12) for errors

### Test API Authentication

```bash
# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"TestPassword123!"}'

# Should return JWT token
```

### Test Database

```bash
# From backend directory with venv activated
python -c "from app.database import engine; print('✓ DB OK')"
```

---

## Ports Reference

| Service | Port | Note |
|---------|------|------|
| Frontend (Next.js) | 3000 | Web app |
| Backend (FastAPI) | 8000 | REST API |
| PostgreSQL | 5432 | Database |
| Redis | 6379 | Cache/Queue |
| Celery (optional) | 5555 | Monitoring UI |

---

## Stop Everything

```bash
# Terminal 1: Ctrl+C (Backend)
# Terminal 2: Ctrl+C (Frontend)
# Terminal 3: Ctrl+C (Redis)

# Deactivate Python environment
deactivate

# Optional: Kill processes manually
taskkill /F /IM python.exe  # Kill all Python
taskkill /F /IM node.exe    # Kill all Node
```

---

## Common Workflows

### Add a New User

```bash
# Login to admin dashboard at http://localhost:3000
# Click "Admin" → "Users" → "Create User"
# Or use API directly:

curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@example.com",
    "password": "SecurePassword123!",
    "first_name": "John",
    "last_name": "Doe",
    "role": "student"
  }'
```

### Clear Cache

```bash
# Clear Redis cache
redis-cli FLUSHALL

# Clear frontend build cache
rm -rf frontend/.next
```

### Reset Database

```bash
# Option 1: Drop and recreate
alembic downgrade base
alembic upgrade head

# Option 2: Delete data but keep schema
psql -U postgres -d sbms_db -c "TRUNCATE ALL TABLES CASCADE;"
```

### Restart Everything

```bash
# Kill all services
taskkill /F /IM python.exe
taskkill /F /IM node.exe

# Wait 2 seconds
# Start fresh (use Quick Startup section above)
```

---

## Performance Tips

- **Use pnpm** instead of npm (faster)
- **SSD recommended** for disk operations
- **Close unnecessary applications** before starting
- **First build is slower** (5-10s), subsequent are faster (1-2s)
- **Redis improves performance** for rate limiting and caching

---

## Next Steps

1. ✅ Run the quick startup commands above
2. ✅ Access frontend at http://localhost:3000
3. ✅ Create a test account and login
4. ✅ Create a test complaint
5. ✅ Check admin dashboard
6. ✅ Review API docs at http://localhost:8000/docs

---

**Need Help?**

- Read full `STARTUP_GUIDE.md` for detailed troubleshooting
- Check `README.md` for project overview
- Review `IMPLEMENTATION_SUMMARY.md` for features implemented
- Browse API docs: http://localhost:8000/docs

**Version:** 1.0.0 | **Last Updated:** January 2024
