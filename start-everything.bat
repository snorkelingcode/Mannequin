@echo off
echo ========================================
echo 🚀 MANNEQUIN ONE-CLICK STARTUP
echo ========================================
echo.
echo Starting all services for Mannequin...
echo.

:: Change to the Mannequin directory
cd /d "C:\Users\danek\OneDrive\Desktop\Mannequin"

:: Start ngrok tunnel in background
echo 🌐 Starting ngrok tunnel (5.tcp.ngrok.io:28371)...
start "ngrok-tunnel" /min ngrok tcp 7777 --remote-addr=5.tcp.ngrok.io:28371

:: Wait a moment for ngrok to initialize
timeout /t 3 /nobreak >nul

:: Start WebRTC Bridge
echo 📹 Starting WebRTC Bridge...
start "webrtc-bridge" cmd /k "cd /d C:\Users\danek\OneDrive\Desktop\Mannequin\WebRTCBridge && python webrtc_bridge_with_raw_audio.py"

:: Wait a moment for bridge to initialize
timeout /t 2 /nobreak >nul

:: Start Unreal Engine Game (you'll need to update this path)
echo 🎮 Starting Unreal Engine Game...
:: TODO: Update this path to your actual .exe file
:: start "unreal-game" "C:\UnrealBuilds\Embody\Binaries\Win64\Embody.exe"
echo ⚠️  Please update the game path in start-everything.bat
echo    Current placeholder: C:\UnrealBuilds\Embody\Binaries\Win64\Embody.exe

echo.
echo ✅ All services started!
echo.
echo 📊 Service Status:
echo   - ngrok tunnel: Running (minimized)
echo   - WebRTC bridge: Running (separate window)
echo   - Unreal Engine: Manual start needed
echo.
echo 🌐 URLs:
echo   - Frontend: https://mannequin.live
echo   - ngrok Web Interface: http://127.0.0.1:4040
echo   - Livepeer Playback: https://lvpr.tv/7de0lr18mu0sassl
echo.
echo Press any key to continue...
pause >nul