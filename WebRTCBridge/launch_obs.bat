@echo off
echo Starting OBS Studio for Unreal Engine Streaming...
echo.
echo Detected Unreal Engine Window: Embody - Unreal Editor
echo.
cd /d "C:\Program Files (x86)\Steam\steamapps\common\OBS Studio\bin\64bit"
start "" obs64.exe
echo.
echo OBS has been launched!
echo.
echo Please configure in OBS:
echo 1. Add Source: Window Capture - Select "Embody - Unreal Editor"
echo 2. Add Source: Audio Output Capture (Desktop Audio)
echo 3. Mute microphone if present
echo 4. Configure stream settings (Settings - Stream)
echo.
pause
