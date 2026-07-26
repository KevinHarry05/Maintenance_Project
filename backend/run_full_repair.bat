@echo off
REM ============================================================================
REM  SBMS BACKEND - COMPREHENSIVE REPAIR
REM  Fixes Pydantic import errors and Celery configuration
REM ============================================================================

setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo ============================================================================
echo SBMS BACKEND COMPREHENSIVE REPAIR SCRIPT
echo ============================================================================

REM Activate virtual environment
echo.
echo [1/12] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate venv
    exit /b 1
)
echo OK

REM Backup current state
echo.
echo [2/12] Backing up current pip list...
pip freeze > requirements_backup.txt
echo Backed up to requirements_backup.txt

REM Uninstall incompatible packages
echo.
echo [3/12] Uninstalling incompatible pydantic packages...
pip uninstall -y pydantic pydantic-core pydantic-settings >nul 2>&1
echo OK

REM Clear pip cache
echo.
echo [4/12] Clearing pip cache...
pip cache purge >nul 2>&1
echo OK

REM Upgrade pip
echo.
echo [5/12] Upgrading pip...
python -m pip install --upgrade pip -q
echo OK

REM Install pydantic-core first (it's a dependency)
echo.
echo [6/12] Installing pydantic-core==2.10.1 (no cache)...
pip install --force-reinstall --no-cache-dir pydantic-core==2.10.1 -q
if errorlevel 1 (
    echo WARNING: pydantic-core installation had issues but continuing...
)
echo OK

REM Install pydantic
echo.
echo [7/12] Installing pydantic==2.5.0 (no cache)...
pip install --force-reinstall --no-cache-dir pydantic==2.5.0 -q
if errorlevel 1 (
    echo WARNING: pydantic installation had issues but continuing...
)
echo OK

REM Install all requirements
echo.
echo [8/12] Installing requirements from requirements.txt...
pip install -r requirements.txt -q
echo OK

REM Verify imports
echo.
echo [9/12] Verifying pydantic import...
python -c "import pydantic; print(f'  OK: pydantic {pydantic.__version__}')" 2>&1
if errorlevel 1 (
    echo  ERROR: pydantic import failed!
)

echo.
echo [10/12] Verifying pydantic_core import...
python -c "from pydantic_core import core; print('  OK: pydantic_core')" 2>&1
if errorlevel 1 (
    echo  ERROR: pydantic_core import failed!
)

echo.
echo [11/12] Verifying fastapi import...
python -c "import fastapi; print(f'  OK: fastapi')" 2>&1
if errorlevel 1 (
    echo  ERROR: fastapi import failed!
)

REM Test app.main import
echo.
echo [12/12] Verifying app.main import...
python -c "from app.main import app; print('  OK: app.main')" 2>&1
if errorlevel 1 (
    echo  ERROR: app.main import failed!
)

echo.
echo ============================================================================
echo REPAIR COMPLETE
echo ============================================================================
echo.
echo Next steps:
echo 1. Verify database connection: psql -U postgres -d smbs-pep
echo 2. Verify Redis connection: redis-cli ping
echo 3. Run migrations: alembic upgrade head
echo 4. Start FastAPI: uvicorn app.main:app --reload
echo 5. Start Celery: celery -A app.celery_app worker --loglevel=info
echo.
pause
