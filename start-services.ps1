# SBMS Complete Startup Script (PowerShell)
# This script starts all required services for SBMS development

param(
    [switch]$Backend,
    [switch]$Frontend,
    [switch]$Redis,
    [switch]$All
)

function Write-Header {
    param([string]$Text)
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "  $Text" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
}

function Write-Success {
    param([string]$Text)
    Write-Host "✓ $Text" -ForegroundColor Green
}

function Write-Error {
    param([string]$Text)
    Write-Host "✗ $Text" -ForegroundColor Red
}

function Write-Warning {
    param([string]$Text)
    Write-Host "⚠ $Text" -ForegroundColor Yellow
}

function Check-Command {
    param([string]$Command)
    $cmd = Get-Command $Command -ErrorAction SilentlyContinue
    return $null -ne $cmd
}

# Default to all if no options specified
if (-not $Backend -and -not $Frontend -and -not $Redis -and -not $All) {
    $All = $true
}

$startBackend = $Backend -or $All
$startFrontend = $Frontend -or $All
$startRedis = $Redis -or $All

Write-Header "SBMS Startup Service"

Write-Host "Starting services:" -ForegroundColor Cyan
if ($startBackend) { Write-Host "  • Backend (FastAPI)" }
if ($startFrontend) { Write-Host "  • Frontend (Next.js)" }
if ($startRedis) { Write-Host "  • Redis" }
Write-Host ""

# Check prerequisites
Write-Host "Checking prerequisites..." -ForegroundColor Yellow

$pythonExists = Check-Command python
$nodeExists = Check-Command node
$npmExists = Check-Command npm
$redisExists = Check-Command redis-cli

Write-Host ""
if ($startBackend) {
    if (-not $pythonExists) {
        Write-Error "Python not found! Install from https://www.python.org/"
        exit 1
    }
    Write-Success "Python found: $(python --version)"
}

if ($startFrontend) {
    if (-not $nodeExists) {
        Write-Error "Node.js not found! Install from https://nodejs.org/"
        exit 1
    }
    Write-Success "Node.js found: $(node --version)"
    
    if (-not $npmExists) {
        Write-Error "npm not found!"
        exit 1
    }
    Write-Success "npm found: $(npm --version)"
}

if ($startRedis) {
    if (-not $redisExists) {
        Write-Warning "Redis CLI not found. Is Redis running?"
    } else {
        Write-Success "Redis CLI found"
    }
}

Write-Host ""

# Setup and start backend
if ($startBackend) {
    Write-Header "Backend Setup"
    
    if (-not (Test-Path ".\backend\app\main.py")) {
        Write-Error "backend\app\main.py not found!"
        exit 1
    }
    
    Push-Location .\backend
    
    # Create venv if needed
    if (-not (Test-Path ".\venv")) {
        Write-Host "Creating Python virtual environment..."
        python -m venv venv
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to create virtual environment"
            Pop-Location
            exit 1
        }
        Write-Success "Virtual environment created"
        
        Write-Host "Installing dependencies (this may take 2-3 minutes)..."
        & .\venv\Scripts\Activate.ps1
        pip install --upgrade pip | Out-Null
        pip install -r requirements.txt
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to install dependencies"
            Pop-Location
            exit 1
        }
        Write-Success "Dependencies installed"
    }
    
    # Activate venv
    & .\venv\Scripts\Activate.ps1
    Write-Success "Virtual environment activated"
    
    # Check .env
    if (-not (Test-Path ".\.env")) {
        Write-Warning ".env not found, creating from .env.example"
        if (Test-Path ".\.env.example") {
            Copy-Item ".\.env.example" ".\.env"
            Write-Success ".env created (update with your configuration)"
        } else {
            Write-Error ".env.example not found"
            Pop-Location
            exit 1
        }
    }
    
    Write-Header "Starting Backend Server"
    Write-Host "Backend will be available at:" -ForegroundColor Green
    Write-Host "  http://localhost:8000" -ForegroundColor Green
    Write-Host "  Documentation: http://localhost:8000/docs" -ForegroundColor Green
    Write-Host ""
    Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
    Write-Host ""
    
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
    
    Pop-Location
}

# Setup and start frontend
if ($startFrontend) {
    Write-Header "Frontend Setup"
    
    if (-not (Test-Path ".\frontend\package.json")) {
        Write-Error "frontend\package.json not found!"
        exit 1
    }
    
    Push-Location .\frontend
    
    # Install dependencies if needed
    if (-not (Test-Path ".\node_modules")) {
        Write-Host "Installing dependencies (this may take 2-3 minutes)..."
        npm install
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Failed to install dependencies"
            Pop-Location
            exit 1
        }
        Write-Success "Dependencies installed"
    }
    
    Write-Header "Starting Frontend Server"
    Write-Host "Frontend will be available at:" -ForegroundColor Green
    Write-Host "  http://localhost:3000" -ForegroundColor Green
    Write-Host ""
    Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
    Write-Host ""
    
    npm run dev
    
    Pop-Location
}

# Start Redis
if ($startRedis) {
    Write-Header "Starting Redis"
    Write-Host "Redis will be available at:" -ForegroundColor Green
    Write-Host "  redis://localhost:6379" -ForegroundColor Green
    Write-Host ""
    Write-Host "Press Ctrl+C to stop" -ForegroundColor Yellow
    Write-Host ""
    
    redis-server
}

Write-Warning "Server stopped"
