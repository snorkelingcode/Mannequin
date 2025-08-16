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

REM Auto-update ngrok URL in .env.local (Terminal 5)
echo 🔄 Auto-updating ngrok URL in .env.local...
start "Auto-Update ngrok URL" cmd /k "cd /d "C:\Users\danek\OneDrive\Desktop\Mannequin" && echo Detecting ngrok URL and updating .env.local... && python update_ngrok_url.py"

REM Wait for URL update
timeout /t 3 /nobreak >nul

echo.
echo ✅ All services starting...
echo 📡 WebSocket Bridge: http://localhost:8080
echo 🎭 Text-to-Face Hook: http://localhost:8001
echo 🔒 ngrok Tunnels: Both HTTP and TCP tunnels running
echo    - HTTP tunnel for text-to-face (port 8001) - AUTO-DETECTED
echo    - TCP tunnel: 5.tcp.ngrok.io:28371 (for Unreal Engine port 7777)
echo 🔄 Auto-Update: Automatically updating .env.local with ngrok URL
echo 🌐 Frontend: http://localhost:3000 or http://localhost:3001
echo.
echo ✅ FULLY AUTOMATED: No manual steps required!
echo    - ngrok URL automatically detected and configured
echo    - .env.local updated automatically
echo    - Just wait for all services to start
echo.
echo 🎮 For Unreal Engine:
echo    - Your TCP connection is available at: 5.tcp.ngrok.io:28371
echo    - Configure your Unreal TCP actor to connect to this address
echo.
echo Wait 30-35 seconds for all services to start and auto-configure...
echo Then open your browser to: http://localhost:3000 (or 3001)
echo.
echo 🎮 Ready to stream with FULL AUTO-SETUP!
echo Press any key to close this window...
pause >nul