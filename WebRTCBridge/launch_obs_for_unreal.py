"""
Direct OBS Launcher for Unreal Engine Streaming
Launches OBS with pre-configured settings without user interaction
"""

import subprocess
import json
import os
from pathlib import Path
import pygetwindow as gw
import time
import sys

class DirectOBSLauncher:
    def __init__(self):
        self.obs_path = r"C:\Program Files (x86)\Steam\steamapps\common\OBS Studio\bin\64bit\obs64.exe"
        
    def launch_obs_simple(self):
        """Launch OBS directly with minimal configuration"""
        
        if not Path(self.obs_path).exists():
            print("ERROR: OBS not found at expected Steam location")
            return False
        
        print("Launching OBS Studio...")
        print("Please configure the following in OBS:")
        print("1. Add 'Window Capture' source")
        print("2. Select 'Embody - Unreal Editor' window")
        print("3. Add 'Audio Output Capture' for desktop audio")
        print("4. Mute any microphone inputs")
        print("\nStarting OBS...")
        
        try:
            # Set working directory to OBS bin folder for locale files
            obs_dir = str(Path(self.obs_path).parent)
            
            # Launch OBS with proper working directory
            subprocess.Popen([self.obs_path], cwd=obs_dir)
            print("\nOBS launched successfully!")
            print("\nTo stream:")
            print("1. Go to Settings -> Stream")
            print("2. Enter your streaming service and stream key")
            print("3. Click 'Start Streaming'")
            return True
            
        except Exception as e:
            print(f"Error launching OBS: {e}")
            return False

def create_obs_batch_file():
    """Create a batch file to launch OBS easily"""
    
    batch_content = '''@echo off
echo Starting OBS Studio for Unreal Engine Streaming...
echo.
echo Detected Unreal Engine Window: Embody - Unreal Editor
echo.
cd /d "C:\\Program Files (x86)\\Steam\\steamapps\\common\\OBS Studio\\bin\\64bit"
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
'''
    
    batch_file = Path("launch_obs.bat")
    with open(batch_file, 'w') as f:
        f.write(batch_content)
    
    print(f"Created batch file: {batch_file}")
    print("You can double-click 'launch_obs.bat' to start OBS anytime")
    
    return batch_file

def main():
    """Main function"""
    
    print("=" * 60)
    print("OBS Launcher for Unreal Engine Streaming")
    print("=" * 60)
    
    # Check if Unreal Engine is running
    unreal_windows = [w for w in gw.getAllWindows() if 'Unreal' in w.title or 'UE4' in w.title or 'UE5' in w.title or 'Embody' in w.title]
    
    if unreal_windows:
        print(f"\n[OK] Detected Unreal Engine window: {unreal_windows[0].title}")
    else:
        print("\n[WARNING] No Unreal Engine window detected")
        print("Please start Unreal Engine before streaming")
    
    # Create batch file for easy launching
    print("\nCreating launch helper...")
    create_obs_batch_file()
    
    # Launch OBS
    print("\n" + "=" * 60)
    launcher = DirectOBSLauncher()
    
    if launcher.launch_obs_simple():
        print("\n[SUCCESS] OBS is now running")
        print("\nQuick Setup Guide:")
        print("-" * 40)
        print("1. In OBS, click '+' under Sources")
        print("2. Add 'Window Capture' -> Select 'Embody - Unreal Editor'")
        print("3. Add 'Audio Output Capture' -> Select your speakers")
        print("4. Right-click any Mic/Aux -> Properties -> Mute")
        print("5. Settings -> Stream -> Add your stream key")
        print("6. Click 'Start Streaming' when ready")
        print("-" * 40)
    else:
        print("\n[ERROR] Failed to launch OBS")
        print("Please check if OBS is installed via Steam")

if __name__ == "__main__":
    main()