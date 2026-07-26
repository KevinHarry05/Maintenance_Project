# SBMS Docker Startup Guide

This guide provides instructions for running the entire SBMS application stack using Docker and Docker Compose.

## Prerequisites

### Required Software

1. **Docker Desktop**
   - Download: https://www.docker.com/products/docker-desktop
   - Verify: `docker --version`
   - Verify: `docker-compose --version`

2. **Git** (optional, for cloning repository)
   - Download: https://git-scm.com/

### System Requirements

- **RAM**: 4GB minimum (8GB recommended)
- **Disk Space**: 2GB available
- **CPU**: Dual-core processor
- **OS**: Windows 10/11, macOS 12+, or Linux (Ubuntu 20.04+)

### Enable Docker on Windows

If using Windows, enable one of:
- **Docker Desktop with WSL 2** (recommended)
- **Hyper-V** backend

**PowerShell (as Administrator):**
```powershell
# Enable WSL 2
wsl --install
wsl --set-default-version 2

# Enable Hyper-V
Enable-WindowsOptionalFeature -Online -FeatureName Hyper-V -All
```

---

## Quick Docker Startup (30 seconds)

### 1. Start All Services

```bash
# Navigate to project root
cd c:\Users\kevin\OneDrive\Desktop\SMBS-PEP

# Start all containers
docker-compose -f docker-compose-dev.yml up -d
```

**Expected output:**
```
Creating sbms-postgres ... done
Creating sbms-redis ... done
Creating sbms-backend ... done
Creating sbms-frontend ... done
Creating sbms-celery ... done
```

### 2. Wait for Services to Be Ready

```bash
# Check service status
docker-compose -f docker-compose-dev.yml ps

# Should show all containers as "Up"
NAME                COMMAND                  STATUS
sbms-postgres       "docker-entrypoint.s…"   Up (healthy)
sbms-redis          "redis-server..."        Up (healthy)
sbms-backend        "uvicorn app.main:app"   Up (healthy)
sbms-frontend       "npm run dev"            Up
sbms-celery         "celery -A app.celery"   Up
```

### 3. Access Services

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:3000 | Web application |
| Backend API | http://localhost:8000 | REST API |
| Swagger Docs | http://localhost:8000/docs | API documentation |

---

## Detailed Setup Instructions

### Step 1: Verify Docker Installation

```bash
# Check Docker version
docker --version
# Expected: Docker version 24.x.x or higher

# Check Docker Compose version
docker-compose --version
# Expected: Docker Compose version 2.x.x or higher

# Test Docker is working
docker run hello-world
# Should output: "Hello from Docker!"
```

### Step 2: Navigate to Project Directory

```bash
cd c:\Users\kevin\OneDrive\Desktop\SMBS-PEP
```

### Step 3: Create Environment File (Optional)

Create `.env` in project root for sensitive variables:

```bash
# .env
SECRET_KEY=your-super-secret-key-change-in-production
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-specific-password
```

**Note:** Most variables are pre-configured in `docker-compose-dev.yml`

### Step 4: Build Docker Images (if needed)

```bash
# Build custom images
docker-compose -f docker-compose-dev.yml build

# Or rebuild with no cache
docker-compose -f docker-compose-dev.yml build --no-cache
```

### Step 5: Start All Services

```bash
# Start all containers in background
docker-compose -f docker-compose-dev.yml up -d

# Or start with logs visible
docker-compose -f docker-compose-dev.yml up
# Press Ctrl+C to stop and view logs, services keep running in background
```

### Step 6: Monitor Services

```bash
# View logs from all services
docker-compose -f docker-compose-dev.yml logs -f

# View logs from specific service
docker-compose -f docker-compose-dev.yml logs -f backend
docker-compose -f docker-compose-dev.yml logs -f frontend
docker-compose -f docker-compose-dev.yml logs -f postgres

# View last 50 lines
docker-compose -f docker-compose-dev.yml logs --tail=50

# View logs without following
docker-compose -f docker-compose-dev.yml logs
```

### Step 7: Verify Services Are Running

```bash
# Check container status
docker-compose -f docker-compose-dev.yml ps

# Test backend health
curl http://localhost:8000/health

# Expected response:
# {"success": true, "data": {"status": "ok"}, ...}

# Test frontend access
# Open browser: http://localhost:3000
```

---

## Common Docker Commands

### Container Management

```bash
# Start services
docker-compose -f docker-compose-dev.yml up -d

# Stop services (containers persist)
docker-compose -f docker-compose-dev.yml stop

# Start stopped services
docker-compose -f docker-compose-dev.yml start

# Remove containers (keeps volumes)
docker-compose -f docker-compose-dev.yml down

# Remove containers, volumes, and networks
docker-compose -f docker-compose-dev.yml down -v

# Restart services
docker-compose -f docker-compose-dev.yml restart

# Restart specific service
docker-compose -f docker-compose-dev.yml restart backend
```

### Logs & Monitoring

```bash
# View all logs with timestamps
docker-compose -f docker-compose-dev.yml logs -t

# Follow logs in real-time
docker-compose -f docker-compose-dev.yml logs -f

# Show last 100 lines
docker-compose -f docker-compose-dev.yml logs --tail=100

# Clear log history
docker-compose -f docker-compose-dev.yml logs --clear
```

### Database Access

```bash
# Connect to PostgreSQL
docker-compose -f docker-compose-dev.yml exec postgres psql -U sbms_user -d sbms_db

# Common psql commands
\l          # List databases
\dt         # List tables
\du         # List users
SELECT * FROM users;  # Query users
\q          # Quit
```

### Redis Access

```bash
# Connect to Redis CLI
docker-compose -f docker-compose-dev.yml exec redis redis-cli

# Check all keys
KEYS *

# Get specific key
GET key_name

# Clear all data
FLUSHALL

# Check Redis info
INFO
```

### Shell Access

```bash
# Access backend shell
docker-compose -f docker-compose-dev.yml exec backend sh

# Access frontend shell
docker-compose -f docker-compose-dev.yml exec frontend sh

# Access PostgreSQL container shell
docker-compose -f docker-compose-dev.yml exec postgres sh
```

---

## Troubleshooting

### Container Won't Start

```bash
# Check detailed error logs
docker-compose -f docker-compose-dev.yml logs backend

# Check container status
docker-compose -f docker-compose-dev.yml ps

# Try rebuilding images
docker-compose -f docker-compose-dev.yml down
docker-compose -f docker-compose-dev.yml build --no-cache
docker-compose -f docker-compose-dev.yml up -d
```

### Port Already in Use

```bash
# Find process using port
netstat -ano | findstr :8000  # Backend
netstat -ano | findstr :3000  # Frontend
netstat -ano | findstr :5432  # Database
netstat -ano | findstr :6379  # Redis

# Kill process (replace PID)
taskkill /PID <PID> /F

# Or modify docker-compose ports
# Change "8000:8000" to "8001:8000" in docker-compose-dev.yml
```

### Database Connection Error

```bash
# Check PostgreSQL logs
docker-compose -f docker-compose-dev.yml logs postgres

# Verify database exists
docker-compose -f docker-compose-dev.yml exec postgres psql -U sbms_user -l

# Reset database
docker-compose -f docker-compose-dev.yml down -v
docker-compose -f docker-compose-dev.yml up -d
```

### Redis Connection Error

```bash
# Check Redis is running
docker-compose -f docker-compose-dev.yml ps redis

# Test Redis connection
docker-compose -f docker-compose-dev.yml exec redis redis-cli ping
# Should return: PONG

# Check Redis logs
docker-compose -f docker-compose-dev.yml logs redis
```

### Frontend Not Loading

```bash
# Check frontend is running
docker-compose -f docker-compose-dev.yml ps frontend

# Check frontend logs for build errors
docker-compose -f docker-compose-dev.yml logs frontend

# Verify port mapping
docker-compose -f docker-compose-dev.yml port frontend 3000

# Try rebuilding frontend
docker-compose -f docker-compose-dev.yml down
docker-compose -f docker-compose-dev.yml up -d --build frontend
```

### Backend Not Responding

```bash
# Check backend logs
docker-compose -f docker-compose-dev.yml logs backend

# Check if migrations completed
docker-compose -f docker-compose-dev.yml logs backend | grep "upgrade"

# Manually run migrations
docker-compose -f docker-compose-dev.yml exec backend alembic upgrade head

# Check health endpoint
curl -v http://localhost:8000/health
```

### Out of Disk Space

```bash
# Clean up unused Docker resources
docker system prune -a

# Remove unused volumes (CAUTION: deletes data)
docker volume prune

# Check Docker disk usage
docker system df
```

### Memory Issues

```bash
# Check Docker resource usage
docker stats

# Increase Docker memory allocation:
# Docker Desktop Settings → Resources → Memory: increase to 4GB+
```

---

## Data Persistence

### Volumes

All data is persisted in Docker named volumes:

```bash
# List volumes
docker volume ls

# Inspect volume
docker volume inspect sbms-postgres

# Backup volume data
docker run --rm -v sbms-postgres:/data -v $(pwd):/backup \
  alpine tar czf /backup/postgres-backup.tar.gz -C /data .

# Restore volume data
docker run --rm -v sbms-postgres:/data -v $(pwd):/backup \
  alpine tar xzf /backup/postgres-backup.tar.gz -C /data
```

### Backup & Restore

```bash
# Backup PostgreSQL database
docker-compose -f docker-compose-dev.yml exec postgres \
  pg_dump -U sbms_user sbms_db > backup.sql

# Restore PostgreSQL database
docker-compose -f docker-compose-dev.yml exec postgres \
  psql -U sbms_user sbms_db < backup.sql

# Backup Redis data
docker cp sbms-redis:/data/dump.rdb ./redis-backup.rdb

# Restore Redis data
docker cp ./redis-backup.rdb sbms-redis:/data/dump.rdb
docker-compose -f docker-compose-dev.yml restart redis
```

---

## Environment Configuration

### Pre-configured Variables

The `docker-compose-dev.yml` includes defaults for:

- **Database**: PostgreSQL 15 with user `sbms_user`, password `sbms_password`
- **Redis**: Port 6379 with persistence enabled
- **Backend**: FastAPI on port 8000 with auto-reload
- **Frontend**: Next.js on port 3000 with hot reload
- **CORS**: Allows localhost:3000 and frontend service name
- **Rate Limiting**: Enabled for security
- **Email Verification**: Enabled
- **File Upload**: Max 10MB

### Override Variables

Edit `.env` file for custom values:

```bash
# .env
SECRET_KEY=custom-secret-key
SMTP_USERNAME=custom-email@gmail.com
SMTP_PASSWORD=custom-password
```

Then start with environment file:

```bash
docker-compose -f docker-compose-dev.yml --env-file .env up -d
```

---

## Production Considerations

**This Docker Compose setup is for development only.**

For production, consider:

1. **Use managed services** (AWS RDS for database, ElastiCache for Redis)
2. **Use Docker registries** (DockerHub, AWS ECR)
3. **Use orchestration** (Kubernetes, Docker Swarm)
4. **Configure SSL/TLS** certificates
5. **Set proper resource limits**
6. **Enable logging drivers** (CloudWatch, ELK)
7. **Set up monitoring** (Prometheus, Datadog)
8. **Configure backups** (daily snapshots)
9. **Use environment-specific configs**
10. **Set up CI/CD pipeline** (GitHub Actions, GitLab CI)

---

## Performance Tips

- **Use SSD** for Docker volumes
- **Allocate 4GB+ RAM** to Docker
- **Close unused applications** to free memory
- **Use `.dockerignore`** to reduce image size
- **Cache layers** in Dockerfile (leverage Docker caching)
- **Monitor with `docker stats`** during development

---

## Docker File Structure

### docker-compose-dev.yml Services

| Service | Image | Purpose | Port |
|---------|-------|---------|------|
| postgres | postgres:15-alpine | Database | 5432 |
| redis | redis:7-alpine | Cache/Queue | 6379 |
| backend | Built from ./backend/Dockerfile | FastAPI API | 8000 |
| frontend | node:18-alpine | Next.js Web | 3000 |
| celery-worker | Built from ./backend/Dockerfile | Background Tasks | - |

### Volumes

| Volume | Purpose |
|--------|---------|
| postgres_data | PostgreSQL database files |
| redis_data | Redis database and AOF file |
| backend_uploads | Uploaded complaint files |

### Networks

All services communicate via `sbms-network` bridge network.

---

## Stop & Cleanup

### Stop Services (Keep Data)

```bash
docker-compose -f docker-compose-dev.yml stop
```

### Remove Services (Keep Data & Volumes)

```bash
docker-compose -f docker-compose-dev.yml down
```

### Remove Everything (Delete All Data!)

```bash
# WARNING: This deletes all data!
docker-compose -f docker-compose-dev.yml down -v
```

### Remove Unused Resources

```bash
# Remove dangling images and containers
docker system prune

# Remove unused volumes
docker volume prune
```

---

## Useful Shortcuts

```bash
# View real-time resource usage
docker stats

# See container file system changes
docker diff sbms-backend

# Export container as image
docker commit sbms-backend sbms-backup

# View container processes
docker top sbms-backend

# Inspect service configuration
docker-compose -f docker-compose-dev.yml config
```

---

## Integration with Development Workflow

### Code Changes in Development

Both frontend and backend have auto-reload:

- **Backend**: Changes to Python files trigger uvicorn reload
- **Frontend**: Changes to Next.js files trigger hot reload

No container restart needed—just refresh the browser.

### Running Tests

```bash
# Backend tests
docker-compose -f docker-compose-dev.yml exec backend pytest

# Frontend tests
docker-compose -f docker-compose-dev.yml exec frontend npm test
```

### Running Migrations

```bash
# Apply pending migrations
docker-compose -f docker-compose-dev.yml exec backend alembic upgrade head

# View migration history
docker-compose -f docker-compose-dev.yml exec backend alembic history

# Downgrade to specific revision
docker-compose -f docker-compose-dev.yml exec backend alembic downgrade -1
```

---

## Next Steps

1. ✅ Install Docker Desktop
2. ✅ Run `docker-compose -f docker-compose-dev.yml up -d`
3. ✅ Access http://localhost:3000
4. ✅ Create test account
5. ✅ Review logs with `docker-compose -f docker-compose-dev.yml logs -f`
6. ✅ Explore API at http://localhost:8000/docs

---

**Need Help?**

- Docker docs: https://docs.docker.com/
- Docker Compose docs: https://docs.docker.com/compose/
- FastAPI docs: https://fastapi.tiangolo.com/
- Next.js docs: https://nextjs.org/docs

**Version:** 1.0.0 | **Last Updated:** January 2024
