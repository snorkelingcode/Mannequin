"""
Headless OBS Streamer for Unreal Engine
Automatically detects and streams Unreal Engine applications running in headless mode
"""

import subprocess
import json
import psutil
import time
import os
from pathlib import Path
import win32gui
import win32con
import win32process
import ctypes
from ctypes import wintypes

class HeadlessOBSStreamer:
    def __init__(self, stream_server="rtmp://localhost/live", stream_key="test"):
        self.obs_path = r"C:\Program Files (x86)\Steam\steamapps\common\OBS Studio\bin\64bit\obs64.exe"
        self.obs_dir = Path(self.obs_path).parent
        self.config_dir = Path("obs_headless_config")
        self.config_dir.mkdir(exist_ok=True)
        self.stream_server = stream_server
        self.stream_key = stream_key
        self.obs_process = None
        
    def find_unreal_process(self):
        """Find Unreal Engine process even if headless"""
        unreal_processes = []
        
        # Common Unreal Engine process names
        unreal_names = [
            "UnrealEditor.exe",
            "UnrealEditor-Win64-Shipping.exe",
            "UE4Editor.exe",
            "UE5Editor.exe",
            "Embody.exe",
            "EmbodyEditor.exe",
            "UnrealGame.exe",
            "YourGameName.exe"  # Replace with your specific game executable
        ]
        
        for proc in psutil.process_iter(['pid', 'name', 'exe']):
            try:
                proc_name = proc.info['name']
                proc_exe = proc.info['exe'] or ""
                
                # Check if it's an Unreal process
                for unreal_name in unreal_names:
                    if unreal_name.lower() in proc_name.lower():
                        unreal_processes.append({
                            'pid': proc.info['pid'],
                            'name': proc_name,
                            'exe': proc_exe
                        })
                        break
                
                # Also check if the exe path contains Unreal/UE4/UE5
                if any(x in proc_exe for x in ['Unreal', 'UE4', 'UE5', 'Embody']):
                    if proc.info not in unreal_processes:
                        unreal_processes.append({
                            'pid': proc.info['pid'],
                            'name': proc_name,
                            'exe': proc_exe
                        })
                        
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return unreal_processes
    
    def find_unreal_window_handle(self, process_pid):
        """Find window handle for a process, even if hidden"""
        handles = []
        
        def enum_windows_callback(hwnd, param):
            if win32gui.IsWindow(hwnd):
                thread_id, process_id = win32process.GetWindowThreadProcessId(hwnd)
                if process_id == process_pid:
                    handles.append(hwnd)
            return True
        
        win32gui.EnumWindows(enum_windows_callback, None)
        return handles[0] if handles else None
    
    def create_obs_config(self, unreal_process=None):
        """Create OBS configuration file for headless streaming"""
        
        # Basic OBS settings
        config = {
            "general": {
                "portable_mode": True,
                "minimize_to_tray": True,
                "start_streaming_on_launch": True
            },
            "video": {
                "base_width": 1920,
                "base_height": 1080,
                "output_width": 1920,
                "output_height": 1080,
                "fps_num": 30,
                "fps_den": 1
            },
            "audio": {
                "desktop_audio": True,
                "mic_audio": False,
                "sample_rate": 48000
            },
            "stream": {
                "server": self.stream_server,
                "key": self.stream_key,
                "use_auth": False,
                "auto_reconnect": True,
                "auto_reconnect_timeout": 10
            },
            "output": {
                "mode": "Simple",
                "video_bitrate": 6000,
                "audio_bitrate": 160,
                "encoder": "x264"
            }
        }
        
        # Save configuration
        config_file = self.config_dir / "config.json"
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        # Create scene collection with game capture
        scene_collection = {
            "name": "Headless Stream",
            "sources": []
        }
        
        # Add game capture source if Unreal process found
        if unreal_process:
            scene_collection["sources"].append({
                "name": "Unreal Game Capture",
                "type": "game_capture",
                "settings": {
                    "capture_mode": "specific",
                    "window": f"{unreal_process['name']}:{unreal_process['exe']}",
                    "priority": 0,
                    "capture_cursor": False,
                    "allow_transparency": False,
                    "force_sdr": False,
                    "capture_overlays": True,
                    "anti_cheat_hook": True
                }
            })
        
        # Always add display capture as fallback
        scene_collection["sources"].append({
            "name": "Display Capture",
            "type": "monitor_capture",
            "settings": {
                "monitor": 0,
                "capture_cursor": True
            }
        })
        
        # Add desktop audio
        scene_collection["sources"].append({
            "name": "Desktop Audio",
            "type": "wasapi_output_capture",
            "settings": {
                "device_id": "default"
            }
        })
        
        scene_file = self.config_dir / "scenes.json"
        with open(scene_file, 'w') as f:
            json.dump(scene_collection, f, indent=2)
        
        return config_file, scene_file
    
    def create_obs_launch_args(self, config_file, scene_file, minimize=True, start_streaming=True):
        """Create OBS command line arguments for headless operation"""
        args = [
            str(self.obs_path),
            "--portable",
            "--multi",
            "--minimize-to-tray" if minimize else "",
            "--startstreaming" if start_streaming else "",
            "--profile", str(config_file.parent),
            "--collection", str(scene_file.stem),
            "--disable-updater"
        ]
        
        # Remove empty strings
        args = [arg for arg in args if arg]
        
        return args
    
    def start_headless_streaming(self, minimize=True, auto_start=True):
        """Start OBS in headless/minimized mode"""
        
        print("=" * 60)
        print("Headless OBS Streamer for Unreal Engine")
        print("=" * 60)
        
        # Find Unreal Engine process
        print("\nSearching for Unreal Engine process...")
        unreal_processes = self.find_unreal_process()
        
        if unreal_processes:
            print(f"Found {len(unreal_processes)} Unreal Engine process(es):")
            for proc in unreal_processes:
                print(f"  - {proc['name']} (PID: {proc['pid']})")
            unreal_process = unreal_processes[0]
        else:
            print("No Unreal Engine process found. Will use display capture.")
            unreal_process = None
        
        # Create configuration
        print("\nCreating OBS configuration...")
        config_file, scene_file = self.create_obs_config(unreal_process)
        
        # Create launch arguments
        args = self.create_obs_launch_args(config_file, scene_file, minimize, auto_start)
        
        # Launch OBS
        print("\nLaunching OBS in headless mode...")
        print(f"Stream Server: {self.stream_server}")
        print(f"Stream Key: {self.stream_key[:5]}..." if len(self.stream_key) > 5 else self.stream_key)
        
        try:
            # Set startup info to hide window
            startupinfo = subprocess.STARTUPINFO()
            if minimize:
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_MINIMIZE
            
            self.obs_process = subprocess.Popen(
                args,
                cwd=str(self.obs_dir),
                startupinfo=startupinfo
            )
            
            print("\n[SUCCESS] OBS launched in headless mode!")
            if auto_start:
                print("Streaming will start automatically...")
            
            return True
            
        except Exception as e:
            print(f"\n[ERROR] Failed to launch OBS: {e}")
            return False
    
    def stop_streaming(self):
        """Stop OBS streaming"""
        if self.obs_process:
            print("\nStopping OBS...")
            self.obs_process.terminate()
            self.obs_process.wait(timeout=5)
            print("OBS stopped.")
    
    def monitor_streaming(self, check_interval=5):
        """Monitor streaming status"""
        print("\nMonitoring streaming status...")
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                if self.obs_process and self.obs_process.poll() is not None:
                    print("\n[WARNING] OBS process has stopped")
                    break
                
                # Check if Unreal is still running
                unreal_processes = self.find_unreal_process()
                if not unreal_processes:
                    print("\n[WARNING] Unreal Engine process not found")
                
                time.sleep(check_interval)
                
        except KeyboardInterrupt:
            print("\n\nStopping stream...")
            self.stop_streaming()

def main():
    """Main function for headless streaming"""
    
    # Configuration - Update these values
    STREAM_SERVER = "rtmp://localhost/live"  # Your RTMP server
    STREAM_KEY = "your_stream_key_here"      # Your stream key
    
    # Create streamer
    streamer = HeadlessOBSStreamer(
        stream_server=STREAM_SERVER,
        stream_key=STREAM_KEY
    )
    
    # Start headless streaming
    if streamer.start_headless_streaming(minimize=True, auto_start=True):
        # Monitor the stream
        streamer.monitor_streaming()
    else:
        print("\nFailed to start streaming")

if __name__ == "__main__":
    main()