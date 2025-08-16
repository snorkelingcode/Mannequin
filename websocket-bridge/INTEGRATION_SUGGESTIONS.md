# WebSocket Bridge Integration for Chat-to-Face Pipeline

## Overview
This document outlines how to integrate the websocket-bridge with ChatGPT and the text-to-face hook system.

## Required Dependencies
Add these to your `package.json`:

```json
{
  "dependencies": {
    "openai": "^4.20.0",
    "axios": "^1.6.0"
  }
}
```

## Environment Variables
Add to your `.env` file:

```env
# ChatGPT Configuration
OPENAI_API_KEY=your-openai-api-key-here
CHATGPT_MODEL=gpt-3.5-turbo
EGIRL_PERSONA_PROMPT="You are a playful, flirty Twitch e-girl personality. Respond with enthusiasm, use cute expressions, and be engaging. Keep responses under 100 words."

# Text-to-Face Hook Configuration
TEXT_TO_FACE_HOOK_URL=http://localhost:8001/chat_response
TEXT_TO_FACE_ENABLED=true
```

## Code Integration

### 1. Add ChatGPT Integration (server.js)

Add these imports at the top:
```javascript
const OpenAI = require('openai');
const axios = require('axios');

// Initialize OpenAI
const openai = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY
});

const EGIRL_PERSONA = process.env.EGIRL_PERSONA_PROMPT || "You are a playful, flirty Twitch e-girl personality. Respond with enthusiasm, use cute expressions, and be engaging. Keep responses under 100 words.";
```

### 2. Add Chat Processing Function

```javascript
async function processUserChat(userMessage) {
    try {
        console.log(`Processing chat: ${userMessage}`);
        
        const completion = await openai.chat.completions.create({
            model: process.env.CHATGPT_MODEL || 'gpt-3.5-turbo',
            messages: [
                {
                    role: 'system',
                    content: EGIRL_PERSONA
                },
                {
                    role: 'user',
                    content: userMessage
                }
            ],
            max_tokens: 150,
            temperature: 0.8
        });

        const response = completion.choices[0].message.content.trim();
        console.log(`ChatGPT response: ${response}`);
        
        // Send to text-to-face hook
        if (process.env.TEXT_TO_FACE_ENABLED === 'true') {
            await sendToTextToFaceHook(response);
        }
        
        return response;
    } catch (error) {
        console.error('Error processing chat:', error);
        throw error;
    }
}

async function sendToTextToFaceHook(text) {
    try {
        const hookUrl = process.env.TEXT_TO_FACE_HOOK_URL || 'http://localhost:8001/chat_response';
        
        const response = await axios.post(hookUrl, {
            text: text
        }, {
            timeout: 5000,
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        console.log(`Text-to-face hook response: ${response.data.message}`);
        return true;
    } catch (error) {
        console.error('Failed to send to text-to-face hook:', error.message);
        return false;
    }
}
```

### 3. Add Chat Message Handler

Add this new message type handler in your WebSocket message handler:

```javascript
// Add this inside the ws.on('message', async (message) => { block after the existing handlers

if (data.type === 'chat') {
    if (!connection || !connection.authenticated) {
        ws.send(JSON.stringify({
            type: 'error',
            message: 'Authentication required'
        }));
        return;
    }
    
    // Validate chat message
    if (!data.message || typeof data.message !== 'string') {
        ws.send(JSON.stringify({
            type: 'error',
            message: 'Invalid chat message format'
        }));
        return;
    }
    
    // Sanitize message
    const userMessage = data.message.trim();
    if (userMessage.length === 0 || userMessage.length > 500) {
        ws.send(JSON.stringify({
            type: 'error',
            message: 'Chat message must be between 1-500 characters'
        }));
        return;
    }
    
    try {
        const aiResponse = await processUserChat(userMessage);
        
        ws.send(JSON.stringify({
            type: 'chat_response',
            message: 'Chat processed successfully',
            user_message: userMessage,
            ai_response: aiResponse
        }));
        
        console.log(`Chat processed for ${clientId}: "${userMessage}" -> "${aiResponse}"`);
    } catch (error) {
        ws.send(JSON.stringify({
            type: 'error',
            message: 'Failed to process chat message',
            details: error.message
        }));
        console.error(`Chat processing failed for ${clientId}:`, error.message);
    }
}
```

### 4. Update Valid Command Patterns

Add this pattern to your VALID_COMMAND_PATTERNS array:
```javascript
/^CHAT_.*$/,  // Allow chat commands
```

## Complete Integration Example

Here's how your message handler should look after integration:

```javascript
ws.on('message', async (message) => {
    try {
        // ... existing rate limiting and connection code ...
        
        const data = JSON.parse(message.toString());
        
        // Handle authentication (existing code)
        if (data.type === 'auth') {
            // ... existing auth code ...
        }
        
        // Handle chat messages (NEW)
        if (data.type === 'chat') {
            if (!connection || !connection.authenticated) {
                ws.send(JSON.stringify({
                    type: 'error',
                    message: 'Authentication required'
                }));
                return;
            }
            
            const userMessage = data.message?.trim();
            if (!userMessage || userMessage.length === 0 || userMessage.length > 500) {
                ws.send(JSON.stringify({
                    type: 'error',
                    message: 'Invalid chat message'
                }));
                return;
            }
            
            try {
                const aiResponse = await processUserChat(userMessage);
                ws.send(JSON.stringify({
                    type: 'chat_response',
                    user_message: userMessage,
                    ai_response: aiResponse
                }));
            } catch (error) {
                ws.send(JSON.stringify({
                    type: 'error',
                    message: 'Chat processing failed'
                }));
            }
            return;
        }
        
        // Handle commands (existing code)
        if (data.type === 'command') {
            // ... existing command code ...
        }
        
    } catch (error) {
        // ... existing error handling ...
    }
});
```

## Testing the Integration

1. Start your text-to-face hook:
   ```bash
   cd C:\Users\danek\OneDrive\Desktop\NeuroBuff\neurosync\neurosync_player-main
   python chat_response_hook.py
   ```

2. Start the websocket bridge:
   ```bash
   cd C:\Users\danek\OneDrive\Desktop\Mannequin\websocket-bridge
   npm start
   ```

3. Test with a simple Node.js script:
   ```javascript
   const WebSocket = require('ws');
   
   const ws = new WebSocket('ws://localhost:8080');
   
   ws.on('open', async () => {
       // Get auth token
       const authResponse = await fetch('http://localhost:8080/api/auth', { method: 'POST' });
       const { token } = await authResponse.json();
       
       // Authenticate
       ws.send(JSON.stringify({ type: 'auth', token }));
       
       // Wait a bit, then send chat
       setTimeout(() => {
           ws.send(JSON.stringify({
               type: 'chat',
               message: 'Hey there! How are you doing today?'
           }));
       }, 1000);
   });
   
   ws.on('message', (data) => {
       console.log('Received:', JSON.parse(data.toString()));
   });
   ```

## Security Considerations

1. Rate limit chat messages (max 10 per minute per user)
2. Sanitize all user input
3. Implement content filtering for inappropriate messages
4. Monitor ChatGPT API usage and costs
5. Add request logging for debugging

## Error Handling

The system includes comprehensive error handling for:
- Invalid chat messages
- ChatGPT API failures
- Text-to-face hook connection issues
- Rate limiting violations
- Authentication failures