#!/usr/bin/env python3
"""
Correct RTMP Bridge - Production-Ready Unreal Engine to Livepeer Stream
Bulletproof reliability with latency optimization and cross-platform audio
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
import sounddevice as sd
import numpy as np
import sys
import platform
from enum import IntEnum

# Import cross-platform audio capabilities
from cross_platform_audio import CrossPlatformAudioCapture, AudioConfig

class FrameSyncedAudioCapture:
    """Frame-synced audio - captures exactly 2400 samples per 20fps video frame for 1:1 sync"""
    
    def __init__(self, sample_rate=48000, channels=2, fps=20):
        self.sample_rate = sample_rate
        self.channels = channels
        self.fps = fps
        # Calculate exact audio samples per video frame for perfect 1:1 sync
        self.samples_per_frame = int(sample_rate / fps)  # 2400 samples per frame at 20fps
        self.running = False
        self.stream = None
        self.audio_frame_buffer = np.zeros((self.samples_per_frame, channels), dtype=np.float32)
        self.buffer_position = 0
        self.frame_ready_queue = queue.Queue(maxsize=3)
        
    def audio_callback(self, indata, frames, time_info, status):
        """Collect audio into frame-sized chunks that match video timing"""
        if not self.running:
            return
            
        # Add incoming audio to frame buffer
        remaining_space = self.samples_per_frame - self.buffer_position
        samples_to_copy = min(frames, remaining_space)
        
        self.audio_frame_buffer[self.buffer_position:self.buffer_position + samples_to_copy] = indata[:samples_to_copy]
        self.buffer_position += samples_to_copy
        
        # When we have a complete frame's worth of audio
        if self.buffer_position >= self.samples_per_frame:
            # Convert to 16-bit PCM for FFmpeg
            audio_frame = (self.audio_frame_buffer * 32767).astype(np.int16)
            
            try:
                # Send complete audio frame (non-blocking)
                self.frame_ready_queue.put_nowait(audio_frame.tobytes())
            except queue.Full:
                # Drop frame if queue full (maintain real-time sync)
                pass
            
            # Reset buffer for next frame
            self.buffer_position = 0
            self.audio_frame_buffer.fill(0)
    
    def start_capture(self):
        """Start frame-synced audio capture"""
        try:
            # Capture with small blocks for responsiveness but accumulate to frame size
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                blocksize=240,  # 5ms blocks for responsiveness
                callback=self.audio_callback,
                device=None,
                latency='low'
            )
            self.stream.start()
            self.running = True
            logger.info(f"🎵 Frame-synced audio: {self.samples_per_frame} samples/frame ({1000/self.fps:.1f}ms per frame)")
            return True
        except Exception as e:
            logger.error(f"Failed to start frame-synced audio: {e}")
            return False
    
    def stop_capture(self):
        """Stop audio capture"""
        self.running = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
    
    def get_audio_frame(self):
        """Get one complete audio frame that matches video frame timing"""
        try:
            return self.frame_ready_queue.get_nowait()
        except queue.Empty:
            return None

class FrameFormat(IntEnum):
    MJPEG = 0
    RGB24 = 1
    YUV420 = 2

# Configure production-grade logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('streaming_performance.log', mode='a')
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

def detect_hardware_encoder():
    """Detect best available hardware encoder"""
    encoders = [
        ('h264_nvenc', 'NVIDIA NVENC'),    # NVIDIA GPUs
        ('h264_amf', 'AMD AMF'),           # AMD GPUs  
        ('h264_qsv', 'Intel Quick Sync'),  # Intel iGPU
        ('libx264', 'Software x264')       # Software fallback
    ]
    
    for encoder, name in encoders:
        try:
            test_cmd = ['ffmpeg', '-hide_banner', '-f', 'lavfi', '-i', 'testsrc=duration=1:size=320x240:rate=1', 
                       '-c:v', encoder, '-t', '1', '-f', 'null', '-']
            result = subprocess.run(test_cmd, capture_output=True, timeout=5)
            if result.returncode == 0:
                logger.info(f"Detected hardware encoder: {name}")
                return encoder, name
        except Exception as e:
            logger.debug(f"Failed to test {encoder}: {e}")
            continue
    
    logger.info("Using software encoder: x264")
    return 'libx264', 'Software x264'

class RawFrameReceiver:
    """High-quality raw frame receiver for direct FFmpeg input"""
    
    def __init__(self, port=5001):
        self.port = port
        self.socket = None
        self.running = False
        self.raw_frame_queue = queue.Queue(maxsize=10)  # Smaller queue for raw frames
        self.receive_thread = None
        
        # Raw frame reconstruction
        self.incomplete_raw_frames = {}
        self.raw_frame_timeout = 2.0  # Increased timeout for raw frames (they're larger)
        self.last_raw_cleanup = time.time()
        
        # Statistics
        self.raw_packets_received = 0
        self.raw_frames_completed = 0
        self.raw_frames_dropped = 0
        
    def start(self):
        """Start raw frame receiver"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.bind(('localhost', self.port))
            self.socket.settimeout(0.1)
            
            self.running = True
            self.receive_thread = threading.Thread(target=self._receive_raw_loop, daemon=True)
            self.receive_thread.start()
            
            logger.info(f"Raw frame receiver started on port {self.port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start raw frame receiver: {e}")
            return False
    
    def _receive_raw_loop(self):
        """Main raw frame receiving loop"""
        logger.info("Raw frame receive loop started")
        
        while self.running:
            try:
                data, addr = self.socket.recvfrom(65536)
                self.raw_packets_received += 1
                
                if len(data) >= 12:  # Raw frame header size
                    self._process_raw_packet(data)
                    
                # Cleanup expired frames
                current_time = time.time()
                if current_time - self.last_raw_cleanup > 0.2:  # Clean every 200ms
                    self._cleanup_incomplete_raw_frames(current_time)
                    self.last_raw_cleanup = current_time
                    
            except socket.timeout:
                continue
            except Exception as e:
                if self.running:
                    logger.error(f"Raw frame receive error: {e}")
                    time.sleep(0.001)
        
        logger.info("Raw frame receive loop stopped")
    
    def _process_raw_packet(self, data):
        """Process raw frame UDP packet"""
        try:
            # Parse raw frame format: [uint32 frame_id][uint8 total_chunks][uint8 chunk_index][uint8 format][uint16 payload_size][uint16 width][uint16 height][payload]
            frame_id = struct.unpack('!I', data[0:4])[0]
            total_chunks = data[4]
            chunk_index = data[5]
            frame_format = data[6]
            payload_size = struct.unpack('!H', data[7:9])[0]
            width = struct.unpack('!H', data[9:11])[0]
            height = struct.unpack('!H', data[11:13])[0]
            
            if len(data) < 13 + payload_size:
                return
                
            payload = data[13:13+payload_size]
            
            # Initialize frame tracking
            if frame_id not in self.incomplete_raw_frames:
                if len(self.incomplete_raw_frames) >= 20:  # Limit incomplete frames
                    self._aggressive_raw_cleanup()
                
                self.incomplete_raw_frames[frame_id] = {
                    'chunks': {},
                    'total_chunks': total_chunks,
                    'format': frame_format,
                    'width': width,
                    'height': height,
                    'timestamp': time.time()
                }
            
            frame_info = self.incomplete_raw_frames[frame_id]
            frame_info['chunks'][chunk_index] = payload
            
            # Check if frame is complete
            if len(frame_info['chunks']) == frame_info['total_chunks']:
                complete_frame = bytearray()
                for i in range(frame_info['total_chunks']):
                    if i in frame_info['chunks']:
                        complete_frame.extend(frame_info['chunks'][i])
                    else:
                        del self.incomplete_raw_frames[frame_id]
                        self.raw_frames_dropped += 1
                        return
                
                # Package complete raw frame
                raw_frame = {
                    'data': bytes(complete_frame),
                    'format': frame_info['format'],
                    'width': frame_info['width'],
                    'height': frame_info['height'],
                    'frame_id': frame_id
                }
                
                try:
                    self.raw_frame_queue.put_nowait(raw_frame)
                    self.raw_frames_completed += 1
                    
                    # Debug log for raw frame completion
                    if self.raw_frames_completed % 10 == 0:
                        logger.info(f"Raw frame completed: {frame_id}, size: {len(complete_frame)} bytes, format: {frame_info['format']}, {frame_info['width']}x{frame_info['height']}")
                except queue.Full:
                    # Replace oldest frame
                    try:
                        self.raw_frame_queue.get_nowait()
                        self.raw_frame_queue.put_nowait(raw_frame)
                    except queue.Empty:
                        pass
                
                del self.incomplete_raw_frames[frame_id]
                
        except Exception as e:
            logger.error(f"Raw packet processing error: {e}")
    
    def _cleanup_incomplete_raw_frames(self, current_time):
        """Remove expired incomplete raw frames"""
        expired = [fid for fid, info in self.incomplete_raw_frames.items() 
                  if current_time - info['timestamp'] > self.raw_frame_timeout]
        for frame_id in expired:
            del self.incomplete_raw_frames[frame_id]
            self.raw_frames_dropped += 1
    
    def _aggressive_raw_cleanup(self):
        """Aggressive cleanup for raw frames"""
        if len(self.incomplete_raw_frames) >= 20:
            sorted_frames = sorted(
                self.incomplete_raw_frames.items(), 
                key=lambda x: x[1]['timestamp'], 
                reverse=True
            )
            
            frames_to_keep = sorted_frames[:10]  # Keep only 10 newest
            frames_to_drop = len(self.incomplete_raw_frames) - len(frames_to_keep)
            
            self.incomplete_raw_frames.clear()
            for frame_id, frame_info in frames_to_keep:
                self.incomplete_raw_frames[frame_id] = frame_info
            
            self.raw_frames_dropped += frames_to_drop
    
    def get_raw_frame(self, timeout=0.001):
        """Get next complete raw frame"""
        try:
            return self.raw_frame_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def get_statistics(self):
        """Get raw frame receiver statistics"""
        total_attempted = self.raw_frames_completed + self.raw_frames_dropped
        if total_attempted > 0:
            success_rate = (self.raw_frames_completed / total_attempted) * 100
        else:
            success_rate = 100.0
            
        return {
            'raw_packets_received': self.raw_packets_received,
            'raw_frames_completed': self.raw_frames_completed,
            'raw_frames_dropped': self.raw_frames_dropped,
            'raw_incomplete_frames': len(self.incomplete_raw_frames),
            'raw_success_rate': success_rate
        }
    
    def stop(self):
        """Stop raw frame receiver"""
        self.running = False
        if self.socket:
            self.socket.close()
        if self.receive_thread:
            self.receive_thread.join(timeout=2)
        logger.info(f"Raw frame receiver stopped - Stats: {self.get_statistics()}")

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
        self.target_frame_interval = 1.0 / 20.0  # 20fps target for stability
        self.frame_buffer = []  # Small buffer for smoothing
        self.max_buffer_size = 2  # Reduced buffer for lower latency
        
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
            
            # Return frames at consistent intervals with adaptive timing
            current_time = time.time()
            if self.last_frame_output_time > 0:
                elapsed = current_time - self.last_frame_output_time
                if elapsed < self.target_frame_interval:
                    # Wait for timing but allow some variance
                    sleep_time = self.target_frame_interval - elapsed
                    if sleep_time > 0.003:  # Only sleep for 3ms+ delays
                        time.sleep(min(sleep_time, 0.015))  # Max 15ms sleep
                        
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
    """Production-grade RTMP streamer with hardware acceleration and raw frame support"""
    
    def __init__(self, rtmp_url, audio_config: AudioConfig = None):
        self.rtmp_url = rtmp_url
        self.audio_config = audio_config or AudioConfig()
        self.process = None
        self.running = False
        
        # Hardware acceleration
        self.encoder, self.encoder_name = detect_hardware_encoder()
        
        # Statistics
        self.frames_sent = 0
        self.raw_frames_sent = 0
        self.frames_failed = 0
        self.audio_chunks_sent = 0
        self.start_time = time.time()
        
        # RTMP connection monitoring
        self.stderr_thread = None
        self.connection_alive = True
        self.last_rtmp_error = None
        
        # Audio streaming
        self.audio_capture = None
        self.audio_thread = None
        self.enable_audio = False
        
        # Raw frame support
        self.raw_frame_receiver = None
        self.raw_frame_thread = None
        self.use_raw_frames = False
        
    def start(self, enable_audio=True):
        """Start optimized FFmpeg RTMP stream with optional audio"""
        self.enable_audio = enable_audio
        logger.info(f"Starting optimized RTMP stream to: {self.rtmp_url} (audio: {enable_audio})")
        
        # Start raw frame receiver if enabled
        if self.use_raw_frames:
            self.raw_frame_receiver = RawFrameReceiver(port=5001)
            if not self.raw_frame_receiver.start():
                logger.warning("Raw frame receiver failed - falling back to MJPEG")
                self.use_raw_frames = False
            else:
                logger.info("Raw frame receiver started - High quality mode enabled")
        
        # Start audio capture for validation if enabled
        if enable_audio:
            self.audio_capture = CrossPlatformAudioCapture(self.audio_config)
            if not self.audio_capture.start_capture():
                logger.warning("Audio validation failed - continuing with video only")
                self.enable_audio = False
            else:
                logger.info(f"Audio validation active: {self.audio_capture.method}")
                logger.info("Note: FFmpeg DirectShow handles actual audio streaming")
        
        # Build FFmpeg command with or without audio
        cmd = self._build_ffmpeg_command()
        
        # Log the complete FFmpeg command for debugging
        logger.info(f"FFmpeg command: {' '.join(cmd)}")
        
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
            
            # Start audio streaming thread if audio is enabled
            if self.enable_audio and self.audio_capture:
                self.audio_thread = threading.Thread(target=self._audio_streaming_loop, daemon=True)
                self.audio_thread.start()
            
            # Start raw frame processing thread if enabled
            if self.use_raw_frames and self.raw_frame_receiver:
                self.raw_frame_thread = threading.Thread(target=self._raw_frame_loop, daemon=True)
                self.raw_frame_thread.start()
            
            logger.info(f"High-quality RTMP streaming started (encoder: {self.encoder_name}, audio: {self.enable_audio}, raw: {self.use_raw_frames})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start RTMP stream: {e}")
            return False
    
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
                
                # Store last error for debugging
                if line_str:
                    self._last_ffmpeg_error = line_str
                
                # Look for input format errors
                if any(error in line_str.lower() for error in [
                    'invalid data found', 'header missing', 'no such file',
                    'invalid argument', 'could not find codec', 'unsupported'
                ]):
                    logger.error(f"FFmpeg input error: {line_str}")
                
                # Look for RTMP connection errors
                elif any(error in line_str.lower() for error in [
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
                    
                # Log video quality metrics
                elif any(metric in line_str.lower() for metric in [
                    'frame=', 'fps=', 'q=', 'size=', 'time=', 'bitrate=', 'speed='
                ]):
                    # Parse and log detailed video metrics for quality optimization
                    if 'frame=' in line_str and 'fps=' in line_str:
                        parts = line_str.split()
                        frame_data = {}
                        for part in parts:
                            if '=' in part:
                                key, value = part.split('=', 1)
                                frame_data[key] = value
                        
                        # Log detailed quality metrics every 100 frames
                        if 'frame' in frame_data:
                            try:
                                frame_num = int(frame_data['frame'])
                                if frame_num % 100 == 0:
                                    logger.info(f"🎥 VIDEO QUALITY: Frame {frame_data.get('frame', 'N/A')}, "
                                              f"FPS {frame_data.get('fps', 'N/A')}, "
                                              f"Quality {frame_data.get('q', 'N/A')}, "
                                              f"Size {frame_data.get('size', 'N/A')}, "
                                              f"Speed {frame_data.get('speed', 'N/A')}")
                            except:
                                pass
                    logger.info(f"FFmpeg: {line_str}")
                
                # Log audio sync issues with detailed analysis and recovery tracking
                elif 'buffer' in line_str.lower() and 'audio' in line_str.lower():
                    # Extract buffer percentage for sync analysis
                    if '%' in line_str:
                        try:
                            percent_start = line_str.find('(') + 1
                            percent_end = line_str.find('%')
                            if percent_start > 0 and percent_end > percent_start:
                                buffer_percent = int(line_str[percent_start:percent_end])
                                
                                # Track audio buffer health for sync optimization
                                if hasattr(self, 'audio_buffer_stats'):
                                    self.audio_buffer_stats.append(buffer_percent)
                                    if len(self.audio_buffer_stats) > 10:
                                        self.audio_buffer_stats.pop(0)
                                    avg_buffer = sum(self.audio_buffer_stats) / len(self.audio_buffer_stats)
                                else:
                                    self.audio_buffer_stats = [buffer_percent]
                                    avg_buffer = buffer_percent
                                
                                if buffer_percent >= 95:
                                    logger.error(f"🔊 CRITICAL AUDIO OVERFLOW: {buffer_percent}% (avg: {avg_buffer:.1f}%)")
                                elif buffer_percent >= 80:
                                    logger.warning(f"🔊 AUDIO SYNC WARNING: {buffer_percent}% (avg: {avg_buffer:.1f}%)")
                                else:
                                    logger.info(f"🔊 AUDIO BUFFER: {buffer_percent}% (avg: {avg_buffer:.1f}%)")
                        except:
                            pass
                    else:
                        logger.warning(f"🔊 AUDIO ISSUE: {line_str}")
                
                # Log any error message
                elif 'error' in line_str.lower() or 'failed' in line_str.lower():
                    logger.error(f"FFmpeg: {line_str}")
                    
                # Log all FFmpeg output for debugging RTMP issues
                else:
                    logger.info(f"FFmpeg: {line_str}")
                    
        except Exception as e:
            logger.debug(f"Stderr monitoring error: {e}")
    
    def _build_ffmpeg_command(self):
        """Build hardware-accelerated FFmpeg command with proper audio sync"""
        if self.enable_audio:
            # Base command with MJPEG input
            cmd = [
                'ffmpeg', '-y',
                
                # Video input: MJPEG frames from Unreal Engine
                '-f', 'image2pipe',
                '-vcodec', 'mjpeg',
                '-framerate', '20',  # Explicitly set input framerate
                '-i', 'pipe:0',
                
                # Audio input: DirectShow with ultra-minimal buffer (prevents overflow)
                '-f', 'dshow',
                '-audio_buffer_size', '5',       # Ultra-minimal 5ms buffer
                '-rtbufsize', '8k',              # Ultra-small real-time buffer (8KB)
                '-i', 'audio=Stereo Mix (Realtek(R) Audio)',  # System audio capture
            ]
            
            # Hardware-specific encoding settings
            if 'nvenc' in self.encoder:
                # NVIDIA NVENC optimizations
                cmd.extend([
                    # Video encoding - RTMP compatible H.264 NVENC
                    '-c:v', 'h264_nvenc',
                    '-preset', 'p3',  # Use p3 preset (faster than 'fast')
                    '-tune', 'll',    # Low latency tuning
                    '-profile:v', 'main',
                    '-level:v', '4.0',
                    '-rc', 'cbr',
                    '-b:v', '3000k',
                    '-maxrate', '3000k',
                    '-bufsize', '1500k',  # Reduced buffer for lower latency
                    '-g', '40',
                    '-keyint_min', '20',
                    '-bf', '0',  # No B-frames for lower latency
                    
                    # Audio encoding - RTMP standard AAC
                    '-c:a', 'aac',
                    '-b:a', '128k',
                    '-ar', '44100',  # Keep original sample rate to avoid resampling
                    '-ac', '2',
                    
                    # Video processing
                    '-vf', 'format=yuv420p',
                    '-r', '20',  # Force output framerate
                    
                    # Audio processing - clean microphone input
                    '-af', 'aresample=async=1:first_pts=0',
                    
                    # Map inputs
                    '-map', '0:v',
                    '-map', '1:a',
                    
                    # Synchronization settings
                    '-vsync', 'cfr',
                    '-copyts',  # Preserve timestamps
                    '-start_at_zero',  # Start timestamps at zero
                    
                    # Output format
                    '-f', 'flv',
                    '-flvflags', 'no_duration_filesize',
                    '-fflags', '+genpts+discardcorrupt',
                    '-max_interleave_delta', '0',  # Strict interleaving
                    self.rtmp_url
                ])
            elif 'amf' in self.encoder:
                # AMD AMF optimizations - RTMP compatible
                cmd.extend([
                    # Video encoding - RTMP compatible H.264 AMF
                    '-c:v', 'h264_amf',
                    '-quality', 'balanced',      # Balanced quality for RTMP
                    '-profile:v', 'main',        # RTMP standard profile
                    '-level:v', '4.0',
                    '-rc', 'cbr',                # Constant bitrate for RTMP
                    '-b:v', '3000k',
                    '-maxrate', '3000k',
                    '-bufsize', '6000k',
                    '-g', '40',                  # Keyframe every 2 seconds
                    '-keyint_min', '20',
                    
                    # Audio encoding - RTMP standard AAC
                    '-c:a', 'aac',
                    '-b:a', '128k',
                    '-ar', '48000',
                    '-ac', '2',
                    
                    # Video processing - RTMP compatible
                    '-vf', 'format=yuv420p',
                    '-r', '20',
                    
                    # Audio processing
                    '-af', 'aresample=async=100',
                    
                    # Map inputs: video from pipe:0, audio from DirectShow
                    '-map', '0:v',
                    '-map', '1:a',
                    
                    # RTMP synchronization settings
                    '-vsync', 'cfr',
                    '-async', '1',
                    
                    # FLV container for RTMP
                    '-f', 'flv',
                    '-flvflags', 'no_duration_filesize',
                    '-fflags', '+flush_packets',
                    '-rtmp_live', 'live',
                    self.rtmp_url
                ])
            elif 'qsv' in self.encoder:
                # Intel Quick Sync optimizations - RTMP compatible
                cmd.extend([
                    # Video encoding - RTMP compatible H.264 QSV
                    '-c:v', 'h264_qsv',
                    '-preset', 'fast',
                    '-profile:v', 'main',        # RTMP standard profile
                    '-level:v', '4.0',
                    '-rc', 'cbr',                # Constant bitrate for RTMP
                    '-b:v', '3000k',
                    '-maxrate', '3000k',
                    '-bufsize', '6000k',
                    '-g', '40',                  # Keyframe every 2 seconds
                    '-keyint_min', '20',
                    
                    # Audio encoding - RTMP standard AAC
                    '-c:a', 'aac',
                    '-b:a', '128k',
                    '-ar', '48000',
                    '-ac', '2',
                    
                    # Video processing - RTMP compatible
                    '-vf', 'format=yuv420p',
                    '-r', '20',
                    
                    # Audio processing
                    '-af', 'aresample=async=1000',
                    
                    # Map inputs: video from pipe:0, audio from DirectShow
                    '-map', '0:v',
                    '-map', '1:a',
                    
                    # RTMP synchronization settings
                    '-vsync', 'cfr',
                    '-async', '1',
                    
                    # FLV container for RTMP
                    '-f', 'flv',
                    '-flvflags', 'no_duration_filesize',
                    '-fflags', '+flush_packets',
                    '-rtmp_live', 'live',
                    self.rtmp_url
                ])
            else:
                # Software encoding with optimal settings
                cmd.extend([
                    '-c:v', 'libx264',
                    '-preset', 'fast',           # Faster than ultrafast but better quality
                    '-tune', 'zerolatency',
                    '-crf', '18',                # Much higher quality
                    '-maxrate', '6000k',         # Higher bitrate
                    '-bufsize', '3000k',
                    
                    # Audio encoding - high quality AAC
                    '-c:a', 'aac',
                    '-b:a', '128k',
                    '-ar', '48000',
                    '-ac', '2',
                    
                    # Video processing
                    '-vf', 'format=yuv420p,fps=20',
                    
                    # Audio sync and processing
                    '-af', 'aresample=async=1',
                    
                    # Map inputs: video from pipe:0, audio from DirectShow
                    '-map', '0:v',
                    '-map', '1:a',
                    
                    # Synchronization settings for A/V sync
                    '-async', '1',
                    '-vsync', 'cfr',
                    
                    # Ultra-stable x264 parameters
                    '-x264-params', 'aq-mode=0:ref=1:bframes=0:rc-lookahead=0:scenecut=0:keyint=40:min-keyint=20',
                    '-g', '40',
                    '-keyint_min', '20',
                    '-profile:v', 'baseline',
                    '-level', '3.0',
                    
                    # Force frame rate
                    '-r', '20',
                    '-force_fps',
                    
                    # Streaming optimizations with timestamp handling
                    '-f', 'flv',
                    '-flvflags', 'no_duration_filesize+no_metadata',
                    '-fflags', '+flush_packets+genpts+igndts',
                    '-max_delay', '100000',
                    '-rtmp_live', 'live',
                    self.rtmp_url
                ])
        else:
            # Video-only command remains the same
            cmd = [
                'ffmpeg', '-y',
                '-f', 'image2pipe',
                '-vcodec', 'mjpeg',
                '-framerate', '20',
                '-i', 'pipe:0',
                '-c:v', 'libx264',
                '-preset', 'ultrafast',
                '-tune', 'zerolatency',
                '-crf', '30',
                '-maxrate', '1200k',
                '-bufsize', '600k',
                '-vf', 'format=yuv420p',
                '-r', '20',
                '-vsync', 'cfr',
                '-x264-params', 'keyint=40:min-keyint=20:bframes=0',
                '-f', 'flv',
                '-flvflags', 'no_duration_filesize',
                '-fflags', '+genpts',
                self.rtmp_url
            ]
        
        return cmd
    
    def _audio_streaming_loop(self):
        """Monitor audio capture for validation (FFmpeg handles actual audio streaming)"""
        if not self.audio_capture:
            return
            
        logger.info(f"Audio monitoring started - FFmpeg DirectShow handles streaming")
        logger.info("Audio Method: DirectShow (integrated with FFmpeg)")
        
        # Since FFmpeg now handles audio directly via DirectShow,
        # we just monitor our audio capture for validation
        audio_chunks_captured = 0
        start_time = time.time()
        
        try:
            while self.running and self.audio_capture:
                audio_data = self.audio_capture.get_audio_data(timeout=0.01)
                
                if audio_data:
                    audio_chunks_captured += 1
                    self.audio_chunks_sent += 1
                    
                    # Log audio activity every 5 seconds for monitoring
                    if audio_chunks_captured % 500 == 0:
                        elapsed = time.time() - start_time
                        logger.info(f"Audio validation: {audio_chunks_captured} chunks in {elapsed:.1f}s")
                        
        except Exception as e:
            logger.error(f"Audio monitoring error: {e}")
        
        logger.info(f"Audio monitoring stopped - DirectShow integration active")
    
    def _raw_frame_loop(self):
        """Process raw frames and send directly to FFmpeg stdin"""
        if not self.raw_frame_receiver:
            return
            
        logger.info("Raw frame processing started - Maximum quality mode")
        
        while self.running and self.raw_frame_receiver:
            raw_frame = self.raw_frame_receiver.get_raw_frame(timeout=0.01)
            
            if raw_frame and self.process and self.process.stdin:
                try:
                    # Check if FFmpeg process is still alive
                    if self.process.poll() is not None:
                        logger.error(f"FFmpeg process died with return code: {self.process.returncode}")
                        break
                    
                    # Send frame data through the standard send_frame method
                    if raw_frame['format'] == FrameFormat.RGB24:
                        # Unreal Engine is actually sending JPEG data on the "raw" port
                        # Send through standard pipeline for proper statistics tracking
                        if self.send_frame(raw_frame['data']):
                            self.raw_frames_sent += 1
                        
                        # Log progress
                        if self.raw_frames_sent % 100 == 0 and self.raw_frames_sent > 0:
                            logger.info(f"Raw frames processed: {self.raw_frames_sent}")
                    else:
                        # Log send_frame failures for debugging
                        logger.error(f"Failed to send raw frame {raw_frame['frame_id']}")
                    
                except BrokenPipeError:
                    logger.error("FFmpeg stdin closed - process likely terminated")
                    break
                except Exception as e:
                    if self.running:
                        logger.error(f"Raw frame processing error: {e}")
                        # Check FFmpeg stderr for clues
                        if hasattr(self, '_last_ffmpeg_error'):
                            logger.error(f"Last FFmpeg error: {self._last_ffmpeg_error}")
                    break
        
        logger.info(f"Raw frame processing stopped - {self.raw_frames_sent} frames processed")
    
    def _handle_compressed_frame_data(self, frame_data):
        """Handle compressed frame data sent on raw frame port"""
        try:
            # The data is JPEG compressed, so we need to send it to the MJPEG input pipeline
            # instead of the raw RGB24 pipeline
            if hasattr(self, '_jpeg_process') and self._jpeg_process and self._jpeg_process.stdin:
                self._jpeg_process.stdin.write(frame_data)
                self._jpeg_process.stdin.flush()
                self.raw_frames_sent += 1
            else:
                # If no separate JPEG process, log the issue
                logger.warning("Received JPEG data on raw port but no JPEG pipeline available")
                
        except Exception as e:
            logger.error(f"Error handling compressed frame data: {e}")
    
    def send_frame(self, jpeg_data):
        """Send JPEG frame with RTMP connection validation and jitter reduction"""
        if not self.running or not self.process:
            return False
        
        # Check if RTMP connection is alive
        if not self.connection_alive:
            logger.warning(f"RTMP connection is down: {self.last_rtmp_error}")
            self.running = False
            return False
        
        # Quick process health check
        if self.process.poll() is not None:
            logger.warning("FFmpeg process died")
            self.running = False
            return False
        
        # Validate JPEG data
        if not jpeg_data or len(jpeg_data) < 10:
            self.frames_failed += 1
            return False
            
        # Validate frame header (JPEG for regular frames, skip for raw frames)
        if not self.use_raw_frames:
            if len(jpeg_data) < 2:
                logger.error(f"Frame too small: {len(jpeg_data)} bytes")
                self.frames_failed += 1
                return False
                
            if jpeg_data[0] != 0xFF or jpeg_data[1] != 0xD8:
                logger.error(f"Invalid JPEG header: {jpeg_data[0]:02x} {jpeg_data[1]:02x} (expected FF D8), frame size: {len(jpeg_data)}")
                self.frames_failed += 1
                return False
        
        # Stable frame pacing - target 20fps with buffer management
        current_time = time.time()
        if hasattr(self, 'last_frame_time'):
            target_interval = 1.0 / 20.0  # 20fps = 50ms
            elapsed = current_time - self.last_frame_time
            
            # Only sleep if we're running too fast, allow catch-up if behind
            if elapsed < target_interval:
                sleep_time = target_interval - elapsed
                if sleep_time > 0.005:  # Only sleep for significant delays (5ms+)
                    time.sleep(min(sleep_time, 0.025))  # Max 25ms sleep
            
            # Update timing
            self.last_frame_time = max(current_time, self.last_frame_time + target_interval)
        else:
            self.last_frame_time = current_time
        
        try:
            self.process.stdin.write(jpeg_data)
            self.process.stdin.flush()
            self.frames_sent += 1
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
            'audio_chunks_sent': self.audio_chunks_sent,
            'fps': fps,
            'success_rate': success_rate,
            'elapsed_time': elapsed,
            'rtmp_connection_alive': self.connection_alive,
            'last_rtmp_error': self.last_rtmp_error,
            'audio_enabled': self.enable_audio,
            'audio_method': self.audio_capture.method if self.audio_capture else None,
            'encoder': self.encoder_name,
            'raw_frames_enabled': self.use_raw_frames
        }
    
    def stop(self):
        """Stop RTMP streaming and audio capture"""
        self.running = False
        
        # Stop audio capture
        if self.audio_capture:
            self.audio_capture.stop_capture()
        
        # Stop raw frame receiver
        if self.raw_frame_receiver:
            self.raw_frame_receiver.stop()
        
        # Stop FFmpeg process
        if self.process:
            try:
                self.process.stdin.close()
                self.process.wait(timeout=3)
            except:
                self.process.terminate()
        
        stats = self.get_statistics()
        logger.info(f"RTMP streaming stopped - Stats: {stats}")

class ProductionWebRTCBridge:
    """Production-ready WebRTC to RTMP bridge with bulletproof reliability and audio"""
    
    def __init__(self, config: LivepeerConfig, audio_config: AudioConfig = None):
        self.config = config
        self.audio_config = audio_config or AudioConfig()
        self.frame_receiver = ProductionFrameReceiver(port=5000)
        self.rtmp_streamer = None
        self.running = False
        
        # Statistics
        self.start_time = None
        self.last_stats_time = 0
        
    def start(self, enable_audio=True):
        """Start production bridge with optional audio"""
        logger.info("=== PRODUCTION WEBRTC BRIDGE STARTING ===")
        logger.info(f"Stream ID: {self.config.stream_id}")
        logger.info(f"Playback ID: {self.config.playback_id}")
        logger.info(f"Audio Enabled: {enable_audio}")
        logger.info(f"Audio Config: {self.audio_config.sample_rate}Hz, {self.audio_config.channels}ch")
        logger.info("=== OPTIMIZED FOR 100% RELIABILITY ===")
        
        # Create RTMP streamer first to check raw frame settings
        rtmp_url = f"{self.config.rtmp_url}/{self.config.stream_key}"
        self.rtmp_streamer = OptimizedRTMPStreamer(rtmp_url, self.audio_config)
        
        # Start frame receiver (only if not using raw frames)
        if not self.rtmp_streamer.use_raw_frames:
            if not self.frame_receiver.start():
                logger.error("Failed to start frame receiver")
                return False
        else:
            logger.info("Skipping regular frame receiver - using raw frames only")
        
        if not self.rtmp_streamer.start(enable_audio=enable_audio):
            logger.error("Failed to start RTMP streaming")
            if not self.rtmp_streamer.use_raw_frames and self.frame_receiver:
                self.frame_receiver.stop()
            return False
        
        self.running = True
        self.start_time = time.time()
        self._main_loop()
        
    def _main_loop(self):
        """Main processing loop with comprehensive monitoring"""
        logger.info("Production processing loop started (with synchronized audio)")
        
        try:
            while self.running:
                # Get frame from receiver (works for both regular and raw frames now)
                if not self.rtmp_streamer.use_raw_frames:
                    frame_data = self.frame_receiver.get_frame(timeout=0.01)
                    
                    if frame_data and self.rtmp_streamer:
                        self.rtmp_streamer.send_frame(frame_data)
                else:
                    # Raw frames are handled in _raw_frame_loop via send_frame()
                    time.sleep(0.01)
                
                # Log statistics every 5 seconds
                current_time = time.time()
                if current_time - self.last_stats_time >= 5.0:
                    self._log_statistics()
                    self.last_stats_time = current_time
                
                if not self.rtmp_streamer.use_raw_frames:
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
        logger.info(f"Audio Chunks: {streamer_stats['audio_chunks_sent']}")
        logger.info(f"Audio Method: {streamer_stats['audio_method']}")
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
            
        if self.frame_receiver and not self.rtmp_streamer.use_raw_frames:
            self.frame_receiver.stop()
        
        logger.info("Production bridge stopped")

def main():
    """Main entry point for production streaming with audio"""
    print("PRODUCTION WEBRTC -> LIVEPEER BRIDGE WITH AUDIO")
    print("===============================================")
    print("Bulletproof reliability - Ultra-low latency")
    print("Cross-platform audio - Optimized FFmpeg pipeline")
    
    # Configure audio settings
    audio_config = AudioConfig(
        sample_rate=48000,
        channels=2,
        chunk_size=1024,
        format_bits=16
    )
    
    config = LivepeerConfig()
    bridge = ProductionWebRTCBridge(config, audio_config)
    
    try:
        print(f"\nStream ID: {config.stream_id}")
        print(f"Playback ID: {config.playback_id}")  
        print(f"Playback URL: https://livepeercdn.com/hls/{config.playback_id}/index.m3u8")
        print(f"Audio Config: {audio_config.sample_rate}Hz, {audio_config.channels} channels")
        print("===============================================")
        print("Press Ctrl+C to stop")
        print()
        
        # Ask user if they want audio
        enable_audio = True
        try:
            response = input("Enable audio? (Y/n): ").strip().lower()
            if response in ['n', 'no']:
                enable_audio = False
        except:
            pass  # Use default
        
        bridge.start(enable_audio=enable_audio)
        
    except KeyboardInterrupt:
        print("\nShutting down bridge...")
    except Exception as e:
        logger.error(f"Bridge failed: {e}")
        print(f"Bridge failed: {e}")

if __name__ == "__main__":
    main()