'use client'

import { useState } from 'react'
import LivepeerPlayer from '../components/LivepeerPlayer'
import MannequinControls from '../components/MannequinControls'
import { useWebSocket } from '../hooks/useWebSocket'

export default function Home() {
  const [showControls, setShowControls] = useState(true)
  
  // WebSocket connection
  const {
    isConnected,
    isAuthenticated,
    sendCommand,
    connectionStatus,
    error,
    connect,
    disconnect
  } = useWebSocket(process.env.NEXT_PUBLIC_WEBSOCKET_URL || 'ws://localhost:8080')
  
  return (
    <main className="min-h-screen p-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <header className="text-center mb-8">
          <h1 className="text-5xl font-bold bg-gradient-to-r from-primary-400 to-primary-600 bg-clip-text text-transparent mb-4">
            Mannequin
          </h1>
          <p className="text-xl text-dark-300">
            Interactive 3D Character Customization Platform
          </p>
          <p className="text-sm text-dark-400 mt-2">
            Powered by Unreal Engine 5.5 • Streamed via Livepeer • Secured WebSocket Bridge
          </p>
        </header>
        
        {/* Connection Status Banner */}
        {error && (
          <div className="mb-6 p-4 bg-red-500/20 border border-red-500/30 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-red-400 font-semibold">Connection Error</h3>
                <p className="text-red-300 text-sm">{error}</p>
              </div>
              <button
                onClick={connect}
                className="btn-secondary px-4 py-2 text-sm"
              >
                🔄 Retry
              </button>
            </div>
          </div>
        )}
        
        <div className="mb-6 card">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className={`flex items-center space-x-2 px-3 py-2 rounded-full ${
                isConnected ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
              }`}>
                <div className={`w-2 h-2 rounded-full ${
                  isConnected ? 'bg-green-400 animate-pulse' : 'bg-red-400'
                }`}></div>
                <span className="text-sm font-medium">{connectionStatus}</span>
              </div>
              
              {isConnected && (
                <div className={`flex items-center space-x-2 px-3 py-2 rounded-full ${
                  isAuthenticated ? 'bg-blue-500/20 text-blue-400' : 'bg-yellow-500/20 text-yellow-400'
                }`}>
                  <div className={`w-2 h-2 rounded-full ${
                    isAuthenticated ? 'bg-blue-400' : 'bg-yellow-400 animate-pulse'
                  }`}></div>
                  <span className="text-sm font-medium">
                    {isAuthenticated ? 'Authenticated' : 'Authenticating...'}
                  </span>
                </div>
              )}
            </div>
            
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setShowControls(!showControls)}
                className="btn-secondary px-4 py-2 text-sm"
              >
                {showControls ? '🎮 Hide Controls' : '🎮 Show Controls'}
              </button>
              
              {isConnected ? (
                <button
                  onClick={disconnect}
                  className="btn-secondary px-4 py-2 text-sm"
                >
                  🔌 Disconnect
                </button>
              ) : (
                <button
                  onClick={connect}
                  className="btn-primary px-4 py-2 text-sm"
                >
                  🔌 Connect
                </button>
              )}
            </div>
          </div>
        </div>
        
        {/* Main Layout */}
        <div className={`grid gap-6 ${showControls ? 'lg:grid-cols-2' : 'lg:grid-cols-1'} transition-all duration-300`}>
          {/* Video Player - Full width when controls are hidden */}
          <div className={`${showControls ? '' : 'lg:col-span-1 max-w-4xl mx-auto'}`}>
            <LivepeerPlayer className="h-full" />
            
            {/* Stream Pipeline Info */}
            <div className="mt-4 card">
              <h3 className="text-lg font-semibold text-primary-400 mb-3">🔄 Stream Pipeline</h3>
              <div className="flex items-center justify-center space-x-2 text-sm">
                <span className="px-2 py-1 bg-blue-500/20 text-blue-400 rounded">End User</span>
                <span className="text-dark-400">→</span>
                <span className="px-2 py-1 bg-green-500/20 text-green-400 rounded">Vercel App</span>
                <span className="text-dark-400">→</span>
                <span className="px-2 py-1 bg-purple-500/20 text-purple-400 rounded">WebSocket Bridge</span>
                <span className="text-dark-400">→</span>
                <span className="px-2 py-1 bg-orange-500/20 text-orange-400 rounded">Unreal Engine</span>
                <span className="text-dark-400">→</span>
                <span className="px-2 py-1 bg-primary-500/20 text-primary-400 rounded">Livepeer Stream</span>
              </div>
            </div>
          </div>
          
          {/* Controls Panel - Hide when showControls is false */}
          {showControls && (
            <div className="space-y-6">
              <MannequinControls 
                sendCommand={sendCommand} 
                isConnected={isConnected && isAuthenticated} 
              />
            </div>
          )}
        </div>
        
        {/* Feature Highlights */}
        {!showControls && (
          <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="card text-center">
              <div className="text-4xl mb-3">🎮</div>
              <h3 className="text-lg font-semibold text-primary-400 mb-2">Real-time Controls</h3>
              <p className="text-dark-300 text-sm">
                Customize your mannequin in real-time with camera controls, facial expressions, and body modifications.
              </p>
            </div>
            
            <div className="card text-center">
              <div className="text-4xl mb-3">🚀</div>
              <h3 className="text-lg font-semibold text-primary-400 mb-2">Ultra-Low Latency</h3>
              <p className="text-dark-300 text-sm">
                Sub-3 second streaming latency using WebRTC and optimized pipeline from Unreal Engine to Livepeer.
              </p>
            </div>
            
            <div className="card text-center">
              <div className="text-4xl mb-3">🔒</div>
              <h3 className="text-lg font-semibold text-primary-400 mb-2">Secure Bridge</h3>
              <p className="text-dark-300 text-sm">
                Hacker-proof WebSocket bridge with authentication, rate limiting, and command validation.
              </p>
            </div>
          </div>
        )}
        
        {/* Footer */}
        <footer className="mt-12 text-center text-dark-400 text-sm">
          <p>
            Built with Next.js, TypeScript, Tailwind CSS • 
            Powered by Unreal Engine 5.5 • 
            Streamed via Livepeer • 
            Deployed on Vercel
          </p>
        </footer>
      </div>
    </main>
  )
}