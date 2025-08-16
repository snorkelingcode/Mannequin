"""
OBS Stream Controller for Unreal Engine Window and PC Audio
Captures Unreal Engine window and system audio (without microphone)
"""

import obsws_python as obs
import pygetwindow as gw
import json
import time
import subprocess
import os
from pathlib import Path

class OBSStreamController:
    def __init__(self, host="localhost", port=4455, password=""):
        """Initialize OBS WebSocket connection"""
        self.host = host
        self.port = port
        self.password = password
        self.ws = None
        
    def connect(self):
        """Connect to OBS WebSocket"""
        try:
            self.ws = obs.ReqClient(host=self.host, port=self.port, password=self.password)
            print("Connected to OBS WebSocket")
            return True
        except Exception as e:
            print(f"Failed to connect to OBS: {e}")
            return False
    
    def setup_unreal_capture(self):
        """Set up window capture for Unreal Engine"""
        try:
            # Find Unreal Engine window
            unreal_windows = [w for w in gw.getAllWindows() if 'Unreal' in w.title or 'UE4' in w.title or 'UE5' in w.title]
            
            if not unreal_windows:
                print("No Unreal Engine window found. Please make sure Unreal Engine is running.")
                return False
            
            window_title = unreal_windows[0].title
            print(f"Found Unreal Engine window: {window_title}")
            
            # Create window capture source
            source_settings = {
                "capture_mode": "window",
                "window": window_title,
                "priority": 1,
                "capture_cursor": True
            }
            
            # Remove existing source if it exists
            try:
                self.ws.remove_input("UnrealEngineCapture")
            except:
                pass
            
            # Create new window capture source
            self.ws.create_input(
                scene_name="Scene",
                input_name="UnrealEngineCapture",
                input_kind="window_capture",
                input_settings=source_settings,
                scene_item_enabled=True
            )
            
            print("Unreal Engine window capture source created")
            return True
            
        except Exception as e:
            print(f"Error setting up Unreal capture: {e}")
            return False
    
    def setup_audio_capture(self):
        """Set up audio capture for desktop audio (no microphone)"""
        try:
            # Create desktop audio source
            audio_settings = {
                "device_id": "default"
            }
            
            # Remove existing audio sources if they exist
            try:
                self.ws.remove_input("DesktopAudio")
                self.ws.remove_input("MicrophoneAudio")
            except:
                pass
            
            # Create desktop audio source
            self.ws.create_input(
                scene_name="Scene",
                input_name="DesktopAudio",
                input_kind="wasapi_output_capture",
                input_settings=audio_settings,
                scene_item_enabled=True
            )
            
            # Mute microphone if it exists
            try:
                self.ws.set_input_mute("Mic/Aux", True)
            except:
                pass
            
            print("Desktop audio capture configured (microphone muted)")
            return True
            
        except Exception as e:
            print(f"Error setting up audio capture: {e}")
            return False
    
    def configure_stream_settings(self, stream_key, server="rtmp://localhost/live"):
        """Configure streaming settings"""
        try:
            stream_settings = {
                "server": server,
                "key": stream_key,
                "use_auth": False
            }
            
            self.ws.set_stream_service_settings(
                stream_service_type="rtmp_common",
                stream_service_settings=stream_settings
            )
            
            # Set output settings for good quality
            video_settings = {
                "base_width": 1920,
                "base_height": 1080,
                "output_width": 1920,
                "output_height": 1080,
                "fps_numerator": 30,
                "fps_denominator": 1
            }
            
            self.ws.set_video_settings(video_settings)
            
            print(f"Stream configured to: {server}")
            return True
            
        except Exception as e:
            print(f"Error configuring stream: {e}")
            return False
    
    def start_streaming(self):
        """Start streaming"""
        try:
            self.ws.start_stream()
            print("Streaming started")
            return True
        except Exception as e:
            print(f"Error starting stream: {e}")
            return False
    
    def stop_streaming(self):
        """Stop streaming"""
        try:
            self.ws.stop_stream()
            print("Streaming stopped")
            return True
        except Exception as e:
            print(f"Error stopping stream: {e}")
            return False
    
    def start_recording(self, output_path=None):
        """Start recording"""
        try:
            if output_path:
                self.ws.set_record_directory(output_path)
            self.ws.start_record()
            print(f"Recording started{' to ' + output_path if output_path else ''}")
            return True
        except Exception as e:
            print(f"Error starting recording: {e}")
            return False
    
    def stop_recording(self):
        """Stop recording"""
        try:
            self.ws.stop_record()
            print("Recording stopped")
            return True
        except Exception as e:
            print(f"Error stopping recording: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from OBS"""
        if self.ws:
            self.ws.disconnect()
            print("Disconnected from OBS")

def main():
    """Main function to set up and control OBS streaming"""
    
    # Configuration
    OBS_PASSWORD = ""  # Set your OBS WebSocket password if configured
    STREAM_KEY = "your_stream_key_here"  # Replace with your actual stream key
    STREAM_SERVER = "rtmp://localhost/live"  # Replace with your streaming server
    
    # Create controller
    controller = OBSStreamController(password=OBS_PASSWORD)
    
    # Connect to OBS
    if not controller.connect():
        print("Please make sure OBS is running and WebSocket is enabled.")
        print("To enable WebSocket in OBS:")
        print("1. Go to Tools -> WebSocket Server Settings")
        print("2. Enable WebSocket server")
        print("3. Set a password if desired")
        return
    
    try:
        # Set up sources
        print("\nSetting up capture sources...")
        controller.setup_unreal_capture()
        controller.setup_audio_capture()
        
        # Configure stream
        print("\nConfiguring stream settings...")
        controller.configure_stream_settings(STREAM_KEY, STREAM_SERVER)
        
        # Start streaming
        print("\nStarting stream...")
        controller.start_streaming()
        
        print("\n" + "="*50)
        print("STREAMING ACTIVE")
        print("="*50)
        print("Unreal Engine window and desktop audio are being streamed")
        print("Microphone is muted")
        print("\nPress Ctrl+C to stop streaming")
        
        # Keep running until interrupted
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\nStopping stream...")
        controller.stop_streaming()
        
    finally:
        controller.disconnect()

if __name__ == "__main__":
    main()