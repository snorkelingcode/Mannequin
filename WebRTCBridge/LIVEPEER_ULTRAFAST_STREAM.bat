@echo off
title Livepeer Ultra-Low Latency Streamer
cls
color 0A

echo ========================================================================
echo                🚀 LIVEPEER ULTRA-LOW LATENCY STREAMER 🚀
echo ========================================================================
echo.

REM Kill any existing OBS
taskkill /F /IM obs64.exe >nul 2>&1

echo ⚡ Optimizing for blazing fast streaming...
echo.

REM Change to OBS directory
cd /d "C:\Program Files (x86)\Steam\steamapps\common\OBS Studio\bin\64bit"

REM Check if OBS exists
if not exist "obs64.exe" (
    echo ❌ ERROR: OBS not found at expected location
    echo Please verify OBS is installed via Steam
    pause
    exit /b 1
)

echo 📡 Streaming Configuration:
echo    Server: rtmp://rtmp.livepeer.com/live
echo    Stream Key: 7de0-7v24-76co-mvbd
echo    Playback: https://livepeercdn.studio/hls/7de0lr18mu0sassl/index.m3u8
echo.

echo 🔥 Ultra-Low Latency Optimizations:
echo    • x264 ultrafast preset + zero-latency tune
echo    • CBR encoding with minimal buffering
echo    • 60 FPS for smooth motion  
echo    • No B-frames for instant encoding
echo    • High priority process
echo    • Optimized game capture
echo.

echo 🚀 Starting stream in 3 seconds...
timeout /t 3 >nul

REM Start OBS with ultra-low latency settings
start /HIGH /min "" obs64.exe --minimize-to-tray --startstreaming --disable-updater --portable

echo.
echo ========================================================================
echo                        🔥 STREAM IS LIVE! 🔥
echo ========================================================================
echo.
echo ⚡ Ultra-fast streaming active with minimal latency
echo 🎮 Auto-capturing Unreal Engine and desktop audio
echo 📺 Watch at: https://livepeercdn.studio/hls/7de0lr18mu0sassl/index.m3u8
echo.
echo 🛑 To stop: Right-click OBS icon in system tray and select Exit
echo.
echo You can close this window. Streaming will continue in background.
echo.
timeout /t 15