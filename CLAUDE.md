# CLAUDE.md - Ultra Low-Latency Live Streaming Analysis & Fixes

## Deep Technical Analysis - Current Pipeline Performance Issues

### Current System Overview
**Unreal Engine → UDP (localhost:5000) → Python Bridge → RTMP → Livepeer → HLS/WebRTC**

### Performance Metrics (Current vs Target)
- **Current Latency**: 4-6 seconds (due to buffering/encoding changes)  
- **Previous "BLAZING" Latency**: <2 seconds
- **UDP Reception**: ✅ 12,000+ packets/5sec (95.7% success rate)
- **Frame Processing**: ✅ 26.7 FPS from Unreal Engine
- **RTMP Connection**: ✅ Successfully connects to Livepeer

---

## CRITICAL LATENCY BOTTLENECKS IDENTIFIED

### 1. **FFmpeg Encoding Configuration - MAJOR BOTTLENECK**
**Current Problem:** Conservative encoding settings added for "stability"
```bash
# CURRENT (SLOW) SETTINGS:
-preset veryfast       # Should be 'ultrafast'
-crf 28               # Should be 18-23 for quality
-maxrate 2000k        # Should be 3000k+
-bufsize 2000k        # Should match maxrate
-g 30                 # Should be 1-5 for ultra-low latency
-profile:v baseline   # Should be 'main' for efficiency
```

**Fix:** Ultra-low latency FFmpeg configuration
```bash
-preset ultrafast
-tune zerolatency
-crf 20
-maxrate 4000k
-bufsize 4000k
-g 1                  # Every frame is keyframe
-keyint_min 1
-sc_threshold 0       # Disable scene change detection
-bf 0                 # No B-frames
-profile:v main
-level 3.1
```

### 2. **UDP Frame Reassembly - BUFFER BUILDUP ISSUE**
**Current Problem:** Frame timeout and cleanup causing delays
```python
# CURRENT (CAUSES BUILDUP):
self.frame_timeout = 1.0  # Too long - causes stale frames
self.max_incomplete_frames = 200  # Too conservative
```

**Fix:** Aggressive frame dropping for real-time streaming
```python
self.frame_timeout = 0.1      # Drop frames after 100ms
self.max_incomplete_frames = 10  # Minimal buffer
# Drop older frames IMMEDIATELY when new ones arrive
```

### 3. **DirectShow Audio Latency - HIDDEN BOTTLENECK**
**Current Problem:** DirectShow audio capture adds 100-300ms latency
```bash
# CURRENT:
-f dshow -i 'audio=Stereo Mix (Realtek(R) Audio)'
```

**Fix:** Either accept frame buildup OR use separate audio stream
```bash
# Option A: Skip audio entirely for ultra-low latency
# Option B: Use WasAPI with minimal buffering
-f wasapi -i default -audio_buffer_size 1024
```

### 4. **Python Processing Overhead**
**Current Problem:** Python async processing and memory management
- Memory pool allocations add 1-2ms per frame
- Queue management with 50-frame buffer
- Cleanup operations every 500ms

**Fix:** Bypass Python processing bottlenecks
```python
# Minimal queue size
self.frame_queue = queue.Queue(maxsize=3)  # Instead of 50
# Skip memory cleanup during streaming
# Process frames synchronously for minimal latency
```

### 5. **RTMP Streaming Parameters**
**Current Problem:** FLV muxing and RTMP buffering
```bash
# CURRENT:
-f flv -flvflags no_duration_filesize
```

**Fix:** Minimal RTMP buffering
```bash
-f flv -flvflags no_duration_filesize
-rtmp_live live
-rtmp_buffer 100    # Minimal buffer (100ms)
-rtmp_flush_interval 1
```

---

## ULTRA LOW-LATENCY CONFIGURATION RECOMMENDATIONS

### Immediate Fixes (Restore <2sec Latency)

#### 1. **Replace FFmpeg Command with Ultra-Fast Settings**
```python
cmd = [
    'ffmpeg', '-y',
    '-fflags', '+genpts+discardcorrupt',
    '-avoid_negative_ts', 'make_zero',
    
    # Video input (minimal processing)
    '-f', 'image2pipe',
    '-vcodec', 'mjpeg', 
    '-i', 'pipe:0',
    
    # ULTRA-FAST ENCODING
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
    
    # RTMP output with minimal buffering
    '-f', 'flv',
    '-flvflags', 'no_duration_filesize',
    '-rtmp_live', 'live', 
    '-rtmp_buffer', '100',
    '-rtmp_flush_interval', '1',
    
    self.rtmp_url
]
```

#### 2. **Aggressive Frame Dropping Configuration**
```python
class UltraLowLatencyFrameReceiver:
    def __init__(self, port=5000):
        self.frame_timeout = 0.05      # 50ms max frame age
        self.frame_queue = queue.Queue(maxsize=2)  # Only 2 frames buffered
        self.max_incomplete_frames = 5  # Minimal incomplete buffer
        
    def _process_packet(self, data):
        # Drop older incomplete frames immediately
        current_time = time.time()
        expired = [fid for fid, info in self.incomplete_frames.items() 
                  if current_time - info['timestamp'] > 0.033]  # 33ms = 30fps
        for frame_id in expired:
            del self.incomplete_frames[frame_id]
```

#### 3. **Skip Audio for Maximum Speed**
```python
class VideoOnlyStreamer:
    """Ultra-fast video-only streaming - no audio latency"""
    
    def start(self):
        cmd = [
            'ffmpeg', '-y',
            '-f', 'image2pipe', '-vcodec', 'mjpeg', '-i', 'pipe:0',
            '-c:v', 'libx264', '-preset', 'ultrafast', '-tune', 'zerolatency',
            '-crf', '18', '-g', '1', '-bf', '0', '-refs', '1',
            '-profile:v', 'main', '-level', '3.1',
            '-f', 'flv', '-rtmp_live', 'live', '-rtmp_buffer', '50',
            self.rtmp_url
        ]
```

#### 4. **Hardware Encoding (If Available)**
```python
# Use NVENC for GPU acceleration
cmd_nvenc = [
    'ffmpeg', '-y',
    '-f', 'image2pipe', '-vcodec', 'mjpeg', '-i', 'pipe:0',
    '-c:v', 'h264_nvenc',           # Hardware encoder
    '-preset', 'p1',                # Fastest preset
    '-tune', 'ull',                 # Ultra-low latency
    '-rc', 'cbr',                   # Constant bitrate
    '-b:v', '3000k',
    '-g', '1',                      # All keyframes
    '-f', 'flv', '-rtmp_live', 'live',
    self.rtmp_url
]
```

### Advanced Optimizations

#### 1. **Unreal Engine UDP Optimizations**
```cpp
// In WebRTCBridgeComponent.cpp
void UWebRTCBridgeComponent::SendFrameChunks(const TArray<uint8>& FrameData)
{
    // Send all chunks in rapid succession (no delays)
    for (uint8 ChunkIndex = 0; ChunkIndex < TotalChunks; ChunkIndex++)
    {
        // Build packet
        TArray<uint8> Packet;
        // ... packet construction ...
        
        // IMMEDIATE SEND - no queuing or delays
        int32 BytesSent = 0;
        UDPSocket->SendTo(Packet.GetData(), Packet.Num(), BytesSent, *RemoteAddr);
        
        // Optional: Send each chunk multiple times for reliability
        if (ChunkIndex == 0 || ChunkIndex == TotalChunks - 1) {
            UDPSocket->SendTo(Packet.GetData(), Packet.Num(), BytesSent, *RemoteAddr);
        }
    }
}

// Reduce JPEG quality for speed
UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WebRTC Bridge")
int32 JPEGQuality = 60; // Lower quality = faster encoding

// Increase FPS for smoother streaming
UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "WebRTC Bridge") 
float TargetFPS = 60.0f; // Higher FPS = lower per-frame latency
```

#### 2. **System-Level Optimizations**
```bash
# Windows network optimizations
netsh int tcp set global autotuninglevel=normal
netsh int tcp set global rss=enabled
netsh int tcp set global chimney=enabled

# Set process priority for Python bridge
# Run bridge with HIGH priority class in Task Manager
```

#### 3. **Alternative: Direct RTMP from Unreal Engine**
```cpp
// Skip Python bridge entirely - stream directly from UE5
// Use UE5's built-in RTMP streaming capabilities
// This eliminates UDP → Python → FFmpeg pipeline entirely
```

---

## RECOMMENDED IMPLEMENTATION STRATEGY

### Phase 1: Immediate Latency Reduction (30 minutes)
1. Replace current FFmpeg settings with ultra-fast configuration
2. Reduce frame timeout to 50ms
3. Skip audio temporarily to test video latency
4. Set frame queue size to 2 frames maximum

### Phase 2: Hardware Acceleration (1 hour) 
1. Test NVENC hardware encoding
2. Implement GPU-based JPEG decoding
3. Use dedicated network thread for UDP reception

### Phase 3: System Architecture (2+ hours)
1. Consider direct RTMP streaming from Unreal Engine
2. Implement custom UDP protocol with forward error correction  
3. Use memory-mapped files for zero-copy frame transfer

---

## EXPECTED PERFORMANCE IMPROVEMENTS

| Optimization | Latency Reduction | Complexity |
|-------------|------------------|------------|
| Ultra-fast FFmpeg | 1-2 seconds | Easy |
| Aggressive frame dropping | 0.5-1 seconds | Easy |
| Skip audio | 0.2-0.5 seconds | Easy |
| Hardware encoding | 0.5-1 seconds | Medium |
| Direct UE5 RTMP | 2-3 seconds | Hard |

**Target Result:** <2 second glass-to-glass latency matching previous "BLAZING fast" performance

---

## LIVEPEER STREAM CONFIGURATION ISSUE

**Current Problem:** Stream key `7de0-7v24-76co-mvbd` returns "Stream open failed"
**Diagnosis:** 
- RTMP connection succeeds (TCP connects to 195.181.169.130:1935)
- Stream key appears invalid/expired
- FFmpeg successfully sends data but Livepeer rejects stream

**Fix Required:** Update/regenerate Livepeer stream credentials before testing latency optimizations.

---

*Analysis completed: 2025-08-11*
*Status: Ready for ultra-low latency implementation*