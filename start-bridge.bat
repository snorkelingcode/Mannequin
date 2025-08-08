@echo off
echo 🌉 Starting Mannequin WebSocket Bridge...
echo ======================================

cd websocket-bridge

if not exist .env (
    echo ❌ Error: .env file not found!
    echo Please run setup.bat first or create .env from .env.example
    pause
    exit /b 1
)

if not exist node_modules (
    echo ❌ Error: node_modules not found!
    echo Please run setup.bat first or 'npm install'
    pause
    exit /b 1
)

echo 🚀 Starting bridge server...
echo Bridge will be available at:
echo - WebSocket: ws://localhost:8080
echo - HTTP API: http://localhost:3001
echo.
echo Press Ctrl+C to stop the server
echo.
npm start