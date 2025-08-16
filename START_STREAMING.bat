@echo off
echo 🚀 Starting Mannequin Streaming Platform...
echo.

REM Kill any existing processes on ports 8080, 8001, and 3000/3001
echo Cleaning up existing processes...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8080') do taskkill /PID %%a /F >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8001') do taskkill /PID %%a /F >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000') do taskkill /PID %%a /F >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3001') do taskkill /PID %%a /F >nul 2>&1

echo.
echo Starting services in separate terminals...

REM Start WebSocket Bridge (Terminal 1)
echo 📡 Starting WebSocket Bridge...
start "WebSocket Bridge" cmd /k "cd /d "C:\Users\danek\OneDrive\Desktop\Mannequin\websocket-bridge" && echo Starting WebSocket Bridge... && npm start"

REM Wait a moment for bridge to start
timeout /t 3 /nobreak >nul

REM Start Frontend (Terminal 2)
echo 🌐 Starting Frontend...
start "Frontend" cmd /k "cd /d "C:\Users\danek\OneDrive\Desktop\Mannequin\frontend" && echo Starting Frontend... && npm run dev"

REM Start Text-to-Face Hook (Terminal 3)
echo 🎭 Starting Text-to-Face Hook...
start "Text-to-Face Hook" cmd /k "cd /d "C:\Users\danek\OneDrive\Desktop\NeuroBuff\neurosync\neurosync_player-main" && echo Starting Text-to-Face Hook... && python chat_response_hook.py"

REM Wait a moment for text-to-face to start
timeout /t 2 /nobreak >nul

echo.
echo ✅ All services starting...
echo 📡 WebSocket Bridge: http://localhost:8080
echo 🎭 Text-to-Face Hook: http://localhost:8001
echo 🌐 Frontend: http://localhost:3000 or http://localhost:3001
echo.
echo Wait 15-20 seconds then open your browser to:
echo http://localhost:3000 (or 3001 if 3000 is busy)
echo.
echo 🎮 Ready to stream with AI chat and facial animations!
echo Press any key to close this window...
pause >nul