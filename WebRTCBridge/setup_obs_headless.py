"""
Setup OBS for Headless Unreal Engine Streaming
Configures OBS settings files directly for automatic headless operation
"""

import json
import os
from pathlib import Path
import configparser
import subprocess
import psutil
import time
import win32con

class OBSHeadlessSetup:
    def __init__(self):
        # OBS paths
        self.obs_exe = r"C:\Program Files (x86)\Steam\steamapps\common\OBS Studio\bin\64bit\obs64.exe"
        self.obs_dir = Path(self.obs_exe).parent
        
        # OBS config paths (AppData)
        self.obs_config_dir = Path(os.environ['APPDATA']) / "obs-studio"
        self.basic_config_dir = self.obs_config_dir / "basic"
        self.profiles_dir = self.basic_config_dir / "profiles"
        self.scenes_dir = self.basic_config_dir / "scenes"
        
    def ensure_directories(self):
        """Create OBS config directories if they don't exist"""
        self.obs_config_dir.mkdir(parents=True, exist_ok=True)
        self.basic_config_dir.mkdir(parents=True, exist_ok=True)
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        self.scenes_dir.mkdir(parents=True, exist_ok=True)
        
        # Create Headless profile directory
        headless_profile = self.profiles_dir / "Headless"
        headless_profile.mkdir(parents=True, exist_ok=True)
        
        return headless_profile
    
    def create_global_config(self):
        """Create global.ini for OBS"""
        config = configparser.ConfigParser()
        
        config['General'] = {
            'FirstRun': 'true',
            'LastVersion': '30.0.0',
            'EnableAutoUpdates': 'false',
            'ConfirmOnExit': 'false',
            'MinimizeToTray': 'true',
            'StartMinimized': 'true'
        }
        
        config['BasicWindow'] = {
            'geometry': '',
            'DockState': ''
        }
        
        global_ini = self.obs_config_dir / "global.ini"
        with open(global_ini, 'w') as f:
            config.write(f)
        
        print(f"Created global config: {global_ini}")
    
    def create_profile_config(self, profile_dir, stream_server="rtmp://localhost/live", stream_key="test"):
        """Create basic.ini for streaming profile"""
        config = configparser.ConfigParser()
        
        # Output settings
        config['SimpleOutput'] = {
            'StreamEncoder': 'x264',
            'FilePath': str(Path.home() / "Videos"),
            'RecFormat': 'mp4',
            'VBitrate': '6000',
            'ABitrate': '160',
            'UseAdvanced': 'false',
            'Preset': 'veryfast',
            'RecQuality': 'Small',
            'RecEncoder': 'x264'
        }
        
        # Video settings
        config['Video'] = {
            'BaseCX': '1920',
            'BaseCY': '1080',
            'OutputCX': '1920',
            'OutputCY': '1080',
            'FPSType': '0',
            'FPSCommon': '30',
            'ScaleType': 'bicubic',
            'ColorFormat': 'NV12',
            'ColorSpace': '709',
            'ColorRange': 'Partial'
        }
        
        # Audio settings
        config['Audio'] = {
            'SampleRate': '48000',
            'ChannelSetup': 'Stereo',
            'Desktop-1': 'default',
            'Desktop-2': 'disabled',
            'Mic-1': 'disabled',
            'Mic-2': 'disabled',
            'Mic-3': 'disabled'
        }
        
        basic_ini = profile_dir / "basic.ini"
        with open(basic_ini, 'w') as f:
            config.write(f)
        
        print(f"Created profile config: {basic_ini}")
        
        # Create service.json for streaming settings
        service_config = {
            "settings": {
                "server": stream_server,
                "key": stream_key,
                "use_auth": False,
                "bwtest": False
            },
            "type": "rtmp_common"
        }
        
        service_json = profile_dir / "service.json"
        with open(service_json, 'w') as f:
            json.dump(service_config, f, indent=2)
        
        print(f"Created service config: {service_json}")
    
    def create_scene_collection(self):
        """Create scene collection with game and display capture"""
        
        scene_collection = {
            "current_program_scene": "Headless Capture",
            "current_scene": "Headless Capture",
            "current_transition": "Fade",
            "groups": [],
            "modules": {
                "auto-scene-switcher": {
                    "active": False
                },
                "scripts-tool": [],
                "output-timer": {
                    "streamTimerHours": 0,
                    "streamTimerMinutes": 0,
                    "streamTimerSeconds": 0,
                    "recordTimerHours": 0,
                    "recordTimerMinutes": 0,
                    "recordTimerSeconds": 0
                }
            },
            "name": "Headless",
            "preview_locked": False,
            "quick_transitions": [
                {
                    "duration": 300,
                    "fade_to_black": False,
                    "hotkeys": [],
                    "id": 1,
                    "name": "Cut"
                }
            ],
            "scaling_enabled": False,
            "scaling_level": 0,
            "scaling_off_x": 0.0,
            "scaling_off_y": 0.0,
            "scene_order": [
                {
                    "name": "Headless Capture"
                }
            ],
            "sources": [
                {
                    "balance": 0.5,
                    "deinterlace_field_order": 0,
                    "deinterlace_mode": 0,
                    "enabled": True,
                    "filters": [],
                    "hotkeys": {},
                    "id": "wasapi_output_capture",
                    "mixers": 255,
                    "monitoring_type": 0,
                    "muted": False,
                    "name": "Desktop Audio",
                    "private_settings": {},
                    "push-to-mute": False,
                    "push-to-mute-delay": 0,
                    "push-to-talk": False,
                    "push-to-talk-delay": 0,
                    "settings": {
                        "device_id": "default"
                    },
                    "sync": 0,
                    "versioned_id": "wasapi_output_capture",
                    "volume": 1.0
                },
                {
                    "balance": 0.5,
                    "deinterlace_field_order": 0,
                    "deinterlace_mode": 0,
                    "enabled": True,
                    "filters": [],
                    "hotkeys": {
                        "libobs.show_scene_item.Game Capture": [],
                        "libobs.hide_scene_item.Game Capture": []
                    },
                    "id": "game_capture",
                    "mixers": 0,
                    "monitoring_type": 0,
                    "muted": False,
                    "name": "Game Capture",
                    "private_settings": {},
                    "push-to-mute": False,
                    "push-to-mute-delay": 0,
                    "push-to-talk": False,
                    "push-to-talk-delay": 0,
                    "settings": {
                        "anti_cheat_hook": True,
                        "capture_cursor": True,
                        "capture_mode": "any_fullscreen",
                        "capture_overlays": False,
                        "force_sdr": False,
                        "hook_rate": 1,
                        "limit_framerate": False,
                        "priority": 0,
                        "sli_compatibility": False
                    },
                    "sync": 0,
                    "versioned_id": "game_capture",
                    "volume": 1.0
                },
                {
                    "balance": 0.5,
                    "deinterlace_field_order": 0,
                    "deinterlace_mode": 0,
                    "enabled": True,
                    "filters": [],
                    "hotkeys": {
                        "libobs.show_scene_item.Display Capture": [],
                        "libobs.hide_scene_item.Display Capture": []
                    },
                    "id": "monitor_capture",
                    "mixers": 0,
                    "monitoring_type": 0,
                    "muted": False,
                    "name": "Display Capture",
                    "private_settings": {},
                    "push-to-mute": False,
                    "push-to-mute-delay": 0,
                    "push-to-talk": False,
                    "push-to-talk-delay": 0,
                    "settings": {
                        "capture_cursor": True,
                        "monitor": 0
                    },
                    "sync": 0,
                    "versioned_id": "monitor_capture",
                    "volume": 1.0
                },
                {
                    "balance": 0.5,
                    "deinterlace_field_order": 0,
                    "deinterlace_mode": 0,
                    "enabled": True,
                    "filters": [],
                    "hotkeys": {},
                    "id": "scene",
                    "mixers": 0,
                    "monitoring_type": 0,
                    "muted": False,
                    "name": "Headless Capture",
                    "private_settings": {},
                    "push-to-mute": False,
                    "push-to-mute-delay": 0,
                    "push-to-talk": False,
                    "push-to-talk-delay": 0,
                    "settings": {
                        "custom_size": False,
                        "id_counter": 3,
                        "items": [
                            {
                                "align": 5,
                                "bounds": {
                                    "x": 1920.0,
                                    "y": 1080.0
                                },
                                "bounds_align": 0,
                                "bounds_type": 2,
                                "crop_bottom": 0,
                                "crop_left": 0,
                                "crop_right": 0,
                                "crop_top": 0,
                                "group_item_backup": False,
                                "hide_transition": {
                                    "duration": 0
                                },
                                "id": 1,
                                "locked": False,
                                "name": "Game Capture",
                                "pos": {
                                    "x": 0.0,
                                    "y": 0.0
                                },
                                "private_settings": {},
                                "rot": 0.0,
                                "scale": {
                                    "x": 1.0,
                                    "y": 1.0
                                },
                                "scale_filter": "disable",
                                "show_transition": {
                                    "duration": 0
                                },
                                "visible": True
                            },
                            {
                                "align": 5,
                                "bounds": {
                                    "x": 1920.0,
                                    "y": 1080.0
                                },
                                "bounds_align": 0,
                                "bounds_type": 2,
                                "crop_bottom": 0,
                                "crop_left": 0,
                                "crop_right": 0,
                                "crop_top": 0,
                                "group_item_backup": False,
                                "hide_transition": {
                                    "duration": 0
                                },
                                "id": 2,
                                "locked": False,
                                "name": "Display Capture",
                                "pos": {
                                    "x": 0.0,
                                    "y": 0.0
                                },
                                "private_settings": {},
                                "rot": 0.0,
                                "scale": {
                                    "x": 1.0,
                                    "y": 1.0
                                },
                                "scale_filter": "disable",
                                "show_transition": {
                                    "duration": 0
                                },
                                "visible": False
                            }
                        ]
                    },
                    "sync": 0,
                    "versioned_id": "scene",
                    "volume": 1.0
                }
            ],
            "transition_duration": 300,
            "transitions": []
        }
        
        scene_file = self.scenes_dir / "Headless.json"
        with open(scene_file, 'w') as f:
            json.dump(scene_collection, f, indent=2)
        
        print(f"Created scene collection: {scene_file}")
        
        # Update basic.ini to use this scene collection
        basic_ini = self.basic_config_dir / "basic.ini"
        if basic_ini.exists():
            config = configparser.ConfigParser()
            config.read(basic_ini)
            config['General'] = {
                'Name': 'Headless',
                'SceneCollection': 'Headless',
                'SceneCollectionFile': 'Headless'
            }
            with open(basic_ini, 'w') as f:
                config.write(f)
    
    def kill_obs_if_running(self):
        """Kill any running OBS processes"""
        killed = False
        for proc in psutil.process_iter(['name']):
            if proc.info['name'] == 'obs64.exe':
                proc.kill()
                killed = True
                print("Killed existing OBS process")
        
        if killed:
            time.sleep(2)  # Wait for process to fully terminate
    
    def launch_obs_headless(self):
        """Launch OBS in headless mode"""
        print("\nLaunching OBS in headless mode...")
        
        # Create launch command
        cmd = [
            str(self.obs_exe),
            "--profile", "Headless",
            "--collection", "Headless",
            "--minimize-to-tray",
            "--startstreaming",
            "--disable-updater"
        ]
        
        # Launch minimized
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = win32con.SW_MINIMIZE
        
        try:
            process = subprocess.Popen(
                cmd,
                cwd=str(self.obs_dir),
                startupinfo=startupinfo
            )
            
            print("[SUCCESS] OBS launched in headless mode!")
            print("OBS is running minimized in the system tray")
            print("Streaming should start automatically")
            
            return process
            
        except Exception as e:
            print(f"[ERROR] Failed to launch OBS: {e}")
            return None

def main():
    """Main setup function"""
    
    print("=" * 60)
    print("OBS Headless Setup for Unreal Engine")
    print("=" * 60)
    
    # Livepeer Configuration
    STREAM_SERVER = "rtmp://rtmp.livepeer.com/live"
    STREAM_KEY = "7de0-7v24-76co-mvbd"
    
    setup = OBSHeadlessSetup()
    
    # Kill any running OBS
    setup.kill_obs_if_running()
    
    # Create directories
    print("\nSetting up OBS configuration...")
    profile_dir = setup.ensure_directories()
    
    # Create configs
    setup.create_global_config()
    setup.create_profile_config(profile_dir, STREAM_SERVER, STREAM_KEY)
    setup.create_scene_collection()
    
    print("\nConfiguration complete!")
    
    # Launch OBS
    obs_process = setup.launch_obs_headless()
    
    if obs_process:
        print("\n" + "=" * 60)
        print("OBS is now streaming in headless mode!")
        print("=" * 60)
        print("\nCapture sources configured:")
        print("1. Game Capture - Will auto-detect Unreal/games")
        print("2. Display Capture - Fallback capture method")
        print("3. Desktop Audio - System audio (no mic)")
        print("\nTo stop: Look for OBS icon in system tray")
        print("\nPress Ctrl+C to stop monitoring...")
        
        try:
            while obs_process.poll() is None:
                time.sleep(5)
        except KeyboardInterrupt:
            print("\n\nStopping OBS...")
            obs_process.terminate()
            obs_process.wait(timeout=5)
            print("OBS stopped.")

if __name__ == "__main__":
    main()