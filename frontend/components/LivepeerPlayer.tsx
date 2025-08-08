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
      
      
    </div>
  )
}