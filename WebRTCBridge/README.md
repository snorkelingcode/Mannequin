# Unreal Engine to Livepeer RTMP Bridge

A high-performance, ultra-low latency streaming solution that captures video from Unreal Engine 5.5 and streams directly to Livepeer via RTMP.

## 🎯 Current Status

**✅ WORKING SOLUTION:**
- **Ultra-fast performance**: Direct JPEG passthrough for maximum speed
- **100% frame success rate**: Reliable frame delivery with retry mechanisms  
- **Stable RTMP streaming**: Direct connection to Livepeer RTMP endpoints
- **Minimal dependencies**: Uses only Python standard library + FFmpeg

## 📁 Project Structure

```
C:\WebRTCBridge\
├── correct_rtmp_bridge.py           # Main working bridge (STABLE)
├── livepeer_player.html             # Test playback interface
├── livepeerCredentials.txt          # Livepeer API keys and URLs
├── livepeerDocumentation.txt        # Livepeer API reference
├── claude_continuation_prompt_updated.txt  # Project context for AI assistance
├── logs.txt                         # Performance logs and diagnostics
├── requirements.txt                 # Dependencies (minimal)
└── README.md                        # This file
```

## 🚀 Quick Start

### 1. Prerequisites

```powershell
# Install FFmpeg (required)
# Download from https://ffmpeg.org/download.html
# Make sure ffmpeg.exe is in your PATH
ffmpeg -version  # Verify installation
```

### 2. Run the Bridge

```powershell
cd C:\WebRTCBridge
python correct_rtmp_bridge.py
```

### 3. Start Unreal Engine Streaming

1. Open your UE5.5 project with WebRTCBridgeComponent
2. Set the camera target and UDP port 5000
3. Press Play to start streaming
4. Watch the bridge logs for frame success rates

## 🔧 Bridge Configuration

The bridge uses hardcoded Livepeer credentials and connects to:
- **UDP Port**: 5000 (receives Unreal Engine frames)
- **RTMP URL**: `rtmp://rtmp.livepeer.com/live/7de0-7v24-76co-mvbd`
- **Playback**: `https://livepeercdn.studio/hls/7de0lr18mu0sassl/index.m3u8`

## 📊 Performance Characteristics

- **Frame Rate**: ~25-30 FPS (matches Unreal Engine output)
- **Latency**: Ultra-low (direct JPEG passthrough)
- **Success Rate**: 100% during stable operation
- **Protocol**: UDP chunked frames with automatic reassembly
- **Quality**: Raw JPEG from Unreal Engine (no recompression)

## 🏗️ Architecture

```
Unreal Engine 5.5
    ↓ UDP port 5000 (JPEG chunks)
correct_rtmp_bridge.py
    ↓ Frame reassembly
    ↓ Direct JPEG passthrough  
    ↓ FFmpeg RTMP encoding
Livepeer RTMP Endpoint
    ↓ Live transcoding
HLS/WebRTC Playback
```

## 🔍 Monitoring

The bridge provides real-time statistics every 3 seconds:

```
HIGH-PERFORMANCE Bridge Statistics:
   Runtime: 15.0s
   UDP packets: 1250
   Frames assembled: 125 (rate: 25.0/s)
   RTMP frames sent: 125  
   Frame success rate: 100.0%
   EXCELLENT: 99%+ frame success rate!
```

## 🛠️ Key Features

- **Zero Processing Overhead**: Direct JPEG passthrough for maximum performance
- **Automatic Recovery**: FFmpeg process restart on failures
- **Comprehensive Logging**: Detailed frame statistics and error reporting
- **Stable Architecture**: Proven reliable performance foundation
- **UDP Frame Assembly**: Handles Unreal Engine's chunked protocol correctly

## 📝 Notes

- **No Color Correction**: Current stable version prioritizes performance over color accuracy
- **Minimal Dependencies**: No NumPy, PIL, or other heavy libraries
- **Windows Optimized**: Tested and optimized for Windows environment
- **Production Ready**: Handles real-world streaming scenarios reliably

## 🚨 Troubleshooting

**Port already in use:**
```powershell
netstat -an | findstr :5000
# Kill any processes using port 5000
```

**FFmpeg not found:**
```powershell
# Ensure FFmpeg is installed and in PATH
where ffmpeg
```

**Low frame success rate:**
- Check network connectivity
- Verify Unreal Engine is streaming
- Check logs.txt for detailed diagnostics

## 🎥 Testing Playback

Open `livepeer_player.html` in a browser to test the stream playback.

---

This bridge represents a stable, high-performance solution optimized for reliability and speed over feature complexity.