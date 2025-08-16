@echo off
title Headless Streaming - Unreal Engine
cls

echo ============================================================
echo           HEADLESS OBS STREAMER FOR UNREAL ENGINE
echo ============================================================
echo.

REM Kill any existing OBS
taskkill /F /IM obs64.exe >nul 2>&1

echo Starting OBS in headless mode...
echo.

REM Change to OBS directory and start minimized
cd /d "C:\Program Files (x86)\Steam\steamapps\common\OBS Studio\bin\64bit"

REM Start OBS minimized to tray with auto-streaming
start /min "" obs64.exe --minimize-to-tray --startstreaming --disable-updater

echo ============================================================
echo                    STREAMING ACTIVE!
echo ============================================================
echo.
echo OBS is running in the background (system tray)
echo.
echo Capturing:
echo   - Unreal Engine / Game windows (auto-detect)
echo   - Desktop display (fallback)
echo   - Desktop audio (microphone muted)
echo.
echo To stop streaming:
echo   - Right-click OBS icon in system tray
echo   - Select Exit
echo.
echo ============================================================
echo.
echo You can close this window. OBS will continue streaming.
timeout /t 10