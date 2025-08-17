'use client'

import { useState, useEffect, useRef, useCallback } from 'react'

interface WebSocketMessage {
  type: string
  message?: string
  command?: string
  clientId?: string
  details?: string
  user_message?: string
  ai_response?: string
}

interface UseWebSocketReturn {
  isConnected: boolean
  isAuthenticated: boolean
  sendCommand: (command: string) => Promise<boolean>
  sendMessage: (message: string) => Promise<boolean>
  connectionStatus: string
  error: string | null
  connect: () => void
  disconnect: () => void
  onMessage: (callback: (data: WebSocketMessage) => void) => void
}

export function useWebSocket(url: string): UseWebSocketReturn {
  const [isConnected, setIsConnected] = useState(false)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState('Disconnected')
  const [error, setError] = useState<string | null>(null)
  
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const authTokenRef = useRef<string | null>(null)
  const messageCallbacksRef = useRef<((data: WebSocketMessage) => void)[]>([])
  
  const connect = useCallback(async () => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return
    }
    
    try {
      setConnectionStatus('Connecting...')
      setError(null)
      
      // Get authentication token
      if (!authTokenRef.current) {
        // Authentication in progress
        const response = await fetch('/api/auth', { method: 'POST' })
        if (!response.ok) {
          throw new Error(`Auth failed: ${response.status} ${response.statusText}`)
        }
        const data = await response.json()
        // Auth response received
        if (!data.token) {
          throw new Error('No token received from auth endpoint')
        }
        authTokenRef.current = data.token
        // Token obtained
      }
      
      // Connecting to WebSocket
      const ws = new WebSocket(url)
      wsRef.current = ws
      
      ws.onopen = () => {
        // WebSocket connected
        setIsConnected(true)
        setConnectionStatus('Connected')
        
        // Authenticate immediately after connection
        if (authTokenRef.current) {
          // Sending authentication
          ws.send(JSON.stringify({
            type: 'auth',
            token: authTokenRef.current
          }))
        }
      }
      
      ws.onmessage = (event) => {
        try {
          const data: WebSocketMessage = JSON.parse(event.data)
          
          // Call all registered callbacks
          messageCallbacksRef.current.forEach(callback => {
            try {
              callback(data)
            } catch (err) {
              console.error('Error in message callback:', err)
            }
          })
          
          switch (data.type) {
            case 'welcome':
              setConnectionStatus(`Connected - ${data.message}`)
              break
              
            case 'auth_success':
              // Authentication successful
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
              
            case 'chat_response':
              // Chat response handled by callbacks
              break
              
            default:
              // Received unknown message type
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
    // Sending command
    
    if (!wsRef.current || !isConnected || !isAuthenticated) {
      console.error('Cannot send command - not connected or authenticated')
      setError('Not connected or authenticated')
      return false
    }
    
    try {
      // Command being sent
      wsRef.current.send(JSON.stringify({
        type: 'command',
        command: command
      }))
      
      return true
    } catch (err) {
      console.error('Failed to send command:', err)
      setError(`Failed to send command: ${err}`)
      return false
    }
  }, [isConnected, isAuthenticated])

  const sendMessage = useCallback(async (message: string): Promise<boolean> => {
    if (!wsRef.current || !isConnected || !isAuthenticated) {
      setError('Not connected or authenticated')
      return false
    }

    try {
      wsRef.current.send(message)
      return true
    } catch (err) {
      setError(`Failed to send message: ${err}`)
      return false
    }
  }, [isConnected, isAuthenticated])

  const onMessage = useCallback((callback: (data: WebSocketMessage) => void) => {
    messageCallbacksRef.current.push(callback)
    
    return () => {
      messageCallbacksRef.current = messageCallbacksRef.current.filter(cb => cb !== callback)
    }
  }, [])
  
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
    sendMessage,
    connectionStatus,
    error,
    connect,
    disconnect,
    onMessage
  }
}