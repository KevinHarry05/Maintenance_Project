@echo off
REM TASK 1: Diagnose Pydantic/pydantic-core Import Error

setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo ======================================================================
echo TASK 1: DIAGNOSE PYDANTIC/PYDANTIC-CORE IMPORT ERROR
echo ======================================================================
echo.

echo 1.1 Check Python Version...
call venv\Scripts\activate.bat
python --version

echo.
echo 1.2 Check Virtual Environment...
where python

echo.
echo 1.3 List Pydantic Packages...
pip list | findstr pydantic

echo.
echo 1.4 Test pydantic import...
python -c "import pydantic; print(f'pydantic version: {pydantic.__version__}')" 2>&1

echo.
echo 1.5 Test pydantic_core import...
python -c "from pydantic_core import core; print('pydantic_core OK')" 2>&1

echo.
echo 1.6 Test FastAPI import...
python -c "import fastapi; print(f'fastapi OK')" 2>&1

echo.
echo 1.7 Test app.main import...
python -c "from app.main import app; print('app.main OK')" 2>&1

echo.
echo ======================================================================
echo DIAGNOSTIC COMPLETE
echo ======================================================================
