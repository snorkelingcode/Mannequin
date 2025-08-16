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
  
  const { isConnected, isAuthenticated, sendMessage, connectionStatus, error, onMessage } = useWebSocket(websocketUrl)
  
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
      // Format message with custom GPT prompt
      const formattedMessage = `${message} - Hey GPT, use a twitch streaming e girl as the personality for this response, make it one text block with no emojis, and grammer when emotion needs to be communicated through text`
      
      // Send chat message through WebSocket
      const success = await sendMessage(JSON.stringify({
        type: 'chat',
        message: formattedMessage
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
    const unsubscribe = onMessage(async (data) => {
      if (data.type === 'chat_response' && data.ai_response) {
        const aiMessage: ChatMessage = {
          id: Date.now().toString(),
          type: 'ai',
          message: data.ai_response,
          timestamp: new Date()
        }
        
        setMessages(prev => [...prev, aiMessage])
        setIsTyping(false)
        
        // Send AI response to text-to-face receiver via ngrok
        // Get current ngrok URL dynamically through our API
        let textToFaceUrl = null
        try {
          const ngrokResponse = await fetch('/api/ngrok-url')
          const ngrokData = await ngrokResponse.json()
          if (ngrokData.status === 'success' && ngrokData.url) {
            textToFaceUrl = `${ngrokData.url}/chat_response`
          }
        } catch (error) {
          console.log('Could not get ngrok URL dynamically, skipping text-to-face')
        }

        // Fallback to current ngrok URL if dynamic detection fails
        if (!textToFaceUrl) {
          textToFaceUrl = 'https://5936064b6245.ngrok.app/chat_response'
        }

        if (textToFaceUrl) {
          try {
            await fetch(textToFaceUrl, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                text: data.ai_response
              })
            })
            console.log('Sent to text-to-face receiver via ngrok:', textToFaceUrl)
          } catch (error) {
            console.log('Text-to-face receiver not available:', error)
          }
        } else {
          console.log('No ngrok tunnel found for text-to-face')
        }
      }
    })
    
    return unsubscribe
  }, [onMessage])
  
  return (
    <div className={clsx('bg-neutral-900 rounded-lg border border-neutral-700 overflow-hidden', className)}>
      {/* Header */}
      <div className="flex items-center justify-between p-3 border-b border-neutral-700 bg-neutral-800">
        <div className="flex items-center space-x-2">
          <ChatBubbleLeftRightIcon className="h-5 w-5 text-purple-400" />
          <h3 className="text-sm font-semibold text-white">Stream Chat</h3>
        </div>
      </div>
      
      {/* Messages */}
      <div className="h-64 overflow-y-auto p-3 space-y-2 bg-neutral-900 chat-scrollbar">
        {messages.length === 0 && (
          <div className="text-center text-neutral-500 py-8">
            <ChatBubbleLeftRightIcon className="h-8 w-8 mx-auto mb-2 text-neutral-600" />
            <p className="text-sm">Chat with the AI streamer!</p>
          </div>
        )}
        
        {messages.map((msg) => (
          <div key={msg.id} className="flex items-start space-x-2">
            <div className={clsx(
              'w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold',
              msg.type === 'user' 
                ? 'bg-blue-600 text-white' 
                : 'bg-purple-600 text-white'
            )}>
              {msg.type === 'user' ? 'U' : 'AI'}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center space-x-2 mb-1">
                <span className={clsx(
                  'text-sm font-semibold',
                  msg.type === 'user' ? 'text-blue-400' : 'text-purple-400'
                )}>
                  {msg.type === 'user' ? 'You' : 'AI Streamer'}
                </span>
                <span className="text-xs text-neutral-500">
                  {msg.timestamp.toLocaleTimeString()}
                </span>
              </div>
              <p className="text-sm text-neutral-300 break-words">
                {msg.message}
              </p>
            </div>
          </div>
        ))}
        
        {isTyping && (
          <div className="flex items-start space-x-2">
            <div className="w-6 h-6 rounded-full bg-purple-600 flex items-center justify-center text-xs font-bold text-white">
              AI
            </div>
            <div className="flex-1">
              <div className="flex items-center space-x-2 mb-1">
                <span className="text-sm font-semibold text-purple-400">AI Streamer</span>
              </div>
              <div className="flex space-x-1">
                <div className="h-2 w-2 bg-neutral-500 rounded-full animate-bounce" />
                <div className="h-2 w-2 bg-neutral-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                <div className="h-2 w-2 bg-neutral-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      {/* Input */}
      <div className="border-t border-neutral-700 p-3 bg-neutral-800">
        {error && (
          <div className="mb-2 p-2 bg-red-900/50 border border-red-700 text-red-300 rounded text-xs">
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
            placeholder={isAuthenticated ? "Say something..." : "Connecting..."}
            disabled={!isAuthenticated}
            className="flex-1 bg-neutral-700 border border-neutral-600 rounded px-3 py-2 text-white placeholder-neutral-400 text-sm focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent disabled:bg-neutral-800 disabled:text-neutral-500"
            maxLength={200}
          />
          <button
            onClick={sendChatMessage}
            disabled={!inputMessage.trim() || !isAuthenticated}
            className="bg-purple-600 text-white rounded px-3 py-2 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 focus:ring-offset-neutral-800 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <PaperAirplaneIcon className="h-4 w-4" />
          </button>
        </div>
        
        <div className="mt-2 text-xs text-neutral-500">
          {inputMessage.length}/200 characters
        </div>
      </div>
      
      <style jsx global>{`
        .chat-scrollbar::-webkit-scrollbar {
          width: 6px;
        }
        .chat-scrollbar::-webkit-scrollbar-track {
          background: #262626;
        }
        .chat-scrollbar::-webkit-scrollbar-thumb {
          background: #525252;
          border-radius: 3px;
        }
        .chat-scrollbar::-webkit-scrollbar-thumb:hover {
          background: #737373;
        }
      `}</style>
    </div>
  )
}