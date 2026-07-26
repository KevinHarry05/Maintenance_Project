# SBMS Startup Scripts

Quick shortcuts to start the SBMS application without manual terminal commands.

## Available Scripts

### Windows Batch Scripts

#### `start-backend.bat`
Starts the FastAPI backend server with automatic setup.

**Usage:**
```bash
cd backend
start-backend.bat
```

**What it does:**
1. ✓ Checks Python installation
2. ✓ Creates virtual environment (if needed)
3. ✓ Installs dependencies (if needed)
4. ✓ Creates .env file (if needed)
5. ✓ Activates virtual environment
6. ✓ Starts FastAPI server on port 8000

**Troubleshooting:**
- If it fails, read the error message for specifics
- Check that Python 3.10+ is installed
- Check that port 8000 is not in use
- Check that .env is properly configured

---

#### `start-frontend.bat`
Starts the Next.js frontend server with automatic setup.

**Usage:**
```bash
cd frontend
start-frontend.bat
```

**What it does:**
1. ✓ Checks Node.js installation
2. ✓ Installs node_modules (if needed)
3. ✓ Starts Next.js dev server on port 3000

**Troubleshooting:**
- If it fails, read the error message for specifics
- Check that Node.js 18+ is installed
- Check that port 3000 is not in use
- Delete node_modules and try again if npm install fails

---

### PowerShell Script

#### `start-services.ps1`
Advanced startup script that can start multiple services.

**Usage:**
```powershell
# Start everything
.\start-services.ps1

# Start only backend
.\start-services.ps1 -Backend

# Start only frontend
.\start-services.ps1 -Frontend

# Start only Redis
.\start-services.ps1 -Redis

# Start backend and frontend
.\start-services.ps1 -Backend -Frontend

# Start all
.\start-services.ps1 -All
```

**Features:**
- Color-coded output (Green=success, Red=error, Yellow=warning)
- Automatic prerequisite checking
- Automatic setup (venv, node_modules, .env)
- Support for selective service startup
- Better error messages

**Enable Script Execution:**
If you see "cannot be loaded because running scripts is disabled", enable it:

```powershell
# For current user only
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then try again
.\start-services.ps1
```

---

## Quick Start Workflows

### Complete Local Setup (First Time)

**Terminal 1 - Backend:**
```bash
cd backend
start-backend.bat
# Waits for first setup (2-3 minutes), then backend runs
```

**Terminal 2 - Frontend:**
```bash
cd frontend
start-frontend.bat
# Waits for first setup (2-3 minutes), then frontend runs
```

**Terminal 3 - Redis (optional):**
```bash
redis-server
# Or use Windows Start menu to launch Redis
```

**Then:**
1. Open http://localhost:3000
2. Create account
3. Verify email
4. Login and use the application

---

### Subsequent Startups (Every Time After)

Just run the same commands as above. Setup steps are skipped if already done.

**Expected times:**
- Backend startup: ~1-2 seconds after venv activation
- Frontend startup: ~3-5 seconds
- Overall startup: ~5-10 seconds total

---

### Docker Alternative

Don't want to manage services? Use Docker:

```bash
docker-compose -f docker-compose-dev.yml up -d
# Everything starts in ~30 seconds
```

See `DOCKER_STARTUP.md` for details.

---

## Understanding the Scripts

### What Batch Scripts Do

```batch
@echo off                              # Hide commands
REM                                   # Comment
if not exist "app\main.py"            # Check if backend exists
echo ERROR: ...                        # Print error
pause                                  # Wait for user
exit /b 1                              # Exit with error code
call venv\Scripts\activate.bat         # Activate Python environment
pip install -r requirements.txt        # Install Python packages
uvicorn app.main:app --reload ...      # Start FastAPI
npm run dev                            # Start Next.js
```

### What PowerShell Script Does

```powershell
param(                                 # Script parameters
    [switch]$Backend,
    [switch]$Frontend
)

function Write-Success {               # Define reusable function
    param([string]$Text)
    Write-Host "✓ $Text" -ForegroundColor Green
}

$pythonExists = Check-Command python   # Check if command exists
Push-Location .\backend                # Change directory
& .\venv\Scripts\Activate.ps1          # Call script with &
Pop-Location                           # Return to previous directory
```

---

## Troubleshooting Scripts

### "Command not found"

**Batch:**
```
The system cannot find the specified file
```
- Check you're in the correct directory
- Check the script name is spelled correctly
- Try running the full path: `C:\path\to\start-backend.bat`

**PowerShell:**
```
start-services.ps1 : File not found
```
- Check you're in the project root
- Try with path: `.\start-services.ps1`
- Check script execution is enabled (see above)

---

### "Port already in use"

**Error:**
```
ERROR: Address already in use
```

**Solution:**
```bash
# Find what's using the port
netstat -ano | findstr :8000    # Backend port
netstat -ano | findstr :3000    # Frontend port

# Kill the process (replace PID)
taskkill /PID <PID> /F

# Or use different port:
# Edit start-backend.bat and change 8000 to 8001
```

---

### "Python/Node not found"

**Error:**
```
Python is not installed or not in PATH
Node.js is not installed or not in PATH
```

**Solution:**
1. Install the missing software:
   - Python: https://www.python.org/downloads/
   - Node.js: https://nodejs.org/

2. Make sure to add to PATH during installation

3. Close and reopen terminal for PATH to update

4. Verify installation:
   ```bash
   python --version
   node --version
   ```

---

### "Permission denied" (PowerShell)

**Error:**
```
cannot be loaded because running scripts is disabled
```

**Solution:**
```powershell
# Run PowerShell as Administrator
# Then:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Type 'Y' to confirm
# Then close and reopen PowerShell
```

---

### Script stops immediately

**Check:**
1. Read the error message carefully
2. Look for "ERROR:" prefix
3. Common issues:
   - Wrong directory (not in backend/ or frontend/)
   - Missing dependencies (Python, Node.js)
   - Port already in use
   - Corrupted .env file

**Debug:**
```bash
# Run commands manually to see actual error
cd backend
python --version
pip install -r requirements.txt
uvicorn app.main:app --reload
```

---

## Comparing Methods

### Batch Scripts
- ✓ Simple and straightforward
- ✓ Works without PowerShell
- ✓ Good for one-service startup
- ✗ Less flexible
- ✗ Limited error handling

### PowerShell Script
- ✓ More flexible (multi-service)
- ✓ Better error messages (colored output)
- ✓ Parameter support (-Backend, -Frontend)
- ✗ Requires PowerShell enabled
- ✗ Slightly more complex

### Docker Compose
- ✓ One command starts everything
- ✓ No local dependencies needed
- ✓ Isolated environments
- ✗ Slightly slower startup
- ✗ Requires Docker installation

### Manual Commands
- ✓ Full control
- ✓ Easy debugging
- ✗ More typing
- ✗ Easy to make mistakes

---

## Advanced Usage

### Running Multiple Backends (for testing)

**Terminal 1:**
```bash
cd backend
# Edit start-backend.bat or use direct command:
uvicorn app.main:app --reload --port 8000
```

**Terminal 2:**
```bash
cd backend
venv\Scripts\activate
uvicorn app.main:app --reload --port 8001
```

Now you have two backend instances on ports 8000 and 8001.

---

### Keeping Terminal Open After Error

**Batch:**
Already included! Errors show with `pause` to review message.

**PowerShell:**
```powershell
.\start-services.ps1 ; Pause
```

The `;` runs pause after the script ends (whether success or error).

---

### Running in Task Scheduler (Windows)

Create a scheduled task to auto-start services:

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (e.g., "At startup")
4. Action: "Start a program"
5. Program: `C:\Windows\System32\cmd.exe`
6. Arguments: `/c D:\path\to\start-backend.bat`
7. Set to run whether user is logged in or not

---

## Environment Variables in Scripts

Scripts read from `.env` file (backend) and use defaults.

**To modify:**

**Batch:**
Edit the script and look for environment variables, then modify.

**PowerShell:**
```powershell
# Set before running
$env:DATABASE_URL = "postgresql://..."
.\start-services.ps1
```

---

## Uninstalling/Cleanup

### Remove Virtual Environment
```bash
cd backend
rmdir /s /q venv
# Or
Remove-Item -Recurse -Force venv
```

### Remove Node Modules
```bash
cd frontend
rmdir /s /q node_modules
# Or
Remove-Item -Recurse -Force node_modules
```

### Start Fresh
```bash
# Backend
cd backend
rmdir /s /q venv
start-backend.bat

# Frontend
cd frontend
rmdir /s /q node_modules
start-frontend.bat
```

---

## Tips & Tricks

### Keep Services Running After Restart

Use Windows Task Scheduler to auto-start with the scripts.

### Monitor Multiple Terminals

Use Windows Terminal with multiple tabs:
1. Open Windows Terminal
2. Ctrl+Shift+2 to split into two panes
3. Run start-backend.bat in one
4. Run start-frontend.bat in the other
5. Resize panes to see both

### Faster Startup with Visual Studio Code

1. Open project in VS Code
2. Open integrated terminal (Ctrl+`)
3. Run `start-backend.bat`
4. Open another terminal (Ctrl+Shift+`)
5. Run `start-frontend.bat`
6. Watch both in one window!

### Background Execution

**PowerShell:**
```powershell
Start-Process powershell -ArgumentList "-NoExit", "-Command", ".\start-services.ps1"
```

This starts services in a new window while keeping current window open.

---

## Getting Help

If scripts don't work:

1. **Read the error message** - it usually tells you what's wrong
2. **Check prerequisites** - Python, Node.js, PostgreSQL, Redis
3. **Check ports** - 3000, 8000, 5432, 6379
4. **Try manual startup** - see STARTUP_GUIDE.md
5. **Use Docker** - see DOCKER_STARTUP.md

---

## Version Information

- **Batch Scripts:** Compatible with Windows 7+
- **PowerShell Script:** Requires PowerShell 3.0+ (included with Windows 7+)
- **Dependencies:** See STARTUP_GUIDE.md

---

## Next Steps

1. Choose your method:
   - Easy: Use batch scripts or PowerShell
   - Simple: Use one command to start all (Docker)
   - Manual: See STARTUP_GUIDE.md

2. Run the script:
   ```bash
   start-backend.bat
   start-frontend.bat
   ```

3. Wait for "server started" message

4. Open http://localhost:3000

5. Create account and login

---

**Need Help?**
- Read STARTUP_GUIDE.md for detailed instructions
- Read QUICK_STARTUP.md for cheat sheet
- Read DOCKER_STARTUP.md for Docker method
- Check scripts for comments (lines starting with REM or #)

**Version:** 1.0.0 | **Last Updated:** January 2024
