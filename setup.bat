@echo off
echo 🎭 Mannequin Setup Script
echo ========================

echo.
echo 📦 Installing WebSocket Bridge dependencies...
cd websocket-bridge
call npm install
if errorlevel 1 (
    echo ❌ Failed to install bridge dependencies
    pause
    exit /b 1
)

echo.
echo 📦 Installing Frontend dependencies...
cd ..\frontend
call npm install
if errorlevel 1 (
    echo ❌ Failed to install frontend dependencies
    pause
    exit /b 1
)

echo.
echo 🔧 Creating configuration files...
cd ..\websocket-bridge
if not exist .env (
    copy .env.example .env
    echo ✅ Created websocket-bridge/.env from example
) else (
    echo ⚠️ websocket-bridge/.env already exists
)

cd ..\frontend
if not exist .env.local (
    copy .env.local.example .env.local
    echo ✅ Created frontend/.env.local from example
) else (
    echo ⚠️ frontend/.env.local already exists
)

echo.
echo 🎉 Setup completed successfully!
echo.
echo 📋 Next Steps:
echo 1. Configure your .env files with proper settings
echo 2. Start Unreal Engine with TCP server on port 7777
echo 3. Run start-bridge.bat to start the WebSocket bridge
echo 4. Run start-frontend.bat to start the React app
echo 5. Open http://localhost:3000 in your browser
echo.
echo 🔧 Configuration files to edit:
echo - websocket-bridge/.env (bridge settings)
echo - frontend/.env.local (frontend URLs)
echo.
pause