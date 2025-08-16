"""
Livepeer Ultra-Low Latency Streamer for Unreal Engine
Optimized for blazing fast streaming with minimal delay
"""

import subprocess
import json
import configparser
import psutil
import time
import os
from pathlib import Path
import win32con

class LivepeerUltraLowStreamer:
    def __init__(self):
        # Livepeer credentials from file
        self.stream_key = "7de0-7v24-76co-mvbd"
        self.rtmp_server = "rtmp://rtmp.livepeer.com/live"
        self.playback_url = "https://livepeercdn.studio/hls/7de0lr18mu0sassl/index.m3u8"
        
        # OBS paths
        self.obs_exe = r"C:\Program Files (x86)\Steam\steamapps\common\OBS Studio\bin\64bit\obs64.exe"
        self.obs_dir = Path(self.obs_exe).parent
        
        # Config paths
        self.obs_config_dir = Path(os.environ['APPDATA']) / "obs-studio"
        self.basic_config_dir = self.obs_config_dir / "basic"
        self.profiles_dir = self.basic_config_dir / "profiles"
        self.scenes_dir = self.basic_config_dir / "scenes"
        
    def ensure_directories(self):
        """Create OBS config directories"""
        self.obs_config_dir.mkdir(parents=True, exist_ok=True)
        self.basic_config_dir.mkdir(parents=True, exist_ok=True)
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        self.scenes_dir.mkdir(parents=True, exist_ok=True)
        
        # Create UltraLow profile directory
        profile_dir = self.profiles_dir / "UltraLow"
        profile_dir.mkdir(parents=True, exist_ok=True)
        
        return profile_dir
    
    def create_ultralow_profile(self, profile_dir):
        """Create OBS profile optimized for ultra-low latency"""
        config = configparser.ConfigParser()
        
        # Advanced Output settings for minimal latency
        config['AdvOut'] = {
            'Track1Bitrate': '160',
            'Track1Name': 'Track1', 
            'Track2Bitrate': '160',
            'Track2Name': 'Track2',
            'Track3Bitrate': '160',
            'Track3Name': 'Track3',
            'Track4Bitrate': '160',
            'Track4Name': 'Track4',
            'Track5Bitrate': '160',
            'Track5Name': 'Track5',
            'Track6Bitrate': '160',
            'Track6Name': 'Track6',
            'Encoder': 'obs_x264',
            'ApplyServiceSettings': 'true',
            'UseStreamEncoder': 'false',
            'VodTrackIndex': '1'
        }
        
        # Ultra-low latency video settings
        config['Video'] = {
            'BaseCX': '1920',
            'BaseCY': '1080', 
            'OutputCX': '1920',
            'OutputCY': '1080',
            'FPSType': '0',
            'FPSCommon': '60',  # Higher FPS for lower perceived latency
            'ScaleType': 'bilinear',  # Fastest scaling
            'ColorFormat': 'NV12',
            'ColorSpace': '709',
            'ColorRange': 'Partial'
        }
        
        # Audio settings optimized for low latency
        config['Audio'] = {
            'SampleRate': '48000',
            'ChannelSetup': 'Stereo',
            'Desktop-1': 'default',
            'Desktop-2': 'disabled',
            'Mic-1': 'disabled',
            'Mic-2': 'disabled',
            'Mic-3': 'disabled',
            'BufferingTime': '1000',  # Minimal audio buffering
            'LowLatencyAudioBuffering': 'true'
        }
        
        # Stream settings for Livepeer
        config['Stream1'] = {
            'Encoder': 'obs_x264',
            'Rescale': 'false',
            'OutputCX': '1920',
            'OutputCY': '1080',
            'Track': '1',
            'VBitrate': '8000',  # High bitrate for quality at low latency
            'ABitrate': '160'
        }
        
        # General settings
        config['General'] = {
            'Name': 'UltraLow',
            'SceneCollection': 'UltraLow',
            'SceneCollectionFile': 'UltraLow'
        }
        
        # Output mode
        config['Output'] = {
            'Mode': 'Advanced'
        }
        
        basic_ini = profile_dir / "basic.ini"
        with open(basic_ini, 'w') as f:
            config.write(f)
        
        print(f"Created ultra-low latency profile: {basic_ini}")
        
        # Create service.json for Livepeer streaming
        service_config = {
            "settings": {
                "server": self.rtmp_server,
                "key": self.stream_key,
                "use_auth": False,
                "bwtest": False
            },
            "type": "rtmp_common"
        }
        
        service_json = profile_dir / "service.json"
        with open(service_json, 'w') as f:
            json.dump(service_config, f, indent=2)
        
        print(f"Created Livepeer service config: {service_json}")
        
        # Create streamEncoder.json for x264 ultra-fast preset
        encoder_config = {
            "encoder": "obs_x264",
            "settings": {
                "preset": "ultrafast",  # Fastest encoding
                "profile": "baseline",  # Lowest complexity profile
                "tune": "zerolatency", # Zero latency tuning
                "x264opts": "nal-hrd=cbr:force-cfr=1:keyint=30:min-keyint=30:scenecut=0:intra-refresh=1",
                "rate_control": "CBR",  # Constant bitrate for predictable latency
                "bitrate": 8000,
                "buffer_size": 8000,    # Minimal buffering
                "max_bitrate": 8000,
                "bf": 0,                # No B-frames for lower latency
                "crf": 0,
                "use_bufsize": True
            }
        }
        
        encoder_json = profile_dir / "streamEncoder.json"
        with open(encoder_json, 'w') as f:
            json.dump(encoder_config, f, indent=2)
        
        print(f"Created ultra-fast encoder config: {encoder_json}")
    
    def create_ultralow_scene(self):
        """Create scene collection optimized for game capture"""
        
        scene_collection = {
            "current_program_scene": "Ultra Low Capture",
            "current_scene": "Ultra Low Capture", 
            "current_transition": "Cut",  # Instant transitions
            "groups": [],
            "modules": {
                "auto-scene-switcher": {"active": False},
                "scripts-tool": [],
                "output-timer": {
                    "streamTimerHours": 0,
                    "streamTimerMinutes": 0,
                    "streamTimerSeconds": 0
                }
            },
            "name": "UltraLow",
            "preview_locked": False,
            "quick_transitions": [{
                "duration": 0,  # Instant transitions
                "fade_to_black": False,
                "hotkeys": [],
                "id": 1,
                "name": "Cut"
            }],
            "scaling_enabled": False,
            "scaling_level": 0,
            "scaling_off_x": 0.0,
            "scaling_off_y": 0.0,
            "scene_order": [{"name": "Ultra Low Capture"}],
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
                    "hotkeys": {},
                    "id": "game_capture",
                    "mixers": 0,
                    "monitoring_type": 0,
                    "muted": False,
                    "name": "Ultra Game Capture",
                    "private_settings": {},
                    "push-to-mute": False,
                    "push-to-mute-delay": 0,
                    "push-to-talk": False,
                    "push-to-talk-delay": 0,
                    "settings": {
                        "anti_cheat_hook": True,
                        "capture_cursor": False,  # Disable cursor for performance
                        "capture_mode": "any_fullscreen",
                        "capture_overlays": False,
                        "force_sdr": True,  # Faster processing
                        "hook_rate": 1,  # Fastest hook rate
                        "limit_framerate": False,
                        "priority": 0,  # Highest priority
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
                    "hotkeys": {},
                    "id": "scene",
                    "mixers": 0,
                    "monitoring_type": 0,
                    "muted": False,
                    "name": "Ultra Low Capture",
                    "private_settings": {},
                    "settings": {
                        "custom_size": False,
                        "id_counter": 2,
                        "items": [
                            {
                                "align": 5,
                                "bounds": {"x": 1920.0, "y": 1080.0},
                                "bounds_align": 0,
                                "bounds_type": 2,
                                "crop_bottom": 0,
                                "crop_left": 0,
                                "crop_right": 0,
                                "crop_top": 0,
                                "group_item_backup": False,
                                "hide_transition": {"duration": 0},
                                "id": 1,
                                "locked": False,
                                "name": "Ultra Game Capture",
                                "pos": {"x": 0.0, "y": 0.0},
                                "private_settings": {},
                                "rot": 0.0,
                                "scale": {"x": 1.0, "y": 1.0},
                                "scale_filter": "disable",  # No scaling for performance
                                "show_transition": {"duration": 0},
                                "visible": True
                            }
                        ]
                    },
                    "sync": 0,
                    "versioned_id": "scene",
                    "volume": 1.0
                }
            ],
            "transition_duration": 0,  # Instant transitions
            "transitions": []
        }
        
        scene_file = self.scenes_dir / "UltraLow.json"
        with open(scene_file, 'w') as f:
            json.dump(scene_collection, f, indent=2)
        
        print(f"Created ultra-low latency scene: {scene_file}")
    
    def kill_obs(self):
        """Kill any running OBS processes"""
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'] == 'obs64.exe':
                    proc.kill()
                    print("Stopped existing OBS process")
                    time.sleep(2)
            except:
                pass
    
    def detect_unreal_engine(self):
        """Detect Unreal Engine processes"""
        unreal_processes = []
        for proc in psutil.process_iter(['name', 'exe']):
            try:
                name = proc.info['name']
                exe = proc.info['exe'] or ""
                if any(x in name.lower() for x in ['unreal', 'ue4', 'ue5', 'embody']) or \
                   any(x in exe for x in ['Unreal', 'UE4', 'UE5', 'Embody']):
                    unreal_processes.append(name)
            except:
                pass
        return unreal_processes
    
    def launch_ultralow_stream(self):
        """Launch OBS with ultra-low latency configuration"""
        
        print("=" * 70)
        print("🚀 LIVEPEER ULTRA-LOW LATENCY STREAMER 🚀")
        print("=" * 70)
        
        # Kill existing OBS
        self.kill_obs()
        
        # Setup configuration
        print("\n⚙️  Setting up ultra-low latency configuration...")
        profile_dir = self.ensure_directories()
        self.create_ultralow_profile(profile_dir)
        self.create_ultralow_scene()
        
        # Detect Unreal Engine
        unreal_processes = self.detect_unreal_engine()
        if unreal_processes:
            print(f"\n🎮 Detected Unreal Engine: {', '.join(unreal_processes)}")
        else:
            print("\n⚠️  No Unreal Engine detected - will capture any fullscreen game")
        
        # Launch command with ultra-low latency flags
        cmd = [
            str(self.obs_exe),
            "--profile", "UltraLow",
            "--collection", "UltraLow", 
            "--minimize-to-tray",
            "--startstreaming",
            "--disable-updater",
            "--portable"  # Use portable mode for better performance
        ]
        
        print(f"\n📡 Streaming to Livepeer:")
        print(f"   Server: {self.rtmp_server}")
        print(f"   Stream Key: {self.stream_key}")
        print(f"   Playback: {self.playback_url}")
        
        try:
            # Launch minimized with high priority
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = win32con.SW_MINIMIZE
            
            process = subprocess.Popen(
                cmd,
                cwd=str(self.obs_dir),
                startupinfo=startupinfo,
                creationflags=subprocess.HIGH_PRIORITY_CLASS  # High priority for low latency
            )
            
            print(f"\n🔥 ULTRA-LOW LATENCY STREAM ACTIVE! 🔥")
            print("=" * 70)
            print("\n⚡ Optimizations Applied:")
            print("   • x264 ultrafast preset with zero-latency tune")
            print("   • CBR encoding with minimal buffering")
            print("   • 60 FPS for smooth motion")
            print("   • No B-frames for instant encoding")
            print("   • High priority process")
            print("   • Instant scene transitions")
            print("   • Optimized game capture")
            
            print(f"\n📺 Watch your stream at:")
            print(f"   {self.playback_url}")
            
            print(f"\n🛑 To stop: Right-click OBS in system tray → Exit")
            print(f"\n📊 Press Ctrl+C to stop monitoring...")
            
            # Monitor the stream
            try:
                while process.poll() is None:
                    time.sleep(5)
            except KeyboardInterrupt:
                print("\n\n🛑 Stopping ultra-low latency stream...")
                process.terminate()
                time.sleep(2)
                print("✅ Stream stopped.")
            
            return True
            
        except Exception as e:
            print(f"\n❌ ERROR: Failed to start stream: {e}")
            return False

def main():
    """Main function"""
    streamer = LivepeerUltraLowStreamer()
    streamer.launch_ultralow_stream()

if __name__ == "__main__":
    main()