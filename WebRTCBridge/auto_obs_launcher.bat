@echo off
title Headless OBS Streamer for Unreal Engine
echo ============================================================
echo Headless OBS Streamer - Auto Launch
echo ============================================================
echo.

REM Change to OBS directory
cd /d "C:\Program Files (x86)\Steam\steamapps\common\OBS Studio\bin\64bit"

REM Check if OBS exists
if not exist "obs64.exe" (
    echo ERROR: OBS not found at expected location
    echo Please verify OBS is installed via Steam
    pause
    exit /b 1
)

echo Starting OBS in minimized mode with auto-streaming...
echo.

REM Launch OBS minimized with streaming
start /min "" obs64.exe --minimize-to-tray --startstreaming --disable-updater

echo OBS is now running in the background
echo.
echo Status:
echo - Running minimized in system tray
echo - Auto-streaming enabled
echo - Capturing display/game automatically
echo.
echo To stop: Right-click OBS icon in system tray and Exit
echo.
timeout /t 5