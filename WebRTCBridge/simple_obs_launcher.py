"""
Simple OBS Launcher for Unreal Engine Streaming
Launches OBS with pre-configured settings for capturing Unreal Engine and desktop audio
"""

import subprocess
import json
import os
from pathlib import Path
import pygetwindow as gw
import time

class SimpleOBSLauncher:
    def __init__(self):
        self.obs_path = self.find_obs_installation()
        self.config_dir = Path("obs_config")
        self.config_dir.mkdir(exist_ok=True)
        
    def find_obs_installation(self):
        """Find OBS installation path"""
        possible_paths = [
            r"C:\Program Files (x86)\Steam\steamapps\common\OBS Studio\bin\64bit\obs64.exe",
            r"C:\Program Files\obs-studio\bin\64bit\obs64.exe",
            r"C:\Program Files (x86)\obs-studio\bin\64bit\obs64.exe",
            r"C:\Program Files\OBS Studio\bin\64bit\obs64.exe",
            Path.home() / "AppData/Local/Programs/obs-studio/bin/64bit/obs64.exe"
        ]
        
        for path in possible_paths:
            if Path(path).exists():
                print(f"Found OBS at: {path}")
                return str(path)
        
        print("OBS installation not found. Please install OBS Studio from https://obsproject.com")
        return None
    
    def create_scene_collection(self):
        """Create OBS scene collection for Unreal Engine streaming"""
        
        # Find Unreal Engine window
        unreal_windows = [w for w in gw.getAllWindows() if 'Unreal' in w.title or 'UE4' in w.title or 'UE5' in w.title]
        window_title = unreal_windows[0].title if unreal_windows else "Unreal Engine"
        
        scene_collection = {
            "current_scene": "Unreal Stream",
            "current_program_scene": "Unreal Stream",
            "scene_order": [
                {"name": "Unreal Stream"}
            ],
            "sources": [
                {
                    "name": "Unreal Stream",
                    "uuid": "scene",
                    "settings": {},
                    "items": [
                        {
                            "name": "Unreal Engine Window",
                            "type": "window_capture",
                            "settings": {
                                "window": window_title,
                                "capture_cursor": True,
                                "compatibility": False,
                                "priority": 1
                            }
                        },
                        {
                            "name": "Desktop Audio",
                            "type": "wasapi_output_capture",
                            "settings": {
                                "device_id": "default"
                            }
                        }
                    ]
                }
            ]
        }
        
        # Save scene collection
        scene_file = self.config_dir / "unreal_stream.json"
        with open(scene_file, 'w') as f:
            json.dump(scene_collection, f, indent=2)
        
        return scene_file
    
    def create_profile(self, stream_server="rtmp://localhost/live", stream_key="test"):
        """Create OBS profile with streaming settings"""
        
        profile = {
            "Output": {
                "Mode": "Simple",
                "SimpleOutputPath": str(Path.home() / "Videos"),
                "SimpleOutputVideoBitrate": 6000,
                "SimpleOutputAudioBitrate": 160,
                "SimpleOutputVideoEncoder": "x264",
                "SimpleOutputStreamingServer": stream_server,
                "SimpleOutputStreamingKey": stream_key
            },
            "Video": {
                "BaseCX": 1920,
                "BaseCY": 1080,
                "OutputCX": 1920,
                "OutputCY": 1080,
                "FPSType": "Common",
                "FPSCommon": "30"
            },
            "Audio": {
                "SampleRate": 48000,
                "ChannelSetup": "Stereo",
                "Desktop1": {
                    "Enabled": True,
                    "Volume": 1.0
                },
                "Mic1": {
                    "Enabled": False,
                    "Volume": 0.0
                }
            }
        }
        
        # Save profile
        profile_file = self.config_dir / "unreal_profile.json"
        with open(profile_file, 'w') as f:
            json.dump(profile, f, indent=2)
        
        return profile_file
    
    def launch_obs(self, auto_start_stream=False, minimize_to_tray=False):
        """Launch OBS with configured settings"""
        
        if not self.obs_path:
            return False
        
        # Create configuration files
        scene_file = self.create_scene_collection()
        profile_file = self.create_profile()
        
        # Build OBS command
        cmd = [self.obs_path]
        
        if auto_start_stream:
            cmd.append("--startstreaming")
        
        if minimize_to_tray:
            cmd.append("--minimize-to-tray")
        
        cmd.extend([
            "--scene", "Unreal Stream",
            "--profile", str(profile_file),
            "--collection", str(scene_file)
        ])
        
        print(f"Launching OBS with command: {' '.join(cmd)}")
        
        try:
            subprocess.Popen(cmd)
            print("\nOBS launched successfully!")
            print("Configuration:")
            print("- Capturing: Unreal Engine window")
            print("- Audio: Desktop audio only (microphone muted)")
            print("- Resolution: 1920x1080 @ 30fps")
            print("- Bitrate: 6000 kbps")
            
            if auto_start_stream:
                print("\nStreaming will start automatically")
            else:
                print("\nTo start streaming:")
                print("1. Click 'Start Streaming' in OBS")
                print("2. Or use the hotkey (usually Ctrl+Shift+S)")
            
            return True
            
        except Exception as e:
            print(f"Error launching OBS: {e}")
            return False

def main():
    """Main function"""
    
    print("Simple OBS Launcher for Unreal Engine Streaming")
    print("=" * 50)
    
    # Check if Unreal Engine is running
    unreal_windows = [w for w in gw.getAllWindows() if 'Unreal' in w.title or 'UE4' in w.title or 'UE5' in w.title]
    
    if not unreal_windows:
        print("\nWARNING: No Unreal Engine window detected.")
        print("Please start Unreal Engine before streaming.")
        response = input("\nContinue anyway? (y/n): ")
        if response.lower() != 'y':
            return
    else:
        print(f"\nDetected Unreal Engine window: {unreal_windows[0].title}")
    
    # Create launcher
    launcher = SimpleOBSLauncher()
    
    # Get user preferences
    print("\nConfiguration:")
    auto_start = input("Auto-start streaming? (y/n): ").lower() == 'y'
    minimize = input("Minimize OBS to tray? (y/n): ").lower() == 'y'
    
    # Launch OBS
    print("\nLaunching OBS...")
    if launcher.launch_obs(auto_start_stream=auto_start, minimize_to_tray=minimize):
        print("\nOBS is now running with your Unreal Engine capture configured.")
        print("The desktop audio is being captured (microphone is muted).")
    else:
        print("\nFailed to launch OBS. Please check the installation.")

if __name__ == "__main__":
    main()