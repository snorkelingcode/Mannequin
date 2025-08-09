@echo off
title Mannequin Startup Manager
color 0A

echo.
echo ████████████████████████████████████████████
echo █                                          █
echo █          🎭 MANNEQUIN STARTUP           █  
echo █                                          █
echo ████████████████████████████████████████████
echo.
echo 🚀 Launching all Mannequin services...
echo.

:: Set working directory
set MANNEQUIN_DIR=C:\Users\danek\OneDrive\Desktop\Mannequin
cd /d "%MANNEQUIN_DIR%"

:: Function to check if process is running
setlocal enabledelayedexpansion

echo [1/4] 🌐 Starting ngrok tunnel...
echo       Connecting to permanent address: 5.tcp.ngrok.io:28371
start "Mannequin-ngrok" /min cmd /c "ngrok tcp 7777 --remote-addr=5.tcp.ngrok.io:28371"
echo       ✅ ngrok tunnel started (minimized window)
echo.

:: Wait for ngrok to establish connection
echo       ⏳ Waiting for tunnel to establish...
timeout /t 5 /nobreak >nul

echo [2/4] 📹 Starting WebRTC Bridge...
echo       Video streaming: Unreal Engine → Livepeer
echo       Audio capture: Realtek Device 21
cd /d "%MANNEQUIN_DIR%\WebRTCBridge"
start "Mannequin-WebRTC" cmd /k "echo 🎥 WebRTC Bridge Console && echo. && python webrtc_bridge_with_raw_audio.py"
echo       ✅ WebRTC Bridge started
echo.

:: Return to main directory
cd /d "%MANNEQUIN_DIR%"

echo [3/4] 🎮 Looking for Unreal Engine executable...
:: Check common locations for the .exe
set "GAME_EXE="
if exist "C:\UnrealBuilds\Embody\Binaries\Win64\Embody.exe" (
    set "GAME_EXE=C:\UnrealBuilds\Embody\Binaries\Win64\Embody.exe"
)
if exist "C:\UnrealBuilds\Embody\Binaries\Win64\EmbodyEditor.exe" (
    set "GAME_EXE=C:\UnrealBuilds\Embody\Binaries\Win64\EmbodyEditor.exe"
)

if defined GAME_EXE (
    echo       Found: !GAME_EXE!
    echo       🚀 Launching Unreal Engine...
    start "Mannequin-Game" "!GAME_EXE!"
    echo       ✅ Unreal Engine started
) else (
    echo       ⚠️  Unreal Engine executable not found!
    echo       Please manually start your .exe file from:
    echo       C:\UnrealBuilds\Embody\Binaries\Win64\
)
echo.

echo [4/4] 🌐 Opening web interfaces...
timeout /t 3 /nobreak >nul
start "" "https://mannequin.live"
start "" "http://127.0.0.1:4040"
echo       ✅ Web interfaces opened
echo.

echo ████████████████████████████████████████████
echo █              🎉 ALL READY! 🎉            █
echo ████████████████████████████████████████████
echo.
echo 📊 Service Status:
echo   🌐 ngrok tunnel     : Running (5.tcp.ngrok.io:28371)
echo   📹 WebRTC Bridge    : Running (Video + Audio)
echo   🎮 Unreal Engine    : %if defined GAME_EXE (echo Running) else (echo Manual start needed)%
echo   🌍 Frontend         : https://mannequin.live
echo.
echo 🎯 Quick Links:
echo   • Frontend: https://mannequin.live
echo   • ngrok Dashboard: http://127.0.0.1:4040  
echo   • Stream Player: https://lvpr.tv/7de0lr18mu0sassl
echo.
echo 💡 Tips:
echo   • All services run in separate windows
echo   • Close this window when done to keep services running
echo   • Check ngrok dashboard to monitor tunnel status
echo.
echo Press any key to finish setup...
pause >nul
cls
echo.
echo 🎭 Mannequin is ready! Have fun creating! 🎨
echo.
timeout /t 3 /nobreak >nul