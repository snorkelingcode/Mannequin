# Frontend Integration for Chat-to-Face Pipeline

## Overview
This document outlines how to integrate chat functionality into your Next.js frontend that works with the websocket-bridge and text-to-face system.

## Required Dependencies
Add these to your `package.json`:

```json
{
  "dependencies": {
    "@heroicons/react": "^2.0.18",
    "clsx": "^2.0.0"
  }
}
```

## Component Structure

### 1. Create Chat Component

Create `components/ChatInterface.tsx`:

```typescript
'use client'

import { useState, useRef, useEffect } from 'react'
import { useWebSocket } from '../hooks/useWebSocket'
import { PaperAirplaneIcon, ChatBubbleLeftRightIcon } from '@heroicons/react/24/outline'
import clsx from 'clsx'

interface ChatMessage {
  id: string
  type: 'user' | 'ai'
  message: string
  timestamp: Date
}

interface ChatInterfaceProps {
  websocketUrl: string
  className?: string
}

export function ChatInterface({ websocketUrl, className }: ChatInterfaceProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputMessage, setInputMessage] = useState('')
  const [isTyping, setIsTyping] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  
  const { isConnected, isAuthenticated, sendMessage, connectionStatus, error } = useWebSocket(websocketUrl)
  
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }
  
  useEffect(() => {
    scrollToBottom()
  }, [messages])
  
  const sendChatMessage = async () => {
    const message = inputMessage.trim()
    if (!message || !isAuthenticated) return
    
    // Add user message to chat
    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      type: 'user',
      message: message,
      timestamp: new Date()
    }
    
    setMessages(prev => [...prev, userMessage])
    setInputMessage('')
    setIsTyping(true)
    
    try {
      // Send chat message through WebSocket
      const success = await sendMessage(JSON.stringify({
        type: 'chat',
        message: message
      }))
      
      if (!success) {
        throw new Error('Failed to send message')
      }
    } catch (err) {
      console.error('Failed to send chat message:', err)
      setIsTyping(false)
    }
  }
  
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendChatMessage()
    }
  }
  
  // Listen for AI responses
  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data)
        
        if (data.type === 'chat_response' && data.ai_response) {
          const aiMessage: ChatMessage = {
            id: Date.now().toString(),
            type: 'ai',
            message: data.ai_response,
            timestamp: new Date()
          }
          
          setMessages(prev => [...prev, aiMessage])
          setIsTyping(false)
        }
      } catch (err) {
        console.error('Error parsing WebSocket message:', err)
      }
    }
    
    // This would need to be connected to your WebSocket instance
    // You might need to modify useWebSocket to expose the raw WebSocket
    
  }, [])
  
  return (
    <div className={clsx('flex flex-col h-full bg-white rounded-lg shadow-lg', className)}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200">
        <div className="flex items-center space-x-2">
          <ChatBubbleLeftRightIcon className="h-6 w-6 text-purple-600" />
          <h3 className="text-lg font-semibold text-gray-900">AI Chat</h3>
        </div>
        <div className="flex items-center space-x-2">
          <div className={clsx(
            'h-2 w-2 rounded-full',
            isAuthenticated ? 'bg-green-500' : 'bg-red-500'
          )} />
          <span className="text-sm text-gray-600">{connectionStatus}</span>
        </div>
      </div>
      
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 py-8">
            <ChatBubbleLeftRightIcon className="h-12 w-12 mx-auto mb-4 text-gray-300" />
            <p>Start a conversation with the AI!</p>
          </div>
        )}
        
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={clsx(
              'flex',
              msg.type === 'user' ? 'justify-end' : 'justify-start'
            )}
          >
            <div
              className={clsx(
                'max-w-xs lg:max-w-md px-4 py-2 rounded-lg',
                msg.type === 'user'
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-200 text-gray-900'
              )}
            >
              <p className="text-sm">{msg.message}</p>
              <p className={clsx(
                'text-xs mt-1',
                msg.type === 'user' ? 'text-purple-200' : 'text-gray-500'
              )}>
                {msg.timestamp.toLocaleTimeString()}
              </p>
            </div>
          </div>
        ))}
        
        {isTyping && (
          <div className="flex justify-start">
            <div className="bg-gray-200 text-gray-900 px-4 py-2 rounded-lg">
              <div className="flex space-x-1">
                <div className="h-2 w-2 bg-gray-500 rounded-full animate-bounce" />
                <div className="h-2 w-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                <div className="h-2 w-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      {/* Input */}
      <div className="border-t border-gray-200 p-4">
        {error && (
          <div className="mb-2 p-2 bg-red-100 border border-red-300 text-red-700 rounded text-sm">
            {error}
          </div>
        )}
        
        <div className="flex space-x-2">
          <input
            ref={inputRef}
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={isAuthenticated ? "Type your message..." : "Connecting..."}
            disabled={!isAuthenticated}
            className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-purple-600 focus:border-transparent disabled:bg-gray-100"
            maxLength={500}
          />
          <button
            onClick={sendChatMessage}
            disabled={!inputMessage.trim() || !isAuthenticated}
            className="bg-purple-600 text-white rounded-lg px-4 py-2 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-600 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <PaperAirplaneIcon className="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  )
}
```

### 2. Update useWebSocket Hook

Modify `hooks/useWebSocket.ts` to handle chat messages:

```typescript
// Add this to the WebSocketMessage interface
interface WebSocketMessage {
  type: string
  message?: string
  command?: string
  clientId?: string
  details?: string
  user_message?: string    // NEW
  ai_response?: string     // NEW
}

// Add this to the UseWebSocketReturn interface
interface UseWebSocketReturn {
  isConnected: boolean
  isAuthenticated: boolean
  sendCommand: (command: string) => Promise<boolean>
  sendMessage: (message: string) => Promise<boolean>  // NEW
  connectionStatus: string
  error: string | null
  connect: () => void
  disconnect: () => void
  onMessage: (callback: (data: WebSocketMessage) => void) => void  // NEW
}

// Add these to your useWebSocket function
const messageCallbacksRef = useRef<((data: WebSocketMessage) => void)[]>([])

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

// Update the ws.onmessage handler to call callbacks
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
    
    // ... existing switch statement ...
  } catch (err) {
    console.error('Failed to parse WebSocket message:', err)
  }
}

// Return the new functions
return {
  isConnected,
  isAuthenticated,
  sendCommand,
  sendMessage,  // NEW
  connectionStatus,
  error,
  connect,
  disconnect,
  onMessage     // NEW
}
```

### 3. Update Main Page

Modify `app/page.tsx` to include the chat interface:

```typescript
'use client'

import { useState } from 'react'
import { MannequinControls } from '../components/MannequinControls'
import { ChatInterface } from '../components/ChatInterface'
import { LivepeerPlayer } from '../components/LivepeerPlayer'

export default function Home() {
  const [activeTab, setActiveTab] = useState<'controls' | 'chat'>('controls')
  const websocketUrl = process.env.NEXT_PUBLIC_WEBSOCKET_URL || 'ws://localhost:8080'
  
  return (
    <main className="min-h-screen bg-gray-100">
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-4xl font-bold text-center mb-8 text-gray-900">
          Mannequin AI
        </h1>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Video Player */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-2xl font-semibold mb-4">Live Stream</h2>
            <LivepeerPlayer />
          </div>
          
          {/* Controls/Chat Panel */}
          <div className="bg-white rounded-lg shadow-lg overflow-hidden">
            {/* Tab Navigation */}
            <div className="flex border-b">
              <button
                onClick={() => setActiveTab('controls')}
                className={`flex-1 py-4 px-6 text-center font-medium ${
                  activeTab === 'controls'
                    ? 'bg-purple-600 text-white'
                    : 'bg-gray-50 text-gray-700 hover:bg-gray-100'
                }`}
              >
                Character Controls
              </button>
              <button
                onClick={() => setActiveTab('chat')}
                className={`flex-1 py-4 px-6 text-center font-medium ${
                  activeTab === 'chat'
                    ? 'bg-purple-600 text-white'
                    : 'bg-gray-50 text-gray-700 hover:bg-gray-100'
                }`}
              >
                AI Chat
              </button>
            </div>
            
            {/* Tab Content */}
            <div className="h-96">
              {activeTab === 'controls' && (
                <div className="h-full overflow-y-auto p-6">
                  <MannequinControls />
                </div>
              )}
              {activeTab === 'chat' && (
                <ChatInterface 
                  websocketUrl={websocketUrl} 
                  className="h-full"
                />
              )}
            </div>
          </div>
        </div>
      </div>
    </main>
  )
}
```

### 4. Environment Configuration

Create/update `.env.local`:

```env
NEXT_PUBLIC_WEBSOCKET_URL=ws://localhost:8080
NEXT_PUBLIC_API_BASE_URL=http://localhost:8080
```

## Testing the Integration

1. Start all services:
   ```bash
   # Terminal 1: Text-to-Face Hook
   cd C:\Users\danek\OneDrive\Desktop\NeuroBuff\neurosync\neurosync_player-main
   python chat_response_hook.py
   
   # Terminal 2: WebSocket Bridge
   cd C:\Users\danek\OneDrive\Desktop\Mannequin\websocket-bridge
   npm start
   
   # Terminal 3: Frontend
   cd C:\Users\danek\OneDrive\Desktop\Mannequin\frontend
   npm run dev
   ```

2. Open browser to `http://localhost:3000`
3. Switch to "AI Chat" tab
4. Wait for "Authenticated & Ready" status
5. Type a message and press Enter
6. Watch for facial animations in Unreal Engine

## Features Included

- Real-time chat interface
- Message history
- Typing indicators
- Connection status display
- Error handling
- Character limit (500 chars)
- Auto-scroll to new messages
- Responsive design
- Tab-based UI integration

## Customization Options

- Modify `EGIRL_PERSONA_PROMPT` in bridge environment
- Adjust ChatGPT model and parameters
- Customize chat UI colors and styling
- Add message filtering/moderation
- Implement user authentication
- Add emoji/reaction support