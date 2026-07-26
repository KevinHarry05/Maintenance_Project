@echo off
REM SBMS Frontend Startup Script for Windows
REM This script starts the Next.js development server

title SBMS Frontend Server
echo.
echo ========================================
echo     SBMS Frontend Startup Script
echo ========================================
echo.

REM Check if we're in the frontend directory
if not exist "package.json" (
    echo.
    echo ERROR: package.json not found!
    echo Please run this script from the frontend directory:
    echo   cd frontend
    echo   start-frontend.bat
    echo.
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: Node.js is not installed or not in PATH!
    echo Please install Node.js 18+ from https://nodejs.org/
    echo.
    pause
    exit /b 1
)

echo ✓ Node.js found
node --version

REM Check if npm/pnpm is available
npm --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: npm is not available!
    echo.
    pause
    exit /b 1
)

echo ✓ npm found
npm --version

REM Check if node_modules exists
if not exist "node_modules" (
    echo.
    echo Installing dependencies (this may take 2-3 minutes)...
    call npm install
    if errorlevel 1 (
        echo.
        echo ERROR: Failed to install dependencies!
        echo.
        pause
        exit /b 1
    )
    echo ✓ Dependencies installed
)

REM Start the frontend server
echo.
echo ========================================
echo     Starting Frontend Server...
echo ========================================
echo.
echo Frontend will be available at:
echo   http://localhost:3000
echo.
echo Press Ctrl+C to stop the server
echo.

npm run dev

REM If dev server fails
if errorlevel 1 (
    echo.
    echo ERROR: Failed to start frontend server!
    echo.
    echo Troubleshooting:
    echo - Check that port 3000 is not in use
    echo - Try deleting node_modules and running again
    echo - Check for errors in package.json
    echo.
    pause
    exit /b 1
)
