# Mannequin WebSocket Bridge

A secure WebSocket to TCP bridge that allows the Mannequin web application to safely communicate with your local Unreal Engine TCP server.

## Security Features

- **Authentication**: Secure token-based authentication using HMAC-SHA256
- **Origin Validation**: Only allows connections from authorized domains
- **Rate Limiting**: Prevents abuse with configurable request limits
- **Command Validation**: Only allows predefined, safe command patterns
- **Connection Limits**: Configurable maximum concurrent connections
- **Automatic Cleanup**: Removes inactive connections

## Setup

1. **Install Dependencies**
   ```bash
   cd websocket-bridge
   npm install
   ```

2. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Start the Bridge**
   ```bash
   npm start
   ```

## Configuration

### Environment Variables

- `WEBSOCKET_PORT`: WebSocket server port (default: 8080)
- `TCP_HOST`: Unreal Engine TCP host (default: 127.0.0.1)
- `TCP_PORT`: Unreal Engine TCP port (default: 7777)
- `SECRET_KEY`: Secret key for token generation
- `ALLOWED_ORIGINS`: Comma-separated list of allowed origins
- `MAX_CONNECTIONS`: Maximum concurrent connections (default: 10)

## API Endpoints

### WebSocket Connection

Connect to `ws://localhost:8080`

#### Message Types

1. **Authentication**
   ```json
   {
     "type": "auth",
     "token": "base64-encoded-token"
   }
   ```

2. **Send Command**
   ```json
   {
     "type": "command",
     "command": "FACE.Happy"
   }
   ```

### HTTP Endpoints

- `GET /health` - Health check
- `POST /api/auth` - Generate authentication token (dev only)

## Supported Commands

The bridge validates all commands against predefined patterns:

- **Camera Controls**: `CAMSTREAM_X_Y_Z_RX_RY_RZ`, `CAMSHOT.Default`
- **Character Customization**: `FACE.Happy`, `OF.Kimono`, `HAIR.Red_0.5`
- **Animations**: `ANIM.Dance`, `EMOTE.Wave`
- **Environment**: `LVL.Medieval`, `View.Desktop`
- **System**: `NEW.Character`, `BTN.Save`, `LOAD_CharacterName`

## Security Best Practices

1. **Always use HTTPS in production**
2. **Set a strong SECRET_KEY**
3. **Limit ALLOWED_ORIGINS to your domains only**
4. **Run behind a reverse proxy with additional security headers**
5. **Monitor connection logs for suspicious activity**

## Development

```bash
npm run dev  # Start with nodemon for auto-restart
```

## Production Deployment

1. Set production environment variables
2. Use a process manager like PM2
3. Configure reverse proxy (nginx/apache)
4. Set up SSL/TLS termination
5. Configure firewall rules

```bash
pm2 start server.js --name mannequin-bridge
```