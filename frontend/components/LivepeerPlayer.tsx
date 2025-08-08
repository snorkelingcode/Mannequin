'use client'

import { useState } from 'react'

interface LivepeerPlayerProps {
  className?: string
}

const STREAM_CONFIG = {
  PLAYBACK_ID: '7de0lr18mu0sassl',
  IFRAME_URL: 'https://lvpr.tv?v=7de0lr18mu0sassl'
}

export default function LivepeerPlayer({ className = '' }: LivepeerPlayerProps) {
  const [isStreamLoaded, setIsStreamLoaded] = useState(false)
  
  return (
    <div className={`card ${className}`}>
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-primary-400 mb-2">🚀 Live Mannequin Stream</h2>
        <p className="text-dark-300">Ultra-low latency streaming from Unreal Engine 5.5</p>
      </div>
      
      {/* Livepeer Stream Iframe */}
      <div className="relative bg-black rounded-lg overflow-hidden mb-4 aspect-video">
        <iframe 
          src={STREAM_CONFIG.IFRAME_URL}
          className="w-full h-full"
          frameBorder="0"
          allowFullScreen
          allow="autoplay; encrypted-media; picture-in-picture"
          sandbox="allow-same-origin allow-scripts"
          onLoad={() => setIsStreamLoaded(true)}
        />
      </div>
      
      {/* Status Indicator */}
      <div className="flex items-center justify-center space-x-3 mb-4">
        <div className={`w-3 h-3 rounded-full ${isStreamLoaded ? 'bg-green-500 animate-pulse-slow' : 'bg-yellow-500'}`}></div>
        <span className="text-dark-300">
          {isStreamLoaded ? 'Stream loaded and ready' : 'Loading stream player...'}
        </span>
      </div>
      
      {/* Stream Info */}
      <div className="mt-6 text-sm text-dark-400 space-y-1">
        <div><strong>Stream ID:</strong> 7de094b8-3fbe-4b16-ac75-594556d39b18</div>
        <div><strong>Playback ID:</strong> {STREAM_CONFIG.PLAYBACK_ID}</div>
        <div><strong>Resolution:</strong> 1280x720 @ 30fps</div>
        <div><strong>Player:</strong> Livepeer Embedded Player</div>
        <div><strong>Latency:</strong> Ultra-low via WebRTC/HLS adaptive</div>
      </div>
      
      {/* Stream Pipeline Info */}
      <div className="mt-4 p-4 bg-dark-700/30 rounded-lg">
        <h4 className="text-sm font-semibold text-primary-400 mb-2">🔄 Stream Pipeline</h4>
        <div className="flex items-center justify-center space-x-2 text-xs">
          <span className="px-2 py-1 bg-blue-500/20 text-blue-400 rounded">Unreal Engine</span>
          <span className="text-dark-400">→</span>
          <span className="px-2 py-1 bg-purple-500/20 text-purple-400 rounded">WebRTC Bridge</span>
          <span className="text-dark-400">→</span>
          <span className="px-2 py-1 bg-green-500/20 text-green-400 rounded">Livepeer</span>
          <span className="text-dark-400">→</span>
          <span className="px-2 py-1 bg-primary-500/20 text-primary-400 rounded">Your Browser</span>
        </div>
      </div>
    </div>
  )
}