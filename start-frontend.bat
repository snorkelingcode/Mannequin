@echo off
echo 🎭 Starting Mannequin Frontend...
echo ===============================

cd frontend

if not exist .env.local (
    echo ❌ Error: .env.local file not found!
    echo Please run setup.bat first or create .env.local from .env.local.example
    pause
    exit /b 1
)

if not exist node_modules (
    echo ❌ Error: node_modules not found!
    echo Please run setup.bat first or 'npm install'
    pause
    exit /b 1
)

echo 🚀 Starting development server...
echo Frontend will be available at:
echo - Development: http://localhost:3000
echo.
echo Press Ctrl+C to stop the server
echo.
npm run dev