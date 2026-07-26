@echo off
REM TASK 2: Repair Pydantic Dependencies

setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo ======================================================================
echo TASK 2: REPAIR PYDANTIC DEPENDENCIES
echo ======================================================================
echo.

echo 2.1 Activating Virtual Environment...
call venv\Scripts\activate.bat

echo.
echo 2.2 Upgrading pip...
python -m pip install --upgrade pip

echo.
echo 2.3 Backing up current pip list...
pip freeze > requirements_backup.txt

echo.
echo 2.4 Uninstalling incompatible pydantic packages...
pip uninstall -y pydantic pydantic-core pydantic-settings

echo.
echo 2.5 Clearing pip cache...
pip cache purge

echo.
echo 2.6 Installing pydantic-core 2.10.1...
pip install --force-reinstall pydantic-core==2.10.1

echo.
echo 2.7 Installing pydantic 2.5.0...
pip install --force-reinstall pydantic==2.5.0

echo.
echo 2.8 Installing all requirements...
pip install -r requirements.txt

echo.
echo 2.9 Verifying pydantic imports...
python -c "import pydantic; print(f'pydantic {pydantic.__version__}')" 2>&1

echo.
echo 2.10 Verifying pydantic_core imports...
python -c "from pydantic_core import core; print('pydantic_core OK')" 2>&1

echo.
echo 2.11 Verifying FastAPI imports...
python -c "import fastapi; print(f'fastapi OK')" 2>&1

echo.
echo ======================================================================
echo TASK 2 COMPLETE
echo ======================================================================
