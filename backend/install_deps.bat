@echo off
setlocal enabledelayedexpansion

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Installing dependencies from requirements.txt...
pip install -r requirements.txt

echo.
echo Verifying pydantic installation...
python -c "import pydantic; print(f'Pydantic version: {pydantic.__version__}')"

echo.
echo Done!
pause
