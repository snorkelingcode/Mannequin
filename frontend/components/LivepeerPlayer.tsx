'use client'

import { useState, useEffect, useRef } from 'react'
import Hls from 'hls.js'

interface LivepeerPlayerProps {
  className?: string
}

const STREAM_CONFIG = {
  PLAYBACK_ID: '7de0lr18mu0sassl',
  HLS_URL: 'https://livepeercdn.studio/hls/7de0lr18mu0sassl/index.m3u8',
  WEBRTC_URL: 'https://livepeer.studio/webrtc/7de0lr18mu0sassl'
}

type Protocol = 'webrtc' | 'hls'
type StreamStatus = 'disconnected' | 'connecting' | 'connected' | 'error'

export default function LivepeerPlayer({ className = '' }: LivepeerPlayerProps) {
  const [protocol, setProtocol] = useState<Protocol>('webrtc')
  const [status, setStatus] = useState<StreamStatus>('disconnected')
  const [statusMessage, setStatusMessage] = useState('Ready to connect')
  
  const videoRef = useRef<HTMLVideoElement>(null)
  const hlsRef = useRef<Hls | null>(null)
  const webrtcRef = useRef<RTCPeerConnection | null>(null)
  
  const updateStatus = (newStatus: StreamStatus, message: string) => {
    setStatus(newStatus)
    setStatusMessage(message)
  }
  
  const startWebRTCStream = async () => {
    try {
      updateStatus('connecting', 'Connecting to WebRTC stream...')
      
      // For now, fallback to HLS since WebRTC requires more complex setup
      // In production, this would use WHEP protocol
      console.log('WebRTC URL:', STREAM_CONFIG.WEBRTC_URL)
      updateStatus('error', 'WebRTC not yet implemented - falling back to HLS')
      await startHLSStream()
      
    } catch (error) {
      console.error('WebRTC connection failed:', error)
      updateStatus('error', 'WebRTC connection failed - trying HLS backup')
      await startHLSStream()
    }
  }
  
  const startHLSStream = async () => {
    try {
      updateStatus('connecting', 'Connecting to HLS stream...')
      
      if (!videoRef.current) {
        throw new Error('Video element not available')
      }
      
      // Cleanup existing HLS instance
      if (hlsRef.current) {
        hlsRef.current.destroy()
        hlsRef.current = null
      }
      
      const video = videoRef.current
      
      if (video.canPlayType('application/vnd.apple.mpegurl')) {
        // Native HLS support (Safari)
        video.src = STREAM_CONFIG.HLS_URL
        video.addEventListener('loadedmetadata', () => {
          updateStatus('connected', 'Stream connected - Playing HLS (Native)')
        })
      } else if (Hls.isSupported()) {
        // Use HLS.js for other browsers
        const hls = new Hls({
          lowLatencyMode: true,
          backBufferLength: 90,
          maxBufferLength: 30,
          maxMaxBufferLength: 60,
          liveSyncDurationCount: 1,
          liveMaxLatencyDurationCount: 3,
          enableWorker: true,
          startLevel: -1, // Auto quality selection
        })
        
        hlsRef.current = hls
        hls.loadSource(STREAM_CONFIG.HLS_URL)
        hls.attachMedia(video)
        
        hls.on(Hls.Events.MANIFEST_PARSED, () => {
          updateStatus('connected', 'Stream connected - Playing HLS (HLS.js)')
          video.play().catch(console.error)
        })
        
        hls.on(Hls.Events.ERROR, (event, data) => {
          console.error('HLS Error:', data)
          if (data.fatal) {
            switch (data.type) {
              case Hls.ErrorTypes.NETWORK_ERROR:
                updateStatus('error', `Network Error: ${data.details}`)
                break
              case Hls.ErrorTypes.MEDIA_ERROR:
                updateStatus('error', `Media Error: ${data.details}`)
                hls.recoverMediaError()
                break
              default:
                updateStatus('error', `HLS Error: ${data.details}`)
                break
            }
          }
        })
        
        hls.on(Hls.Events.BUFFER_APPENDED, () => {
          // Stream is actively buffering
          if (status === 'connecting') {
            updateStatus('connected', 'Stream playing with low latency')
          }
        })
        
      } else {
        throw new Error('HLS not supported in this browser')
      }
      
    } catch (error) {
      console.error('HLS connection failed:', error)
      updateStatus('error', `HLS connection failed: ${error}`)
    }
  }
  
  const startStream = async () => {
    if (protocol === 'webrtc') {
      await startWebRTCStream()
    } else {
      await startHLSStream()
    }
  }
  
  const stopStream = () => {
    if (hlsRef.current) {
      hlsRef.current.destroy()
      hlsRef.current = null
    }
    
    if (webrtcRef.current) {
      webrtcRef.current.close()
      webrtcRef.current = null
    }
    
    if (videoRef.current) {
      videoRef.current.src = ''
    }
    
    updateStatus('disconnected', 'Stream stopped')
  }
  
  const refreshStream = () => {
    stopStream()
    setTimeout(startStream, 1000)
  }
  
  const handleProtocolChange = (newProtocol: Protocol) => {
    setProtocol(newProtocol)
    if (status === 'connected') {
      // Restart with new protocol
      stopStream()
      setTimeout(() => {
        setProtocol(newProtocol)
        startStream()
      }, 500)
    }
  }
  
  // Video event handlers
  const handleVideoEvents = () => {
    const video = videoRef.current
    if (!video) return
    
    video.addEventListener('loadstart', () => {
      if (status === 'connecting') {
        updateStatus('connecting', 'Loading stream...')
      }
    })
    
    video.addEventListener('canplay', () => {
      updateStatus('connected', 'Stream ready - Playing')
    })
    
    video.addEventListener('playing', () => {
      updateStatus('connected', 'Stream playing')
    })
    
    video.addEventListener('error', (e) => {
      updateStatus('error', `Video error: ${e.type}`)
    })
    
    video.addEventListener('stalled', () => {
      updateStatus('connecting', 'Stream stalled - buffering...')
    })
    
    video.addEventListener('waiting', () => {
      updateStatus('connecting', 'Buffering...')
    })
  }
  
  useEffect(() => {
    handleVideoEvents()
    
    // Auto-start stream after component mount
    const timer = setTimeout(() => {
      startStream()
    }, 2000)
    
    return () => {
      clearTimeout(timer)
      stopStream()
    }
  }, [])
  
  const getStatusColor = () => {
    switch (status) {
      case 'connected': return 'bg-green-500'
      case 'connecting': return 'bg-yellow-500'
      case 'error': return 'bg-red-500'
      default: return 'bg-gray-500'
    }
  }
  
  const getLatencyInfo = () => {
    if (protocol === 'webrtc') {
      return <span className="text-green-400 font-semibold">(0.5-3s latency)</span>
    } else {
      return <span className="text-yellow-400 font-semibold">(~10s latency)</span>
    }
  }
  
  return (
    <div className={`card ${className}`}>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-primary-400 mb-2">🚀 Live Mannequin Stream</h2>
        <p className="text-dark-300">Ultra-low latency streaming from Unreal Engine 5.5</p>
      </div>
      
      {/* Protocol Selection */}
      <div className="mb-6 flex justify-center space-x-6">
        <label className="flex items-center space-x-2 cursor-pointer">
          <input
            type="radio"
            name="protocol"
            value="webrtc"
            checked={protocol === 'webrtc'}
            onChange={() => handleProtocolChange('webrtc')}
            className="text-primary-500"
          />
          <span className="text-white font-medium">WebRTC {getLatencyInfo()}</span>
        </label>
        <label className="flex items-center space-x-2 cursor-pointer">
          <input
            type="radio"
            name="protocol"
            value="hls"
            checked={protocol === 'hls'}
            onChange={() => handleProtocolChange('hls')}
            className="text-primary-500"
          />
          <span className="text-white font-medium">HLS {protocol === 'hls' && getLatencyInfo()}</span>
        </label>
      </div>
      
      {/* Video Player */}
      <div className="relative bg-black rounded-lg overflow-hidden mb-4 aspect-video">
        <video
          ref={videoRef}
          className="w-full h-full"
          controls
          autoPlay
          muted
          playsInline
        >
          Your browser does not support the video tag.
        </video>
      </div>
      
      {/* Status Indicator */}
      <div className="flex items-center justify-center space-x-3 mb-4">
        <div className={`w-3 h-3 rounded-full ${getStatusColor()} ${status === 'connected' ? 'animate-pulse-slow' : ''}`}></div>
        <span className="text-dark-300">{statusMessage}</span>
      </div>
      
      {/* Controls */}
      <div className="flex justify-center space-x-4">
        <button
          onClick={startStream}
          className="btn-primary"
          disabled={status === 'connecting'}
        >
          🎯 Start Stream
        </button>
        <button
          onClick={stopStream}
          className="btn-secondary"
        >
          ⏹️ Stop
        </button>
        <button
          onClick={refreshStream}
          className="btn-secondary"
          disabled={status === 'connecting'}
        >
          🔄 Refresh
        </button>
      </div>
      
      {/* Stream Info */}
      <div className="mt-6 text-sm text-dark-400 space-y-1">
        <div><strong>Stream ID:</strong> 7de094b8-3fbe-4b16-ac75-594556d39b18</div>
        <div><strong>Playback ID:</strong> {STREAM_CONFIG.PLAYBOOK_ID}</div>
        <div><strong>Resolution:</strong> 1280x720 @ 30fps</div>
        <div><strong>Current Protocol:</strong> {protocol.toUpperCase()}</div>
      </div>
    </div>
  )
}