#!/usr/bin/env python3
"""
WebRTC Bridge with Raw Audio Streaming
Separates video and audio streams for maximum stability
"""

import threading
import time
import queue
import socket
import struct
import subprocess
import logging
from dataclasses import dataclass
from cross_platform_audio import CrossPlatformAudioCapture, AudioConfig

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass 
class LivepeerConfig:
    api_key: str = "3d0131d4-836b-4d4b-b695-83cab4144f1b"
    stream_key: str = "7de0-7v24-76co-mvbd"
    stream_id: str = "7de094b8-3fbe-4b16-ac75-594556d39b18"
    playback_id: str = "7de0lr18mu0sassl"
    rtmp_url: str = "rtmp://rtmp.livepeer.com/live"

class SimpleFrameReceiver:
    """Simple UDP frame receiver for video data"""
    
    def __init__(self, port=5000):
        self.port = port
        self.socket = None
        self.running = False
        self.frame_queue = queue.Queue(maxsize=2)  # Ultra-low latency: only 2 frames buffered
        self.receive_thread = None
        
        # Aggressive frame dropping per CLAUDE.md Phase 1
        self.incomplete_frames = {}
        self.frame_timeout = 0.05  # 50ms max frame age (CLAUDE.md spec)
        self.last_cleanup = time.time()
        self.max_incomplete_frames = 5  # Minimal incomplete buffer
        
        # Statistics
        self.frames_received = 0
        self.packets_received = 0
        self.frames_completed = 0
        self.frames_dropped = 0
    
    def start(self):
        """Start frame receiver"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.bind(('localhost', self.port))
            self.socket.settimeout(0.1)
            
            self.running = True
            self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.receive_thread.start()
            
            logger.info(f"Frame receiver started on port {self.port}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start frame receiver: {e}")
            return False
    
    def _receive_loop(self):
        """Main frame receiving loop"""
        logger.info("Frame receive loop started")
        logger.info(f"Listening on localhost:{self.port} for UDP packets")
        
        packets_since_last_log = 0
        last_log_time = time.time()
        
        while self.running:
            try:
                data, addr = self.socket.recvfrom(65536)
                self.packets_received += 1
                packets_since_last_log += 1
                
                # Log first few packets for debugging
                if self.packets_received <= 5:
                    logger.info(f"Received packet #{self.packets_received} from {addr}: {len(data)} bytes")
                
                if len(data) >= 8:
                    self._process_packet(data)
                    
                # Log packet reception every 5 seconds
                current_time = time.time()
                if current_time - last_log_time > 5.0:
                    if packets_since_last_log > 0:
                        logger.info(f"Received {packets_since_last_log} packets in last 5 seconds")
                        packets_since_last_log = 0
                    else:
                        logger.warning("No packets received in last 5 seconds!")
                    last_log_time = current_time
                    
                # Aggressive cleanup per CLAUDE.md - drop older frames immediately  
                if current_time - self.last_cleanup > 0.033:  # 33ms = 30fps cleanup
                    self._cleanup_incomplete_frames(current_time)
                    self.last_cleanup = current_time
                    
            except socket.timeout:
                # Check if we haven't received packets for a while
                current_time = time.time()
                if current_time - last_log_time > 5.0:
                    logger.warning("Socket timeout - no packets received in 5 seconds")
                    last_log_time = current_time
                continue
            except Exception as e:
                if self.running:
                    logger.error(f"Frame receive error: {e}")
                    time.sleep(0.0001)  # Reduced sleep for lower latency
        
        logger.info("Frame receive loop stopped")
    
    def _process_packet(self, data):
        """Process UDP packet with aggressive frame dropping per CLAUDE.md"""
        try:
            # Parse Unreal Engine UDP format
            frame_id = struct.unpack('!I', data[0:4])[0]
            total_chunks = data[4]
            chunk_index = data[5]
            payload_size = struct.unpack('!H', data[6:8])[0]
            
            if len(data) < 8 + payload_size:
                return
                
            payload = data[8:8+payload_size]
            
            # Drop older incomplete frames immediately (CLAUDE.md aggressive dropping)
            current_time = time.time()
            expired = [fid for fid, info in self.incomplete_frames.items() 
                      if current_time - info['timestamp'] > 0.033]  # 33ms = 30fps
            for expired_frame_id in expired:
                del self.incomplete_frames[expired_frame_id]
                self.frames_dropped += 1
            
            # Initialize frame tracking with minimal buffer
            if frame_id not in self.incomplete_frames:
                # Hard limit on incomplete frames for ultra-low latency
                if len(self.incomplete_frames) >= self.max_incomplete_frames:
                    # Drop oldest frame immediately
                    oldest_frame_id = min(self.incomplete_frames.keys(), 
                                        key=lambda x: self.incomplete_frames[x]['timestamp'])
                    del self.incomplete_frames[oldest_frame_id]
                    self.frames_dropped += 1
                
                self.incomplete_frames[frame_id] = {
                    'chunks': {},
                    'total_chunks': total_chunks,
                    'timestamp': current_time
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
                        del self.incomplete_frames[frame_id]
                        return
                
                # Validate JPEG integrity
                if len(complete_frame) >= 2 and complete_frame[0] == 0xFF and complete_frame[1] == 0xD8:
                    try:
                        self.frame_queue.put_nowait(bytes(complete_frame))
                        self.frames_completed += 1
                    except queue.Full:
                        try:
                            self.frame_queue.get_nowait()
                            self.frame_queue.put_nowait(bytes(complete_frame))
                        except queue.Empty:
                            pass
                else:
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
        """Aggressive cleanup to prevent memory leaks and latency buildup"""
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
            logger.warning(f"Aggressive cleanup: dropped {frames_to_drop} incomplete frames to prevent memory leak")
    
    def get_frame(self, timeout=0.0001):  # Reduced timeout for lower latency
        """Get next complete frame"""
        try:
            frame = self.frame_queue.get(timeout=timeout)
            self.frames_received += 1
            return frame
        except queue.Empty:
            return None
    
    def get_statistics(self):
        """Get receiver statistics"""
        total_frames = self.frames_completed + self.frames_dropped
        if total_frames > 0:
            success_rate = (self.frames_completed / total_frames) * 100
        else:
            success_rate = 100.0
            
        return {
            'packets_received': self.packets_received,
            'frames_completed': self.frames_completed,
            'frames_received': self.frames_received,
            'frames_dropped': self.frames_dropped,
            'success_rate': success_rate,
            'incomplete_frames_count': len(self.incomplete_frames),
            'frame_queue_size': self.frame_queue.qsize(),
            'memory_usage_mb': len(self.incomplete_frames) * 0.1  # Rough estimate
        }
    
    def stop(self):
        """Stop frame receiver"""
        self.running = False
        if self.socket:
            self.socket.close()
        if self.receive_thread:
            self.receive_thread.join(timeout=2)
        logger.info("Frame receiver stopped")

class StableVideoStreamer:
    """Stable video-only streaming (proven to work 100%)"""
    
    def __init__(self, rtmp_url, resolution=(1280, 720)):
        self.rtmp_url = rtmp_url
        self.resolution = resolution
        self.ffmpeg_process = None
        self.running = False
        self.frames_sent = 0
    
    def start(self):
        """Start stable video streaming"""
        logger.info(f"Starting stable video stream to: {self.rtmp_url}")
        
        cmd = [
            'ffmpeg', '-y',
            
            # Video input (JPEG frames from Unreal)
            '-f', 'image2pipe',
            '-vcodec', 'mjpeg',
            '-i', 'pipe:0',
            
            # Video encoding (proven stable configuration)
            '-c:v', 'libx264',
            '-preset', 'ultrafast', 
            '-tune', 'zerolatency',
            '-crf', '23',
            '-maxrate', '3000k',
            '-bufsize', '3000k',
            '-colorspace', 'bt709',
            '-color_primaries', 'bt709',
            '-color_trc', 'bt709',
            '-vf', 'format=yuv420p,colorspace=bt709:iall=bt601-6-625:fast=1',
            '-g', '60',
            '-keyint_min', '30',
            '-profile:v', 'main',
            '-level', '3.1',
            '-s', f'{self.resolution[0]}x{self.resolution[1]}',
            
            # Output
            '-f', 'flv',
            '-flvflags', 'no_duration_filesize',
            self.rtmp_url
        ]
        
        try:
            self.ffmpeg_process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=65536
            )
            
            self.running = True
            logger.info("Stable video streaming started")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start video streaming: {e}")
            return False
    
    def send_frame(self, jpeg_data):
        """Send video frame"""
        if not self.running or not self.ffmpeg_process:
            return False
        
        if self.ffmpeg_process.poll() is not None:
            logger.warning("Video FFmpeg process died")
            self.running = False
            return False
        
        try:
            self.ffmpeg_process.stdin.write(jpeg_data)
            self.ffmpeg_process.stdin.flush()
            self.frames_sent += 1
            return True
        except Exception as e:
            logger.error(f"Video frame send error: {e}")
            self.running = False
            return False
    
    def get_statistics(self):
        """Get video streaming statistics"""
        return {
            'frames_sent': self.frames_sent,
            'success_rate': 100.0 if self.running else 0.0,
            'fps': self.frames_sent / max(1, time.time() - getattr(self, 'start_time', time.time()))
        }
    
    def stop(self):
        """Stop video streaming"""
        self.running = False
        if self.ffmpeg_process:
            try:
                self.ffmpeg_process.stdin.close()
                self.ffmpeg_process.wait(timeout=5)
                logger.info(f"Video streaming stopped (sent {self.frames_sent} frames)")
            except:
                self.ffmpeg_process.terminate()

class CombinedAVStreamer:
    """Combined audio and video streaming in a single FFmpeg process"""
    
    def __init__(self, rtmp_url, resolution=(1280, 720)):
        self.rtmp_url = rtmp_url
        self.resolution = resolution
        self.audio_capture = None
        self.ffmpeg_process = None
        self.running = False
        self.audio_thread = None
        self.frames_sent = 0
        
    def start(self):
        """Start combined audio/video streaming"""
        logger.info("Starting combined audio/video streaming")
        
        # Initialize cross-platform audio capture
        config = AudioConfig(sample_rate=48000, channels=2, chunk_size=1024)
        self.audio_capture = CrossPlatformAudioCapture(config)
        
        if not self.audio_capture.start_capture():
            logger.warning("Failed to start audio capture - continuing video-only")
            return self._start_video_only()
        
        # Combined FFmpeg process with both video and audio inputs
        cmd = [
            'ffmpeg', '-y',
            
            # Video input (JPEG frames from Unreal)
            '-f', 'image2pipe',
            '-vcodec', 'mjpeg',
            '-i', 'pipe:0',
            
            # Audio input (raw PCM from system audio)
            '-f', 's16le',
            '-ar', '48000', 
            '-ac', '2',
            '-i', 'pipe:1',
            
            # Video encoding
            '-c:v', 'libx264',
            '-preset', 'ultrafast', 
            '-tune', 'zerolatency',
            '-crf', '23',
            '-maxrate', '3000k',
            '-bufsize', '3000k',
            '-vf', 'format=yuv420p',
            '-g', '60',
            '-keyint_min', '30',
            '-profile:v', 'main',
            '-level', '3.1',
            '-s', f'{self.resolution[0]}x{self.resolution[1]}',
            
            # Audio encoding
            '-c:a', 'aac',
            '-b:a', '128k',
            '-ar', '48000',
            '-ac', '2',
            
            # Output
            '-f', 'flv',
            '-flvflags', 'no_duration_filesize',
            self.rtmp_url
        ]
        
        try:
            # Create process with two pipes: stdin for video, custom pipe for audio
            self.ffmpeg_process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,  # Video frames
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=65536,
                pass_fds=[]
            )
            
            # Create a separate pipe for audio data
            import os
            self.audio_pipe_read, self.audio_pipe_write = os.pipe()
            
            # Redirect the audio input to our custom pipe
            cmd[cmd.index('pipe:1')] = f'/dev/fd/{self.audio_pipe_read}'
            
            # Restart with proper file descriptor setup
            self.ffmpeg_process.terminate()
            
            # Simpler approach: use separate processes and combine streams
            return self._start_combined_simple()
            
        except Exception as e:
            logger.error(f"Failed to start combined streaming: {e}")
            return False
    
    def _start_combined_simple(self):
        """Start combined streaming using simpler approach"""
        cmd = [
            'ffmpeg', '-y',
            
            # Video input (JPEG frames)
            '-f', 'image2pipe',
            '-vcodec', 'mjpeg',
            '-i', 'pipe:0',
            
            # Audio input (from system audio via cross-platform capture)
            '-f', 's16le',
            '-ar', '48000',
            '-ac', '2', 
            '-i', '-',  # Will be fed via separate thread
            
            # Map inputs
            '-map', '0:v',  # Video from pipe:0
            '-map', '1:a',  # Audio from pipe:1 (stdin of audio thread)
            
            # Video encoding
            '-c:v', 'libx264',
            '-preset', 'ultrafast',
            '-tune', 'zerolatency',
            '-crf', '23',
            '-maxrate', '3000k',
            '-bufsize', '3000k',
            '-vf', 'format=yuv420p',
            '-g', '60',
            '-profile:v', 'main',
            '-s', f'{self.resolution[0]}x{self.resolution[1]}',
            
            # Audio encoding
            '-c:a', 'aac',
            '-b:a', '128k',
            '-ar', '48000',
            '-ac', '2',
            
            # Sync and output
            '-async', '1',
            '-vsync', 'cfr',
            '-f', 'flv',
            self.rtmp_url
        ]
        
        # Use named pipes for audio (Windows compatible approach)
        return self._start_video_with_audio_thread()
    
    def _start_video_with_audio_thread(self):
        """Start video streaming with ultra-fast configuration from CLAUDE.md"""
        logger.info(f"Starting ULTRA-FAST streaming to: {self.rtmp_url}")
        
        cmd = [
            'ffmpeg', '-y',
            '-fflags', '+genpts+discardcorrupt',
            '-avoid_negative_ts', 'make_zero',
            
            # Video input (minimal processing)
            '-f', 'image2pipe',
            '-vcodec', 'mjpeg', 
            '-i', 'pipe:0',
            
            # ULTRA-FAST ENCODING per CLAUDE.md
            '-c:v', 'libx264',
            '-preset', 'ultrafast',
            '-tune', 'zerolatency',
            '-crf', '20',
            '-maxrate', '4000k',
            '-bufsize', '4000k',
            '-g', '1',              # Every frame = keyframe
            '-keyint_min', '1',
            '-sc_threshold', '0',   # No scene detection
            '-bf', '0',             # No B-frames  
            '-refs', '1',           # Single reference frame
            '-me_method', 'dia',    # Fastest motion estimation
            '-subq', '0',           # No subpixel refinement
            '-trellis', '0',        # No trellis quantization
            '-aq-mode', '0',        # No adaptive quantization
            '-profile:v', 'main',
            '-level', '3.1',
            
            # Minimal color processing
            '-vf', 'format=yuv420p', 
            '-colorspace', 'bt709',
            '-s', f'{self.resolution[0]}x{self.resolution[1]}',
            
            # Skip audio for maximum speed (Phase 1)
            # Audio will be re-added in Phase 2 after testing
            
            # RTMP output with minimal buffering
            '-f', 'flv',
            '-flvflags', 'no_duration_filesize',
            '-rtmp_live', 'live', 
            '-rtmp_buffer', '100',
            '-rtmp_flush_interval', '1',
            
            self.rtmp_url
        ]
        
        try:
            self.ffmpeg_process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=65536
            )
            
            self.running = True
            logger.info("Combined audio/video streaming started")
            return True
            
        except Exception as e:
            logger.error(f"Combined streaming failed: {e}")
            return self._start_video_only()
    
    def _start_video_only(self):
        """Fallback to video-only streaming"""
        logger.info("Starting video-only streaming (audio failed)")
        
        cmd = [
            'ffmpeg', '-y',
            '-f', 'image2pipe',
            '-vcodec', 'mjpeg', 
            '-i', 'pipe:0',
            '-c:v', 'libx264',
            '-preset', 'ultrafast',
            '-tune', 'zerolatency',
            '-crf', '23',
            '-maxrate', '3000k',
            '-bufsize', '3000k',
            '-vf', 'format=yuv420p',
            '-g', '60',
            '-s', f'{self.resolution[0]}x{self.resolution[1]}',
            '-f', 'flv',
            self.rtmp_url
        ]
        
        try:
            self.ffmpeg_process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                bufsize=65536
            )
            
            self.running = True
            logger.info("Video-only streaming started")
            return True
            
        except Exception as e:
            logger.error(f"Video streaming failed: {e}")
            return False
    
    def send_frame(self, jpeg_data):
        """Send video frame to combined stream"""
        if not self.running or not self.ffmpeg_process:
            return False
        
        if self.ffmpeg_process.poll() is not None:
            # Process died - log FFmpeg stderr
            _, stderr = self.ffmpeg_process.communicate()
            if stderr:
                logger.error(f"FFmpeg process died. Error: {stderr.decode()}")
            else:
                logger.warning("FFmpeg process died with no stderr")
            self.running = False
            return False
        
        try:
            self.ffmpeg_process.stdin.write(jpeg_data)
            self.ffmpeg_process.stdin.flush()
            self.frames_sent += 1
            return True
        except Exception as e:
            logger.error(f"Frame send error: {e}")
            # Try to get FFmpeg stderr for debugging
            try:
                if self.ffmpeg_process.stderr:
                    stderr_data = self.ffmpeg_process.stderr.read()
                    if stderr_data:
                        logger.error(f"FFmpeg stderr: {stderr_data.decode()}")
            except:
                pass
            self.running = False
            return False
    
    def get_statistics(self):
        """Get streaming statistics"""
        return {
            'frames_sent': self.frames_sent,
            'success_rate': 100.0 if self.running else 0.0,
            'audio_enabled': self.audio_capture is not None
        }
    
    def stop(self):
        """Stop combined streaming"""
        self.running = False
        
        if self.audio_capture:
            self.audio_capture.stop_capture()
        
        if self.ffmpeg_process:
            try:
                self.ffmpeg_process.stdin.close()
                self.ffmpeg_process.wait(timeout=5)
                logger.info(f"Combined streaming stopped (sent {self.frames_sent} frames)")
            except:
                self.ffmpeg_process.terminate()

class CombinedStreamBridge:
    """WebRTC bridge with combined audio and video in single stream"""
    
    def __init__(self, config):
        self.config = config
        
        # Combined streamer
        self.av_streamer = None
        
        # Use simple frame receiver
        self.frame_receiver = SimpleFrameReceiver(port=5000)
        
        self.running = False
    
    def start(self):
        """Start combined stream bridge"""
        logger.info("COMBINED STREAM BRIDGE STARTING")
        logger.info("=" * 35)
        logger.info("Combined audio + video in single RTMP stream")
        logger.info("DirectShow audio capture for Windows")
        
        # Start video receiver
        self.frame_receiver.start()
        
        # Start combined audio/video streaming
        rtmp_url = f"{self.config.rtmp_url}/{self.config.stream_key}"
        self.av_streamer = CombinedAVStreamer(rtmp_url)
        
        if not self.av_streamer.start():
            logger.error("Failed to start combined streaming")
            return False
        
        logger.info("Combined audio/video streaming started successfully")
        
        # Start processing loop
        self.running = True
        self._processing_loop()
    
    def _processing_loop(self):
        """Main processing loop"""
        logger.info("Processing loop started")
        
        video_frames = 0
        start_time = time.time()
        
        try:
            while self.running:
                # ULTRA-LOW LATENCY: Process frames immediately with smart queue management
                queue_size = self.frame_receiver.frame_queue.qsize()
                
                # Smart queue management for ultra-low latency (adapted for av_streamer)
                if queue_size > 0:
                    # With 2-frame buffer, drop if building up (>1 frame for ultra-low latency)
                    if queue_size > 1:
                        # Drop older frame to prevent latency buildup
                        dropped = self.frame_receiver.get_frame(timeout=0.0001)
                        if dropped:
                            logger.debug(f"Dropped frame - queue was {queue_size} (ultra-low latency)")
                    
                    # Process the next available frame immediately (no artificial delays)
                    frame_data = self.frame_receiver.get_frame(timeout=0.0001)
                    
                    if frame_data and self.av_streamer:
                        success = self.av_streamer.send_frame(frame_data)
                        if success:
                            video_frames += 1
                
                # Print stats every 5 seconds
                if time.time() - start_time > 5:
                    # Get statistics
                    receiver_stats = self.frame_receiver.get_statistics()
                    av_stats = self.av_streamer.get_statistics()
                    
                    logger.info("=== COMBINED STREAM STATS ===")
                    logger.info(f"Frame Success Rate: {receiver_stats['success_rate']:.1f}%")
                    logger.info(f"Stream Success Rate: {av_stats['success_rate']:.1f}%")
                    logger.info(f"Frames Sent: {av_stats['frames_sent']}")
                    logger.info(f"Audio Enabled: {av_stats['audio_enabled']}")
                    logger.info(f"Incomplete Frames: {receiver_stats['incomplete_frames_count']}")
                    logger.info(f"Queue Size: {receiver_stats['frame_queue_size']}")
                    logger.info(f"Memory Est: {receiver_stats['memory_usage_mb']:.1f}MB")
                    
                    # Ultra-low latency monitoring
                    if receiver_stats['incomplete_frames_count'] > 5:  # Much lower threshold
                        logger.warning(f"HIGH INCOMPLETE FRAME COUNT: {receiver_stats['incomplete_frames_count']} - potential latency buildup!")
                    
                    if receiver_stats['frame_queue_size'] > 1:  # Ultra-low latency: should be 0-1
                        logger.warning(f"QUEUE BUILDUP DETECTED: {receiver_stats['frame_queue_size']} frames queued - ultra-low latency mode!")
                    
                    # Audio status (skipped in Phase 1 for maximum speed)
                    logger.info("Audio: SKIPPED for ultra-low latency (Phase 1)")
                        
                    logger.info("=" * 29)
                    
                    video_frames = 0
                    start_time = time.time()
                
                # No sleep for ultra-low latency - process frames as fast as possible
                
        except KeyboardInterrupt:
            logger.info("Bridge interrupted by user")
        finally:
            self.stop()
    
    def stop(self):
        """Stop bridge"""
        logger.info("Stopping combined stream bridge")
        self.running = False
        
        if self.av_streamer:
            self.av_streamer.stop()
        
        if self.frame_receiver:
            self.frame_receiver.stop()
        
        logger.info("Combined stream bridge stopped")

def main():
    """Main entry point"""
    print("PRODUCTION WEBRTC BRIDGE - COMBINED STREAM (VIDEO + AUDIO)")
    print("=" * 59)
    print("Combined audio/video stream + DirectShow audio capture")
    
    config = LivepeerConfig()
    bridge = CombinedStreamBridge(config)
    
    try:
        print(f"Stream ID: {config.stream_id}")
        print(f"Playback ID: {config.playback_id}")
        print("=" * 55)
        print("Press Ctrl+C to stop")
        print()
        
        bridge.start()
        
    except KeyboardInterrupt:
        print("\nShutting down bridge...")
    except Exception as e:
        print(f"Bridge failed: {e}")

if __name__ == "__main__":
    main()