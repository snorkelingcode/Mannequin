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
start "Text-to-Face Hook" cmd /k "cd /d "C:\Users\danek\OneDrive\Desktop\NeuroBuff\Neurosync\NeuroSync_Player-main" && echo Installing flask-cors if needed... && pip install flask-cors && echo Starting Text-to-Face Hook... && python chat_response_hook.py"

REM Wait a moment for text-to-face to start
timeout /t 2 /nobreak >nul

REM Start ngrok tunnels with config file (Terminal 4)
echo 🔒 Starting ngrok tunnels (HTTP + TCP)...
start "ngrok Tunnels" cmd /k "cd /d "C:\Users\danek\OneDrive\Desktop\Mannequin" && echo Starting ngrok with config file... && ngrok start --config ngrok-config.yml --all"

REM Wait for ngrok tunnels to start
timeout /t 5 /nobreak >nul

echo.
echo ✅ All services starting...
echo 📡 WebSocket Bridge: http://localhost:8080
echo 🎭 Text-to-Face Hook: http://localhost:8001
echo 🔒 ngrok Tunnels: Check ngrok window for URLs
echo    - HTTP tunnel for text-to-face (port 8001)
echo    - TCP tunnel: 5.tcp.ngrok.io:28371 (for Unreal Engine port 7777)
echo 🌐 Frontend: http://localhost:3000 or http://localhost:3001
echo.
echo ⚠️  IMPORTANT: After ngrok starts, you need to:
echo    1. Check the ngrok window for your HTTP tunnel URL (e.g., https://abc123.ngrok.app)
echo    2. Update frontend/.env.local with: NEXT_PUBLIC_TEXT_TO_FACE_URL=YOUR_NGROK_URL/chat_response
echo    3. Restart the frontend (close and re-run this batch file)
echo.
echo 🎮 For Unreal Engine:
echo    - Your TCP connection is available at: 5.tcp.ngrok.io:28371
echo    - Configure your Unreal TCP actor to connect to this address
echo.
echo Wait 25-30 seconds for all services to start...
echo Then open your browser to: http://localhost:3000 (or 3001)
echo.
echo 🎮 Ready to stream with AI chat, facial animations, and Unreal Engine TCP!
echo Press any key to close this window...
pause >nul