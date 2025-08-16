"""
Livepeer Low-Latency Configuration Generator
Creates optimized OBS settings for minimal streaming delay to Livepeer
"""

import json
import configparser
from pathlib import Path
import os

def create_livepeer_lowlatency_config():
    """Create ultra-optimized OBS configuration for Livepeer streaming"""
    
    # Livepeer credentials
    STREAM_KEY = "7de0-7v24-76co-mvbd"
    RTMP_SERVER = "rtmp://rtmp.livepeer.com/live"
    PLAYBACK_URL = "https://livepeercdn.studio/hls/7de0lr18mu0sassl/index.m3u8"
    
    # OBS config directory
    obs_config_dir = Path(os.environ['APPDATA']) / "obs-studio"
    basic_config_dir = obs_config_dir / "basic"
    
    # Ensure directories exist
    obs_config_dir.mkdir(parents=True, exist_ok=True)
    basic_config_dir.mkdir(parents=True, exist_ok=True)
    
    print("[CONFIG] Creating Livepeer ultra-low latency configuration...")
    
    # Create global.ini with performance optimizations
    global_config = configparser.ConfigParser()
    global_config['General'] = {
        'FirstRun': 'false',
        'LastVersion': '30.0.0',
        'EnableAutoUpdates': 'false',
        'ConfirmOnExit': 'false',
        'MinimizeToTray': 'true',
        'StartMinimized': 'true',
        'ProcessPriority': 'High',
        'EnableNewSocketLoop': 'true',
        'LowLatencyEnable': 'true'
    }
    
    global_ini = obs_config_dir / "global.ini"
    with open(global_ini, 'w') as f:
        global_config.write(f)
    print(f"[OK] Created global config: {global_ini}")
    
    # Create basic.ini with ultra-low latency settings
    basic_config = configparser.ConfigParser()
    
    # Advanced output settings
    basic_config['AdvOut'] = {
        'Track1Bitrate': '160',
        'Track1Name': 'Track1',
        'ApplyServiceSettings': 'true',
        'UseStreamEncoder': 'false',
        'VodTrackIndex': '1',
        'Encoder': 'obs_x264',
        'RecTracks': '1',
        'RecFormat': 'mp4',
        'RecMuxerCustom': '',
        'RecRB': 'false',
        'RecRBTime': '20',
        'RecRBSize': '512',
        'RecSplit': 'false',
        'RecSplitTime': '15',
        'RecSplitSize': '2048'
    }
    
    # Video settings optimized for low latency
    basic_config['Video'] = {
        'BaseCX': '1920',
        'BaseCY': '1080',
        'OutputCX': '1920', 
        'OutputCY': '1080',
        'FPSType': '0',
        'FPSCommon': '60',  # 60 FPS for lower perceived latency
        'ScaleType': 'bilinear',  # Fastest scaling algorithm
        'ColorFormat': 'NV12',
        'ColorSpace': '709',
        'ColorRange': 'Partial'
    }
    
    # Audio settings with minimal latency
    basic_config['Audio'] = {
        'SampleRate': '48000',
        'ChannelSetup': 'Stereo',
        'Desktop-1': 'default',
        'Desktop-2': 'disabled',
        'Mic-1': 'disabled',
        'Mic-2': 'disabled',
        'Mic-3': 'disabled',
        'BufferingTime': '1000',  # Minimal buffering
        'LowLatencyAudioBuffering': 'true'
    }
    
    # Stream encoder settings for ultra-low latency
    basic_config['Stream1'] = {
        'Encoder': 'obs_x264',
        'Rescale': 'false',
        'OutputCX': '1920',
        'OutputCY': '1080', 
        'Track': '1',
        'VBitrate': '6000',  # High bitrate for quality
        'ABitrate': '160'
    }
    
    # Output mode
    basic_config['Output'] = {
        'Mode': 'Advanced'
    }
    
    # General settings
    basic_config['General'] = {
        'Name': 'Livepeer-UltraLow',
        'ConfigOnNewProfile': 'false'
    }
    
    basic_ini = basic_config_dir / "basic.ini"
    with open(basic_ini, 'w') as f:
        basic_config.write(f)
    print(f"[OK] Created basic config: {basic_ini}")
    
    # Create service.json for Livepeer
    service_config = {
        "settings": {
            "server": RTMP_SERVER,
            "key": STREAM_KEY,
            "use_auth": False,
            "bwtest": False
        },
        "type": "rtmp_common"
    }
    
    service_json = basic_config_dir / "service.json"
    with open(service_json, 'w') as f:
        json.dump(service_config, f, indent=2)
    print(f"[OK] Created service config: {service_json}")
    
    # Create streamEncoder.json with zero-latency x264 settings
    encoder_config = {
        "encoder": "obs_x264",
        "settings": {
            "preset": "ultrafast",      # Fastest encoding preset
            "profile": "baseline",      # Lowest complexity profile
            "tune": "zerolatency",     # Zero latency tuning
            "x264opts": "nal-hrd=cbr:force-cfr=1:keyint=60:min-keyint=60:scenecut=0:intra-refresh=1:ref=1:bframes=0:direct=spatial:weightp=0:me=dia:subme=1:analyse=none:trellis=0:no-fast-pskip=0:8x8dct=0",
            "rate_control": "CBR",      # Constant bitrate
            "bitrate": 6000,
            "buffer_size": 6000,       # 1:1 buffer ratio for minimal delay
            "max_bitrate": 6000,
            "bf": 0,                   # No B-frames
            "crf": 0,
            "use_bufsize": True,
            "cpu_usage_preset": "ultrafast"
        }
    }
    
    encoder_json = basic_config_dir / "streamEncoder.json"
    with open(encoder_json, 'w') as f:
        json.dump(encoder_config, f, indent=2)
    print(f"[OK] Created encoder config: {encoder_json}")
    
    print(f"\n[SUCCESS] Livepeer Ultra-Low Latency Configuration Complete!")
    print(f"RTMP Server: {RTMP_SERVER}")
    print(f"Stream Key: {STREAM_KEY}")
    print(f"Playback URL: {PLAYBACK_URL}")
    print(f"\nOptimizations Applied:")
    print(f"   - x264 ultrafast preset with zero-latency tune")
    print(f"   - CBR encoding with 1:1 buffer ratio")
    print(f"   - 60 FPS for smooth motion")
    print(f"   - No B-frames for instant encoding")
    print(f"   - Minimal audio buffering")
    print(f"   - High process priority")
    print(f"   - Optimized scaling and color format")
    
    return PLAYBACK_URL

if __name__ == "__main__":
    playback_url = create_livepeer_lowlatency_config()
    print(f"\n[READY] Stream ready! Watch at: {playback_url}")