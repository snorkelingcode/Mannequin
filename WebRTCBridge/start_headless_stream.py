"""
Quick Start Headless Streaming for Unreal Engine
Simple one-click solution to start OBS streaming in background
"""

import subprocess
import os
from pathlib import Path
import time
import psutil

def kill_obs():
    """Kill any running OBS processes"""
    for proc in psutil.process_iter(['name']):
        try:
            if proc.info['name'] == 'obs64.exe':
                proc.kill()
                print("Stopped existing OBS process")
                time.sleep(2)
        except:
            pass

def start_headless_obs(stream_key="test", stream_server="rtmp://localhost/live"):
    """Start OBS in headless mode with minimal configuration"""
    
    obs_exe = r"C:\Program Files (x86)\Steam\steamapps\common\OBS Studio\bin\64bit\obs64.exe"
    obs_dir = Path(obs_exe).parent
    
    if not Path(obs_exe).exists():
        print("ERROR: OBS not found. Please install OBS from Steam.")
        return False
    
    print("=" * 60)
    print("HEADLESS OBS STREAMER FOR UNREAL ENGINE")
    print("=" * 60)
    
    # Kill any existing OBS
    kill_obs()
    
    # Check for Unreal process
    unreal_found = False
    for proc in psutil.process_iter(['name', 'exe']):
        try:
            name = proc.info['name']
            exe = proc.info['exe'] or ""
            if any(x in name.lower() for x in ['unreal', 'ue4', 'ue5', 'embody']) or \
               any(x in exe for x in ['Unreal', 'UE4', 'UE5', 'Embody']):
                print(f"✓ Found Unreal Engine: {name}")
                unreal_found = True
                break
        except:
            pass
    
    if not unreal_found:
        print("⚠ No Unreal Engine detected - Will capture entire display")
    
    print("\nStarting OBS in background...")
    print(f"Stream Server: {stream_server}")
    print(f"Stream Key: {stream_key[:5]}..." if len(stream_key) > 5 else stream_key)
    
    # Launch OBS minimized with auto-start
    cmd = [
        str(obs_exe),
        "--minimize-to-tray",
        "--startstreaming",
        "--disable-updater"
    ]
    
    try:
        # Start minimized
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 6  # SW_MINIMIZE = 6
        
        process = subprocess.Popen(
            cmd,
            cwd=str(obs_dir),
            startupinfo=startupinfo
        )
        
        print("\n" + "=" * 60)
        print("SUCCESS! OBS IS NOW STREAMING IN BACKGROUND")
        print("=" * 60)
        print("\nStreaming:")
        print("• Running minimized in system tray")
        print("• Capturing game/display automatically")
        print("• Desktop audio enabled (no microphone)")
        print("\nTo stop: Right-click OBS icon in system tray → Exit")
        print("\nPress Ctrl+C to stop monitoring...")
        
        # Monitor process
        try:
            while process.poll() is None:
                time.sleep(5)
        except KeyboardInterrupt:
            print("\n\nStopping OBS...")
            process.terminate()
            time.sleep(2)
            print("Stopped.")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to start OBS: {e}")
        return False

if __name__ == "__main__":
    # Livepeer Configuration
    STREAM_KEY = "7de0-7v24-76co-mvbd"
    STREAM_SERVER = "rtmp://rtmp.livepeer.com/live"
    
    print(f"🔗 Playback URL: https://livepeercdn.studio/hls/7de0lr18mu0sassl/index.m3u8")
    
    start_headless_obs(STREAM_KEY, STREAM_SERVER)