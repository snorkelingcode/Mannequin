'use client'

import { useState, useEffect, useRef, useCallback } from 'react'

interface WebSocketMessage {
  type: string
  message?: string
  command?: string
  clientId?: string
  details?: string
}

interface UseWebSocketReturn {
  isConnected: boolean
  isAuthenticated: boolean
  sendCommand: (command: string) => Promise<boolean>
  connectionStatus: string
  error: string | null
  connect: () => void
  disconnect: () => void
}

export function useWebSocket(url: string): UseWebSocketReturn {
  const [isConnected, setIsConnected] = useState(false)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState('Disconnected')
  const [error, setError] = useState<string | null>(null)
  
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const authTokenRef = useRef<string | null>(null)
  
  const connect = useCallback(async () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return
    }
    
    try {
      setConnectionStatus('Connecting...')
      setError(null)
      
      // Get authentication token
      if (!authTokenRef.current) {
        const response = await fetch('/api/auth', { method: 'POST' })
        const { token } = await response.json()
        authTokenRef.current = token
      }
      
      const ws = new WebSocket(url)
      wsRef.current = ws
      
      ws.onopen = () => {
        setIsConnected(true)
        setConnectionStatus('Connected')
        
        // Authenticate immediately after connection
        if (authTokenRef.current) {
          ws.send(JSON.stringify({
            type: 'auth',
            token: authTokenRef.current
          }))
        }
      }
      
      ws.onmessage = (event) => {
        try {
          const data: WebSocketMessage = JSON.parse(event.data)
          
          switch (data.type) {
            case 'welcome':
              setConnectionStatus(`Connected - ${data.message}`)
              break
              
            case 'auth_success':
              setIsAuthenticated(true)
              setConnectionStatus('Authenticated & Ready')
              break
              
            case 'auth_failed':
              setIsAuthenticated(false)
              setError(`Authentication failed: ${data.message}`)
              setConnectionStatus('Authentication Failed')
              break
              
            case 'success':
              // Command sent successfully
              break
              
            case 'error':
              setError(`Error: ${data.message}`)
              break
              
            default:
              console.log('Unknown message type:', data)
          }
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err)
        }
      }
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
        setError('Connection error occurred')
        setConnectionStatus('Connection Error')
      }
      
      ws.onclose = (event) => {
        setIsConnected(false)
        setIsAuthenticated(false)
        
        if (event.wasClean) {
          setConnectionStatus('Disconnected')
        } else {
          setConnectionStatus('Connection Lost')
          setError('Connection lost unexpectedly')
          
          // Auto-reconnect after 5 seconds
          reconnectTimeoutRef.current = setTimeout(() => {
            connect()
          }, 5000)
        }
      }
      
    } catch (err) {
      setError(`Failed to connect: ${err}`)
      setConnectionStatus('Connection Failed')
    }
  }, [url])
  
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }
    
    if (wsRef.current) {
      wsRef.current.close(1000, 'User requested disconnect')
      wsRef.current = null
    }
    
    setIsConnected(false)
    setIsAuthenticated(false)
    setConnectionStatus('Disconnected')
    setError(null)
  }, [])
  
  const sendCommand = useCallback(async (command: string): Promise<boolean> => {
    if (!wsRef.current || !isConnected || !isAuthenticated) {
      setError('Not connected or authenticated')
      return false
    }
    
    try {
      wsRef.current.send(JSON.stringify({
        type: 'command',
        command: command
      }))
      
      return true
    } catch (err) {
      setError(`Failed to send command: ${err}`)
      return false
    }
  }, [isConnected, isAuthenticated])
  
  useEffect(() => {
    connect()
    
    return () => {
      disconnect()
    }
  }, [connect, disconnect])
  
  return {
    isConnected,
    isAuthenticated,
    sendCommand,
    connectionStatus,
    error,
    connect,
    disconnect
  }
}