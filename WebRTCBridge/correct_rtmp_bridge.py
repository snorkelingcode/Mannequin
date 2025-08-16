#!/usr/bin/env python3
"""
Correct RTMP Bridge - Production-Ready Unreal Engine to Livepeer Stream
Bulletproof reliability with latency optimization and fixed success rate calculation
Based on WebRTCBridgeComponent.cpp UDP format analysis
"""

import time
import logging
import subprocess
import socket
import struct
import threading
import queue
from dataclasses import dataclass
import sys

# Configure production-grade logging with UTF-8 encoding
# Create UTF-8 compatible stream handler
import io

utf8_stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(utf8_stdout),
        logging.FileHandler('streaming_performance.log', mode='a', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class LivepeerConfig:
    """Livepeer streaming configuration"""
    api_key: str = "3d0131d4-836b-4d4b-b695-83cab4144f1b"
    stream_key: str = "7de0-7v24-76co-mvbd"
    stream_id: str = "7de094b8-3fbe-4b16-ac75-594556d39b18"
    playback_id: str = "7de0lr18mu0sassl"
    rtmp_url: str = "rtmp://rtmp.livepeer.com/live"

class ProductionFrameReceiver:
    """Production-grade UDP frame receiver with bulletproof reliability"""
    
    def __init__(self, port=5000):
        self.port = port
        self.socket = None
        self.running = False
        self.frame_queue = queue.Queue(maxsize=50)  # Optimized queue size
        self.receive_thread = None
        
        # Frame reconstruction for chunked UDP packets
        self.incomplete_frames = {}
        self.frame_timeout = 1.0  # Balanced timeout for reliability vs latency
        self.last_cleanup = time.time()
        self.max_incomplete_frames = 200  # Higher limit but still controlled
        
        # Statistics tracking
        self.frames_received = 0
        self.packets_received = 0
        self.frames_completed = 0
        self.frames_dropped = 0
        
        # Jitter reduction - frame timing control
        self.last_frame_output_time = 0
        self.target_frame_interval = 1.0 / 20.0  # 20fps target for ultra-stability
        self.frame_buffer = []  # Small buffer for smoothing
        self.max_buffer_size = 3  # 3-frame buffer
        
    def start(self):
        """Start bulletproof frame receiver"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.bind(('localhost', self.port))
            self.socket.settimeout(0.1)  # Non-blocking with short timeout
            
            self.running = True
            self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.receive_thread.start()
            
            logger.info(f"Production frame receiver started on port {self.port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start frame receiver: {e}")
            return False
    
    def _receive_loop(self):
        """Main frame receiving loop with bulletproof error handling"""
        logger.info("Frame receive loop started")
        
        while self.running:
            try:
                data, addr = self.socket.recvfrom(65536)
                self.packets_received += 1
                
                if len(data) >= 8:
                    self._process_packet(data)
                    
                # Cleanup expired frames to prevent latency buildup
                current_time = time.time()
                if current_time - self.last_cleanup > 0.5:  # Clean every 500ms
                    self._cleanup_incomplete_frames(current_time)
                    self.last_cleanup = current_time
                    
            except socket.timeout:
                continue  # Normal operation
            except Exception as e:
                if self.running:
                    logger.error(f"Frame receive error: {e}")
                    # Don't break - keep trying for bulletproof reliability
                    time.sleep(0.0001)  # Reduced sleep for lower latency
        
        logger.info("Frame receive loop stopped")
    
    def _process_packet(self, data):
        """Process UDP packet and reconstruct JPEG frame"""
        try:
            # Parse Unreal Engine UDP format: [uint32 frame_id][uint8 total_chunks][uint8 chunk_index][uint16 payload_size][payload]
            frame_id = struct.unpack('!I', data[0:4])[0]
            total_chunks = data[4]
            chunk_index = data[5]
            payload_size = struct.unpack('!H', data[6:8])[0]
            
            if len(data) < 8 + payload_size:
                return
                
            payload = data[8:8+payload_size]
            
            # Initialize frame tracking
            if frame_id not in self.incomplete_frames:
                # Aggressive cleanup if too many incomplete frames (prevents latency buildup)
                if len(self.incomplete_frames) >= self.max_incomplete_frames:
                    self._aggressive_cleanup()
                
                self.incomplete_frames[frame_id] = {
                    'chunks': {},
                    'total_chunks': total_chunks,
                    'timestamp': time.time()
                }
            
            frame_info = self.incomplete_frames[frame_id]
            frame_info['chunks'][chunk_index] = payload
            
            # Check if frame is complete
            if len(frame_info['chunks']) == frame_info['total_chunks']:
                complete_frame = bytearray()
                for i in range(frame_info['total_chunks']):
                    if i in frame_info['chunks']:
                        complete_frame.extend(frame_info['chunks'][i])
                    else:
                        # Missing chunk - drop frame
                        del self.incomplete_frames[frame_id]
                        self.frames_dropped += 1
                        return
                
                # Validate JPEG integrity
                if len(complete_frame) >= 2 and complete_frame[0] == 0xFF and complete_frame[1] == 0xD8:
                    try:
                        self.frame_queue.put_nowait(bytes(complete_frame))
                        self.frames_completed += 1
                    except queue.Full:
                        # Replace oldest frame for flow control
                        try:
                            self.frame_queue.get_nowait()
                            self.frame_queue.put_nowait(bytes(complete_frame))
                        except queue.Empty:
                            pass
                else:
                    logger.warning(f"Invalid JPEG frame {frame_id}")
                    self.frames_dropped += 1
                
                del self.incomplete_frames[frame_id]
                
        except Exception as e:
            logger.error(f"Packet processing error: {e}")
    
    def _cleanup_incomplete_frames(self, current_time):
        """Remove expired incomplete frames"""
        expired = [fid for fid, info in self.incomplete_frames.items() 
                  if current_time - info['timestamp'] > self.frame_timeout]
        for frame_id in expired:
            del self.incomplete_frames[frame_id]
            self.frames_dropped += 1
    
    def _aggressive_cleanup(self):
        """Aggressive cleanup to prevent latency buildup"""
        # Sort by timestamp and keep only the newest frames
        if len(self.incomplete_frames) >= self.max_incomplete_frames:
            sorted_frames = sorted(
                self.incomplete_frames.items(), 
                key=lambda x: x[1]['timestamp'], 
                reverse=True
            )
            
            # Keep only the newest 75% of frames (less aggressive)
            frames_to_keep = sorted_frames[:int(self.max_incomplete_frames * 0.75)]
            frames_to_drop = len(self.incomplete_frames) - len(frames_to_keep)
            
            # Clear and rebuild with only recent frames
            self.incomplete_frames.clear()
            for frame_id, frame_info in frames_to_keep:
                self.incomplete_frames[frame_id] = frame_info
            
            self.frames_dropped += frames_to_drop
            logger.debug(f"Aggressive cleanup: dropped {frames_to_drop} incomplete frames")
    
    def get_frame(self, timeout=0.001):
        """Get next complete frame with jitter reduction pacing"""
        try:
            # Fill buffer first
            while len(self.frame_buffer) < self.max_buffer_size:
                try:
                    frame = self.frame_queue.get_nowait()
                    if frame:
                        self.frame_buffer.append(frame)
                except queue.Empty:
                    break
            
            # Return frames at consistent intervals
            current_time = time.time()
            if self.last_frame_output_time > 0:
                elapsed = current_time - self.last_frame_output_time
                if elapsed < self.target_frame_interval:
                    # Wait for exact timing - ultra-stable 20fps
                    sleep_time = self.target_frame_interval - elapsed
                    if sleep_time > 0:
                        time.sleep(min(sleep_time, 0.01))  # Reduced max delay to 10ms
                        
            # Output buffered frame for smooth delivery
            if self.frame_buffer:
                frame = self.frame_buffer.pop(0)
                self.last_frame_output_time = time.time()
                self.frames_received += 1
                return frame
                
            return None
            
        except queue.Empty:
            return None
    
    def get_statistics(self):
        """Get receiver statistics with accurate success rate"""
        # Calculate accurate success rate based on frames completed vs total frames attempted
        total_frames_attempted = self.frames_completed + self.frames_dropped
        if total_frames_attempted > 0:
            accurate_success_rate = (self.frames_completed / total_frames_attempted) * 100
        else:
            accurate_success_rate = 100.0  # No frames attempted yet
            
        return {
            'packets_received': self.packets_received,
            'frames_completed': self.frames_completed,
            'frames_received': self.frames_received,
            'frames_dropped': self.frames_dropped,
            'incomplete_frames': len(self.incomplete_frames),
            'success_rate': accurate_success_rate,
            'total_frames_attempted': total_frames_attempted
        }
    
    def stop(self):
        """Stop frame receiver"""
        self.running = False
        if self.socket:
            self.socket.close()
        if self.receive_thread:
            self.receive_thread.join(timeout=2)
        logger.info(f"Frame receiver stopped - Stats: {self.get_statistics()}")

class OptimizedRTMPStreamer:
    """Production-grade RTMP streamer with RTMP connection monitoring and audio support"""
    
    def __init__(self, rtmp_url, enable_audio=False):
        self.rtmp_url = rtmp_url
        self.process = None
        self.running = False
        self.enable_audio = enable_audio
        self.audio_device = None
        
        # Statistics
        self.frames_sent = 0
        self.frames_failed = 0
        self.start_time = time.time()
        
        # RTMP connection monitoring
        self.stderr_thread = None
        self.connection_alive = True
        self.last_rtmp_error = None
        
        # Frame timing for sync
        self.stream_start_time = None
        self.frame_number = 0
        
    def _select_audio_device(self):
        """Select audio device using DirectShow (since WASAPI not available)"""
        try:
            # List DirectShow audio devices
            cmd = ['ffmpeg', '-hide_banner', '-f', 'dshow', '-list_devices', 'true', '-i', 'dummy']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            
            audio_devices = []
            output = result.stderr
            
            for line in output.split('\n'):
                if '(audio)' in line and '"' in line:
                    start = line.find('"') + 1
                    end = line.find('"', start)
                    if start > 0 and end > start:
                        device_name = line[start:end]
                        audio_devices.append(device_name)
                        logger.info(f"Found DirectShow audio device: {device_name}")
            
            # Priority order - looking for output devices, avoiding input devices
            # Check for Realtek output devices first, then others, avoid microphones
            priority_keywords = [
                ('speakers', 'Speakers'),               # Speakers/output devices
                ('headphones', 'Headphones'),          # Headphone output
                ('realtek', 'Realtek Audio'),          # Any Realtek device
                ('stereo mix', 'Stereo Mix')           # System audio mix (last resort)
            ]
            
            # Exclude these input device keywords
            exclude_keywords = ['microphone', 'mic', 'analogue 1', 'analogue 2', 'input']
            
            for keyword, display_name in priority_keywords:
                for device in audio_devices:
                    device_lower = device.lower()
                    if keyword in device_lower:
                        # Skip if it's an input device
                        if any(exclude in device_lower for exclude in exclude_keywords):
                            logger.info(f"AUDIO: Skipping input device: {device}")
                            continue
                        
                        # Test if device works
                        test_cmd = ['ffmpeg', '-hide_banner', '-f', 'dshow', 
                                  '-i', f'audio={device}', '-t', '0.1', '-f', 'null', '-']
                        try:
                            test_result = subprocess.run(test_cmd, capture_output=True, timeout=3)
                            if test_result.returncode == 0:
                                logger.info(f"AUDIO: Selected DirectShow device: {device}")
                                if 'stereo mix' in device_lower:
                                    logger.warning("WARNING: Using Stereo Mix - may cause echo with speakers!")
                                    logger.info("TIP: Use headphones to avoid echo")
                                else:
                                    logger.info("AUDIO: Using output device (should avoid echo)")
                                return device
                        except Exception as e:
                            logger.warning(f"Device test failed for {device}: {e}")
                            continue
            
            # If no suitable device found
            if audio_devices:
                logger.warning(f"No suitable audio output device found, available devices:")
                for device in audio_devices:
                    logger.warning(f"  - {device}")
                return None
            
            logger.error("ERROR: No DirectShow audio devices found!")
            return None
            
        except Exception as e:
            logger.error(f"Error selecting audio device: {e}")
            return None
        
    def start(self):
        """Start optimized FFmpeg RTMP stream with optional audio"""
        logger.info(f"Starting optimized RTMP stream to: {self.rtmp_url} (audio: {self.enable_audio})")
        
        # Build FFmpeg command with or without audio
        cmd = self._build_ffmpeg_command()
        
        try:
            self.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0  # Unbuffered for minimum latency
            )
            
            self.running = True
            self.start_time = time.time()
            
            # Start stderr monitoring thread to detect RTMP connection issues
            self.stderr_thread = threading.Thread(target=self._monitor_ffmpeg_stderr, daemon=True)
            self.stderr_thread.start()
            
            logger.info("Optimized RTMP streaming started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start RTMP stream: {e}")
            return False
    
    def _build_ffmpeg_command(self):
        """Build FFmpeg command with proper audio sync"""
        if self.enable_audio:
            # Select audio device
            self.audio_device = self._select_audio_device()
            
            # Command with audio and video
            cmd = [
                'ffmpeg', '-y',
                
                # Video input: MJPEG frames from Unreal Engine
                '-f', 'image2pipe',
                '-vcodec', 'mjpeg',
                '-framerate', '20',  # Explicitly set input framerate
                '-i', 'pipe:0',
                
                # Audio input: DirectShow with proper buffering for sync  
                '-f', 'dshow',
                '-audio_buffer_size', '50',      # Match video frame time (50ms at 20fps)
                '-rtbufsize', '512k',             # Reasonable buffer (2.6 seconds of audio)
                '-i', f'audio={self.audio_device}',  # Use detected DirectShow audio device
                
                # CRITICAL: Set reference timestamps for sync
                '-use_wallclock_as_timestamps', '1',  # Use system clock
                '-thread_queue_size', '512',          # Adequate queue size
            
                # Video encoding with audio sync
                '-c:v', 'libx264',
                '-preset', 'ultrafast',      # Ultra-fast encoding for minimum latency
                '-tune', 'zerolatency',      # Ultra-low latency encoding
                '-crf', '23',                # Even higher CRF for ultra-stable bitrate
                '-maxrate', '1200k',         # Further reduced max bitrate
                '-bufsize', '600k',          # Smaller buffer for faster response
                '-minrate', '600k',          # Higher minimum bitrate for consistency
                
                # Audio encoding
                '-c:a', 'aac',
                '-b:a', '128k',
                '-ar', '48000',
                '-ac', '2',
                
                # Use filter_complex for precise sync
                '-filter_complex',
                '[0:v]fps=20,setpts=N/20/TB[v];'
                '[1:a]aresample=async=1:min_hard_comp=0.100000:first_pts=0[a]',
                
                '-map', '[v]',
                '-map', '[a]',
                
                # Ultra-stable x264 parameters - eliminate all variability
                '-x264-params', 'aq-mode=0:ref=1:bframes=0:rc-lookahead=0:scenecut=0:keyint=40:min-keyint=20:qpmin=25:qpmax=35:crf-max=30:vbv-init=0.5',
                '-g', '40',                  # Smaller GOP for 20fps (keyframe every 2 seconds)
                '-keyint_min', '20',         # Keyframe every second at 20fps
                '-profile:v', 'baseline',    # Baseline profile
                '-level', '3.0',             # H.264 level 3.0
                
                # Synchronization flags for proper A/V sync
                '-vsync', 'cfr',        # Constant frame rate
                '-async', '1',          # Audio sync
                '-copyts',              # Preserve timestamps
                '-start_at_zero',       # Start at zero
                
                # Force constant frame rate with strict timing
                '-r', '20',                  # Ultra-stable 20fps
                '-force_fps',                # Force frame rate
                
                # Streaming optimizations for minimal jitter
                '-f', 'flv',
                '-flvflags', 'no_duration_filesize+no_metadata',
                '-fflags', '+flush_packets+genpts',  # Flush packets immediately
                self.rtmp_url
            ]
        else:
            # Video-only command
            cmd = [
                'ffmpeg', '-y',
                
                # Input: MJPEG frames from Unreal Engine
                '-f', 'image2pipe',
                '-vcodec', 'mjpeg', 
                '-i', 'pipe:0',
                
                # Ultra-stable encoding pipeline
                '-c:v', 'libx264',
                '-preset', 'ultrafast',
                '-tune', 'zerolatency',
                '-crf', '23',
                '-maxrate', '1200k',
                '-bufsize', '600k',
                '-minrate', '600k',
                
                '-vf', 'format=yuv420p,fps=20',
                
                '-x264-params', 'aq-mode=0:ref=1:bframes=0:rc-lookahead=0:scenecut=0:keyint=40:min-keyint=20:qpmin=25:qpmax=35:crf-max=30:vbv-init=0.5',
                '-g', '40',
                '-keyint_min', '20',
                '-profile:v', 'baseline',
                '-level', '3.0',
                
                '-r', '20',
                '-vsync', 'cfr',
                '-force_fps',
                
                '-f', 'flv',
                '-flvflags', 'no_duration_filesize+no_metadata',
                '-fflags', '+flush_packets+genpts',
                self.rtmp_url
            ]
        
        return cmd
    
    def _monitor_ffmpeg_stderr(self):
        """Monitor FFmpeg stderr for RTMP connection issues"""
        if not self.process or not self.process.stderr:
            return
            
        try:
            while self.running and self.process:
                line = self.process.stderr.readline()
                if not line:
                    break
                    
                line_str = line.decode('utf-8', errors='ignore').strip()
                
                # Look for RTMP connection errors
                if any(error in line_str.lower() for error in [
                    'connection refused', 'connection reset', 'broken pipe',
                    'rtmp server', 'failed to connect', 'connection timed out',
                    'server disconnected', 'connection lost'
                ]):
                    self.connection_alive = False
                    self.last_rtmp_error = line_str
                    logger.warning(f"RTMP connection issue detected: {line_str}")
                    
                # Look for successful connection messages
                elif any(success in line_str.lower() for success in [
                    'stream mapping', 'press [q] to stop', 'video:'
                ]):
                    self.connection_alive = True
                    
        except Exception as e:
            logger.debug(f"Stderr monitoring error: {e}")
    
    def send_frame(self, jpeg_data):
        """Send JPEG frame with precise timing for A/V sync"""
        if not self.running or not self.process:
            return False
        
        # Initialize timing on first frame
        if not hasattr(self, 'stream_start_time'):
            self.stream_start_time = time.time()
            self.frame_number = 0
            self.last_frame_time = self.stream_start_time
        
        # Calculate exact timing for this frame
        frame_duration = 1.0 / 20.0  # 50ms per frame at 20fps
        target_time = self.stream_start_time + (self.frame_number * frame_duration)
        current_time = time.time()
        
        # If we're ahead, wait
        if current_time < target_time:
            sleep_time = target_time - current_time
            if sleep_time > 0.001:  # Only sleep if more than 1ms
                time.sleep(sleep_time)
        
        # If we're behind, log it but continue
        elif current_time - target_time > 0.050:  # More than 50ms behind
            drift = current_time - target_time
            logger.warning(f"WARNING: Video timing drift: {drift*1000:.1f}ms behind schedule")
        
        # Validate and send frame
        if not jpeg_data or len(jpeg_data) < 10:
            self.frames_failed += 1
            return False
        
        if jpeg_data[0] != 0xFF or jpeg_data[1] != 0xD8:
            logger.error(f"Invalid JPEG header")
            self.frames_failed += 1
            return False
        
        try:
            self.process.stdin.write(jpeg_data)
            self.process.stdin.flush()
            self.frames_sent += 1
            self.frame_number += 1
            self.last_frame_time = time.time()
            return True
        except Exception as e:
            logger.error(f"Frame send error: {e}")
            self.frames_failed += 1
            self.running = False
            return False
    
    def get_statistics(self):
        """Get streaming statistics with RTMP connection status"""
        elapsed = time.time() - self.start_time
        fps = self.frames_sent / max(elapsed, 1)
        success_rate = (self.frames_sent / max(1, self.frames_sent + self.frames_failed)) * 100
        
        return {
            'frames_sent': self.frames_sent,
            'frames_failed': self.frames_failed,
            'audio_chunks_sent': 0,  # Audio handled by FFmpeg DirectShow
            'fps': fps,
            'success_rate': success_rate,
            'elapsed_time': elapsed,
            'rtmp_connection_alive': self.connection_alive,
            'last_rtmp_error': self.last_rtmp_error,
            'audio_enabled': self.enable_audio,
            'audio_device': self.audio_device,  # Changed from audio_method
            'encoder': 'libx264',
            'raw_frames_enabled': False
        }
    
    def stop(self):
        """Stop RTMP streaming"""
        self.running = False
        if self.process:
            try:
                self.process.stdin.close()
                self.process.wait(timeout=3)
            except:
                self.process.terminate()
        
        stats = self.get_statistics()
        logger.info(f"RTMP streaming stopped - Stats: {stats}")

class ProductionWebRTCBridge:
    """Production-ready WebRTC to RTMP bridge with bulletproof reliability and audio support"""
    
    def __init__(self, config: LivepeerConfig, enable_audio=False):
        self.config = config
        self.frame_receiver = ProductionFrameReceiver(port=5000)
        self.rtmp_streamer = None
        self.running = False
        self.enable_audio = enable_audio
        
        # Statistics
        self.start_time = None
        self.last_stats_time = 0
        
    def start(self):
        """Start production bridge with optional audio"""
        logger.info("=== PRODUCTION WEBRTC BRIDGE STARTING ===")
        logger.info(f"Stream ID: {self.config.stream_id}")
        logger.info(f"Playback ID: {self.config.playback_id}")
        logger.info(f"Audio Enabled: {self.enable_audio}")
        logger.info("=== OPTIMIZED FOR 100% RELIABILITY ===")
        
        # Start frame receiver
        if not self.frame_receiver.start():
            logger.error("Failed to start frame receiver")
            return False
        
        # Start RTMP streaming with audio support
        rtmp_url = f"{self.config.rtmp_url}/{self.config.stream_key}"
        self.rtmp_streamer = OptimizedRTMPStreamer(rtmp_url, enable_audio=self.enable_audio)
        
        if not self.rtmp_streamer.start():
            logger.error("Failed to start RTMP streaming")
            self.frame_receiver.stop()
            return False
        
        self.running = True
        self.start_time = time.time()
        self._main_loop()
        
    def _main_loop(self):
        """Main processing loop with comprehensive monitoring"""
        logger.info("Production processing loop started")
        
        try:
            while self.running:
                # Get frame from receiver
                frame_data = self.frame_receiver.get_frame(timeout=0.01)
                
                if frame_data and self.rtmp_streamer:
                    self.rtmp_streamer.send_frame(frame_data)
                
                # Log statistics every 5 seconds
                current_time = time.time()
                if current_time - self.last_stats_time >= 5.0:
                    self._log_statistics()
                    self.last_stats_time = current_time
                
                time.sleep(0.0001)  # Ultra-minimal delay for low latency
                
        except KeyboardInterrupt:
            logger.info("Bridge interrupted by user")
        except Exception as e:
            logger.error(f"Critical error in main loop: {e}")
        finally:
            self.stop()
    
    def _log_statistics(self):
        """Log comprehensive performance statistics"""
        if not self.rtmp_streamer:
            return
            
        receiver_stats = self.frame_receiver.get_statistics()
        streamer_stats = self.rtmp_streamer.get_statistics()
        
        logger.info("=== PRODUCTION PERFORMANCE STATS ===")
        logger.info(f"Frame Success Rate: {receiver_stats['success_rate']:.1f}%")
        logger.info(f"RTMP Success Rate: {streamer_stats['success_rate']:.1f}%")
        logger.info(f"Streaming FPS: {streamer_stats['fps']:.1f}")
        logger.info(f"Frames Sent: {streamer_stats['frames_sent']}")
        logger.info(f"Packets Received: {receiver_stats['packets_received']}")
        logger.info(f"Frames Completed: {receiver_stats['frames_completed']}")
        logger.info(f"Frames Dropped: {receiver_stats['frames_dropped']}")
        logger.info(f"Incomplete Frames: {receiver_stats['incomplete_frames']}")
        logger.info(f"Quality Score: {min(receiver_stats['success_rate'], streamer_stats['success_rate']):.1f}%")
        logger.info("=====================================")
        
        # Alert on performance issues
        if streamer_stats['success_rate'] < 95:
            logger.warning(f"SUCCESS RATE BELOW 95%: {streamer_stats['success_rate']:.1f}%")
    
    def stop(self):
        """Stop bridge with graceful cleanup"""
        logger.info("Stopping production bridge")
        self.running = False
        
        if self.rtmp_streamer:
            self.rtmp_streamer.stop()
            
        if self.frame_receiver:
            self.frame_receiver.stop()
        
        logger.info("Production bridge stopped")

def main():
    """Main entry point for production streaming"""
    print("PRODUCTION WEBRTC -> LIVEPEER BRIDGE")
    print("==================================")
    print("Bulletproof reliability - Ultra-low latency")
    print("Optimized FFmpeg pipeline - Stable 20fps")
    print("Audio Support: Line In Priority")
    
    # Ask user if they want audio
    import sys
    enable_audio = '--audio' in sys.argv or '-a' in sys.argv
    
    config = LivepeerConfig()
    bridge = ProductionWebRTCBridge(config, enable_audio=enable_audio)
    
    try:
        print(f"\nStream ID: {config.stream_id}")
        print(f"Playbook ID: {config.playback_id}")  
        print(f"Playback URL: https://livepeercdn.com/hls/{config.playback_id}/index.m3u8")
        print(f"Audio Enabled: {enable_audio}")
        if enable_audio:
            print("Audio Source: Line In (Realtek(R) Audio) - Priority")
        print("==================================")
        print("Press Ctrl+C to stop")
        print()
        
        bridge.start()
        
    except KeyboardInterrupt:
        print("\nShutting down bridge...")
    except Exception as e:
        logger.error(f"Bridge failed: {e}")
        print(f"Bridge failed: {e}")

if __name__ == "__main__":
    main()