const WebSocket = require('ws');
const net = require('net');
const crypto = require('crypto');
const rateLimit = require('express-rate-limit');
const express = require('express');
const cors = require('cors');
const OpenAI = require('openai');
const axios = require('axios');
require('dotenv').config();

// Initialize OpenAI
const openai = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY
});

const EGIRL_PERSONA = process.env.EGIRL_PERSONA_PROMPT || "You are a playful, flirty Twitch e-girl personality. Respond with enthusiasm, use cute expressions, and be engaging. Keep responses under 100 words.";

// Security configuration
const CONFIG = {
    WEBSOCKET_PORT: process.env.PORT || process.env.WEBSOCKET_PORT || 8080,
    TCP_HOST: process.env.TCP_HOST || '127.0.0.1',
    TCP_PORT: process.env.TCP_PORT || 7777,
    ALLOWED_ORIGINS: (process.env.ALLOWED_ORIGINS || 'https://mannequin.vercel.app,http://localhost:3000').split(','),
    SECRET_KEY: process.env.SECRET_KEY || crypto.randomBytes(32).toString('hex'),
    MAX_CONNECTIONS: parseInt(process.env.MAX_CONNECTIONS) || 10,
    RATE_LIMIT_WINDOW: 15 * 60 * 1000, // 15 minutes
    RATE_LIMIT_MAX: 1000, // Max requests per window
};

// Chat processing functions
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

// Validate commands against known patterns
const VALID_COMMAND_PATTERNS = [
    /^CAMSTREAM_[-\d.]+_[-\d.]+_[-\d.]+_[-\d.]+_[-\d.]+_[-\d.]+$/,
    /^CAM\.(X|Y|Z|RX|RY|RZ)_[-\d.]+$/,
    /^AGENT\.(X|Y|Z|RX|RY|RZ)_[-\d.]+$/,
    /^CAMSHOT\.(Default|ExtremeClose|Close|HighAngle|LowAngle|Medium|MobileMedium|WideShot|MobileWideShot)$/,
    /^View\.(Desktop|Mobile)$/,
    /^NEW\.Character$/,
    /^NAME_\w+$/,
    /^BTN\.Save$/,
    /^LOAD_\w+$/,
    /^DELETE_\w+$/,
    /^PRS\.(Masc|Masc1|Fem|Fem1)$/,
    /^OF\.(Default|MaidDress|PopStar|Kimono|BlackDress|SpaceSuit|ANIME)$/,
    /^HS\.(Default|Buzz|Crop)$/,
    /^SKIN.[0-9.]+$/,
    /^SKC.[0-9.]+$/,  // Alternative skin command from hooks.txt
    /^BONE\.(Head|Chest|Hand|Abdomen|Arm|Leg|Feet)_[0-9.]+$/,
    /^BN(H|C|HD|A|AR|L|F).[0-9.]+$/,  // Alternative bone commands from hooks.txt
    /^HAIR\.(Red|Green|Blue).[0-9.]+$/,
    /^HC(R|G|B).[0-9.]+$/,  // Hair color RGB components from hooks.txt
    /^EYE\.(Color|Saturation).[0-9.]+$/,
    /^E(C|S).[0-9.]+$/,  // Alternative eye commands from hooks.txt
    /^FACE\.(Default|Happy|Sad|Surprised|Fearful|Focused|Disgusted|Childish|Tired|Annoyed|Confused|Curious|Embarrassed|Angry|Bored|Relaxed|Suspicious|Proud|Pained|Nervous|Love)$/,
    /^ANIM\.(Dance|Mannequin)$/,
    /^(startspeaking|stopspeaking)$/,
    /^EMOTE\.\w+$/,
    /^LVL\.(Home|Lofi|DJ|Medieval|Orbit|Split|Split3|Split4|Classroom)$/,
    /^QUIT\.$/,
    /^MORPH\.\w+.[-\d.]+$/,
    // Comprehensive morph target patterns from hooks.txt
    /^MT(HT|HS|HB|HBW).[-\d.]+$/,  // Head morph targets
    /^MT(NFT|NF|NS|NBH|NBL|ND).[-\d.]+$/,  // Neck morph targets  
    /^MT(EW|EP|EL|ERS).[-\d.]+$/,  // Ear morph targets
    /^MT(FHC|FHCR|FHS|T).[-\d.]+$/,  // Forehead/Temple morph targets
    /^MT(EBH|EBW|EBA).[-\d.]+$/,  // Eyebrow morph targets
    /^MT(EC|EYW|EB|EYH).[-\d.]+$/,  // Eye morph targets
    /^MT(NB|NL|NW|N|S|NCR).[-\d.]+$/,  // Nose morph targets
    /^MT(CB|CT|CD).[-\d.]+$/,  // Cheek morph targets
    /^MT(LO|LW|LOV|LCV|LD|LU).[-\d.]+$/,  // Lips morph targets
    /^M(CL|TCW|TJL|TJH|TH).[-\d.]+$/,  // Chin/Jaw morph targets
    /^MTCP.[-\d.]+$/  // Chin point morph target
];

function isValidCommand(command) {
    return VALID_COMMAND_PATTERNS.some(pattern => pattern.test(command));
}

// Connection tracking
const activeConnections = new Map();
let connectionCount = 0;

// Create Express app for health checks
const app = express();

// Trust proxy for Railway deployment
app.set('trust proxy', true);

app.use(cors({
    origin: CONFIG.ALLOWED_ORIGINS,
    credentials: true
}));

// Rate limiting
const limiter = rateLimit({
    windowMs: CONFIG.RATE_LIMIT_WINDOW,
    max: CONFIG.RATE_LIMIT_MAX,
    message: 'Too many requests from this IP',
    standardHeaders: true,
    legacyHeaders: false,
    trustProxy: true, // Explicitly enable trust proxy for Railway
});

app.use('/api', limiter);

// Health check endpoint
app.get('/health', (req, res) => {
    res.json({
        status: 'healthy',
        connections: connectionCount,
        timestamp: new Date().toISOString()
    });
});

// Generate secure token endpoint (for development - in production this should be authenticated)
app.post('/api/auth', (req, res) => {
    const token = generateSecureToken();
    res.json({ token, expiresIn: '1h' });
});

function generateSecureToken() {
    const payload = {
        timestamp: Date.now(),
        nonce: crypto.randomBytes(16).toString('hex')
    };
    
    const hmac = crypto.createHmac('sha256', CONFIG.SECRET_KEY);
    hmac.update(JSON.stringify(payload));
    const signature = hmac.digest('hex');
    
    return Buffer.from(JSON.stringify({...payload, signature})).toString('base64');
}

function verifyToken(token) {
    try {
        const decoded = JSON.parse(Buffer.from(token, 'base64').toString());
        const { timestamp, nonce, signature } = decoded;
        
        // Check if token is expired (1 hour)
        if (Date.now() - timestamp > 3600000) {
            return false;
        }
        
        // Verify signature
        const payload = { timestamp, nonce };
        const hmac = crypto.createHmac('sha256', CONFIG.SECRET_KEY);
        hmac.update(JSON.stringify(payload));
        const expectedSignature = hmac.digest('hex');
        
        return signature === expectedSignature;
    } catch (error) {
        console.error('Token verification failed:', error.message);
        return false;
    }
}

// TCP connection function
async function sendToUnrealEngine(command) {
    return new Promise((resolve, reject) => {
        const client = new net.Socket();
        const timeout = setTimeout(() => {
            client.destroy();
            reject(new Error('TCP connection timeout'));
        }, 5000);
        
        client.connect(CONFIG.TCP_PORT, CONFIG.TCP_HOST, () => {
            clearTimeout(timeout);
            client.write(command);
            client.end();
            resolve();
        });
        
        client.on('error', (error) => {
            clearTimeout(timeout);
            reject(error);
        });
        
        client.on('close', () => {
            clearTimeout(timeout);
            resolve();
        });
    });
}

// Start HTTP server first
const httpServer = app.listen(CONFIG.WEBSOCKET_PORT, '0.0.0.0', () => {
    console.log(`HTTP server running on port ${CONFIG.WEBSOCKET_PORT}`);
});

// WebSocket server runs on top of HTTP server
const wss = new WebSocket.Server({
    server: httpServer,  // Use the existing HTTP server
    verifyClient: (info) => {
        // Check origin
        const origin = info.origin;
        if (!CONFIG.ALLOWED_ORIGINS.includes(origin)) {
            console.log(`Rejected connection from unauthorized origin: ${origin}`);
            return false;
        }
        
        // Check connection limit
        if (connectionCount >= CONFIG.MAX_CONNECTIONS) {
            console.log('Rejected connection: Maximum connections reached');
            return false;
        }
        
        return true;
    }
});

wss.on('connection', (ws, req) => {
    const clientId = crypto.randomBytes(16).toString('hex');
    const clientIP = req.socket.remoteAddress;
    
    console.log(`New WebSocket connection: ${clientId} from ${clientIP}`);
    
    // Connection tracking
    connectionCount++;
    activeConnections.set(clientId, {
        ws,
        ip: clientIP,
        connected: Date.now(),
        authenticated: false,
        lastActivity: Date.now()
    });
    
    // Rate limiting per connection
    const connectionRateLimit = {
        requests: 0,
        window: Date.now()
    };
    
    ws.on('message', async (message) => {
        try {
            // Update last activity
            const connection = activeConnections.get(clientId);
            if (connection) {
                connection.lastActivity = Date.now();
            }
            
            // Rate limiting check
            const now = Date.now();
            if (now - connectionRateLimit.window > 60000) { // Reset every minute
                connectionRateLimit.requests = 0;
                connectionRateLimit.window = now;
            }
            
            connectionRateLimit.requests++;
            if (connectionRateLimit.requests > 100) { // Max 100 requests per minute per connection
                ws.send(JSON.stringify({
                    type: 'error',
                    message: 'Rate limit exceeded'
                }));
                return;
            }
            
            const data = JSON.parse(message.toString());
            
            // Handle authentication
            if (data.type === 'auth') {
                if (verifyToken(data.token)) {
                    if (connection) {
                        connection.authenticated = true;
                    }
                    ws.send(JSON.stringify({
                        type: 'auth_success',
                        message: 'Authentication successful'
                    }));
                    console.log(`Client ${clientId} authenticated successfully`);
                } else {
                    ws.send(JSON.stringify({
                        type: 'auth_failed',
                        message: 'Invalid or expired token'
                    }));
                    console.log(`Client ${clientId} authentication failed`);
                }
                return;
            }
            
            // Handle chat messages  
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
                return;
            }

            // Check if authenticated for command messages
            if (data.type === 'command') {
                if (!connection || !connection.authenticated) {
                    ws.send(JSON.stringify({
                        type: 'error',
                        message: 'Authentication required'
                    }));
                    return;
                }
                
                // Validate command
                if (!data.command || typeof data.command !== 'string') {
                    ws.send(JSON.stringify({
                        type: 'error',
                        message: 'Invalid command format'
                    }));
                    return;
                }
                
                // Sanitize and validate command
                const command = data.command.trim();
                if (!isValidCommand(command)) {
                    ws.send(JSON.stringify({
                        type: 'error',
                        message: 'Invalid command pattern'
                    }));
                    console.log(`Invalid command rejected from ${clientId}: ${command}`);
                    return;
                }
                
                // Send to Unreal Engine
                try {
                    await sendToUnrealEngine(command);
                    ws.send(JSON.stringify({
                        type: 'success',
                        message: 'Command sent successfully',
                        command: command
                    }));
                    console.log(`Command sent from ${clientId}: ${command}`);
                } catch (error) {
                    ws.send(JSON.stringify({
                        type: 'error',
                        message: 'Failed to send command to Unreal Engine',
                        details: error.message
                    }));
                    console.error(`Failed to send command from ${clientId}:`, error.message);
                }
            }
            
        } catch (error) {
            console.error(`Error handling message from ${clientId}:`, error.message);
            ws.send(JSON.stringify({
                type: 'error',
                message: 'Invalid message format'
            }));
        }
    });
    
    ws.on('close', () => {
        console.log(`WebSocket connection closed: ${clientId}`);
        activeConnections.delete(clientId);
        connectionCount--;
    });
    
    ws.on('error', (error) => {
        console.error(`WebSocket error for ${clientId}:`, error.message);
        activeConnections.delete(clientId);
        connectionCount--;
    });
    
    // Send welcome message
    ws.send(JSON.stringify({
        type: 'welcome',
        message: 'Connected to Mannequin WebSocket Bridge',
        clientId: clientId
    }));
});

// Cleanup inactive connections
setInterval(() => {
    const now = Date.now();
    const timeout = 300000; // 5 minutes
    
    for (const [clientId, connection] of activeConnections) {
        if (now - connection.lastActivity > timeout) {
            console.log(`Closing inactive connection: ${clientId}`);
            connection.ws.terminate();
            activeConnections.delete(clientId);
            connectionCount--;
        }
    }
}, 60000); // Check every minute

// HTTP server already started above with WebSocket server

console.log(`🚀 Secure WebSocket Bridge Server Started`);
console.log(`WebSocket Server: ws://localhost:${CONFIG.WEBSOCKET_PORT}`);
console.log(`HTTP Server: http://localhost:${CONFIG.WEBSOCKET_PORT}`);
console.log(`Target TCP: ${CONFIG.TCP_HOST}:${CONFIG.TCP_PORT}`);
console.log(`Allowed Origins: ${CONFIG.ALLOWED_ORIGINS.join(', ')}`);
console.log(`Max Connections: ${CONFIG.MAX_CONNECTIONS}`);

// Graceful shutdown
process.on('SIGINT', () => {
    console.log('Shutting down servers...');
    wss.close();
    httpServer.close();
    process.exit(0);
});