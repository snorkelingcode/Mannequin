'use client'

import { useState } from 'react'
import LivepeerPlayer from '../components/LivepeerPlayer'
import { PrimaryControls, SecondaryControls } from '../components/MannequinControls'
import { useWebSocket } from '../hooks/useWebSocket'

export default function Home() {
  const [showControls, setShowControls] = useState(true)
  
  // WebSocket connection
  const {
    isConnected,
    isAuthenticated,
    sendCommand
  } = useWebSocket(process.env.NEXT_PUBLIC_WEBSOCKET_URL || 'ws://localhost:8080')
  
  return (
    <main className="min-h-screen p-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <header className="text-center mb-8">
          <h1 className="text-5xl font-bold bg-gradient-to-r from-primary-300 to-primary-500 bg-clip-text text-transparent mb-4">
            Mannequin Beta
          </h1>
          <p className="text-xl text-neutral-200">
            Interactive Metahuman Customization Platform
          </p>
          <p className="text-sm text-neutral-400 mt-2">
            All changes appear globally. When you make a change, everyone sees it in real-time. Let's see what we can create!
          </p>
        </header>
      
        {/* Main Layout */}
        {showControls ? (
          <div className="grid gap-6 lg:grid-cols-2 transition-all duration-300">
            {/* Left Column - Video + Some Controls */}
            <div className="space-y-6">
              <LivepeerPlayer className="w-full" />
              
              {/* Primary Controls under video */}
              <div className="space-y-6">
                <SecondaryControls 
                  sendCommand={sendCommand} 
                  isConnected={isConnected && isAuthenticated} 
                />
              </div>
            </div>
            
            {/* Right Column - Main Controls */}
            <div className="space-y-6">
              <PrimaryControls 
                sendCommand={sendCommand} 
                isConnected={isConnected && isAuthenticated} 
              />
            </div>
          </div>
        ) : (
          /* Full width video when controls hidden */
          <div className="max-w-4xl mx-auto">
            <LivepeerPlayer className="w-full" />
          </div>
        )}
        
        {/* Feature Highlights */}
        {!showControls && (
          <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="card text-center">
              <div className="text-4xl mb-3">🎮</div>
              <h3 className="text-lg font-semibold text-primary-300 mb-2">Real-time Controls</h3>
              <p className="text-neutral-300 text-sm">
                Customize your mannequin in real-time with camera controls, facial expressions, and body modifications.
              </p>
            </div>
            
            <div className="card text-center">
              <div className="text-4xl mb-3">🚀</div>
              <h3 className="text-lg font-semibold text-primary-300 mb-2">Ultra-Low Latency</h3>
              <p className="text-neutral-300 text-sm">
                Sub-3 second streaming latency using WebRTC and optimized pipeline from Unreal Engine to Livepeer.
              </p>
            </div>
            
            <div className="card text-center">
              <div className="text-4xl mb-3">🔒</div>
              <h3 className="text-lg font-semibold text-primary-300 mb-2">Secure Bridge</h3>
              <p className="text-neutral-300 text-sm">
                Hacker-proof WebSocket bridge with authentication, rate limiting, and command validation.
              </p>
            </div>
          </div>
        )}
        
        {/* Footer */}
        <footer className="mt-12 text-center text-neutral-400 text-sm">
          <p> 
            Powered by Unreal Engine 5.5 • 
            Streamed via Livepeer • 
            Deployed on Vercel •
            An Embody Product
          </p>
        </footer>
      </div>
    </main>
  )
}