@echo off
echo 🚀 Starting Mannequin Streaming Platform...
echo.

REM Kill any existing processes on ports 8080 and 3000/3001
echo Cleaning up existing processes...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8080') do taskkill /PID %%a /F >nul 2>&1
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

REM Optional: Start Text-to-Face Hook (uncomment if you have it)
REM echo 🎭 Starting Text-to-Face Hook...
REM start "Text-to-Face Hook" cmd /k "cd /d "C:\Users\danek\OneDrive\Desktop\NeuroBuff\neurosync\neurosync_player-main" && echo Starting Text-to-Face Hook... && python chat_response_hook.py"

echo.
echo ✅ All services starting...
echo 📡 WebSocket Bridge: http://localhost:8080
echo 🌐 Frontend: http://localhost:3000 or http://localhost:3001
echo.
echo Wait 10-15 seconds then open your browser to:
echo http://localhost:3000 (or 3001 if 3000 is busy)
echo.
echo Press any key to close this window...
pause >nul