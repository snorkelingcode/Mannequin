# 🎭 Mannequin - Interactive 3D Character Platform

A complete pipeline for real-time 3D character customization and streaming, built with Unreal Engine 5.5, secure WebSocket bridge, and modern web technologies.

## 🌟 Overview

Mannequin enables users to customize 3D characters in real-time through a web interface, with ultra-low latency streaming powered by Livepeer. The system features comprehensive character controls including facial expressions, outfits, body proportions, camera positioning, and environmental settings.

### 📊 Architecture

```
End User → Vercel Web App → WebSocket Bridge → Unreal Engine TCP → WebRTC/UDP → Livepeer → Stream
```

## 🚀 Features

### 🎮 Character Customization
- **Facial Expressions**: 20+ emotions (Happy, Sad, Angry, Surprised, etc.)
- **Outfits**: Multiple clothing options (Kimono, Space Suit, Anime Armor, etc.)
- **Physical Attributes**: Skin tone, hair color (RGB), eye customization
- **Body Proportions**: Adjustable bone scaling for head, chest, arms, legs, etc.
- **Hair Styles**: Various hair cuts and styles

### 📹 Camera System
- **Real-time Controls**: Smooth XYZ positioning and rotation
- **Preset Shots**: Default, Close-up, Wide, High/Low angle views
- **View Modes**: Desktop and mobile optimized layouts
- **Continuous Updates**: Real-time camera streaming with configurable rates

### 🎭 Animations & Emotes
- **Basic Animations**: Dance, speaking states
- **Gesture Emotes**: Wave, bow, salute, thumbs up
- **Expression Emotes**: Plotting, nervous, confident, etc.

### 🏞️ Environments
- **Scene Levels**: Home, Lofi room, DJ booth, Medieval castle, Space orbit
- **Split Screen**: Multi-camera views (2, 3, or 4 way splits)
- **Classroom**: Educational environment setup

### 🔒 Security Features
- **Authentication**: HMAC-SHA256 token-based security
- **Origin Validation**: Configurable allowed domains
- **Rate Limiting**: Per-connection and global request limits
- **Command Validation**: Whitelist of safe command patterns
- **Connection Management**: Automatic cleanup and monitoring

### 📺 Streaming
- **Ultra-Low Latency**: Sub-3 second end-to-end latency
- **Dual Protocol**: WebRTC (0.5-3s) and HLS (~10s) support
- **Automatic Fallback**: Seamless protocol switching
- **Quality Control**: Adaptive bitrate and resolution

## 🏗️ Project Structure

```
Mannequin/
├── websocket-bridge/          # Secure WebSocket to TCP bridge
│   ├── server.js             # Main bridge server
│   ├── package.json          # Dependencies
│   ├── .env.example          # Configuration template
│   └── README.md             # Bridge documentation
├── frontend/                 # Next.js React application
│   ├── app/                  # Next.js 14 App Router
│   ├── components/           # React components
│   ├── hooks/                # Custom hooks
│   ├── package.json          # Frontend dependencies
│   └── README.md             # Frontend documentation
├── WebRTCBridge/            # Existing streaming infrastructure
│   └── livepeer_player.html  # Reference Livepeer player
├── Controller/              # Reference controller interface
│   └── tcp_controller2.html  # Original HTML controller
└── README.md                # This file
```

## 🚀 Quick Start

### Prerequisites
- Node.js 16+
- Unreal Engine 5.5 project with TCP/WebRTC components
- npm or yarn

### 1. WebSocket Bridge Setup
```bash
cd websocket-bridge
npm install
cp .env.example .env
# Configure your .env file
npm start
```

### 2. Frontend Setup
```bash
cd frontend
npm install
cp .env.local.example .env.local
# Configure your environment variables
npm run dev
```

### 3. Unreal Engine Setup
1. Load your Unreal Engine project with the provided TCP/WebRTC components
2. Ensure TCP server is listening on port 7777
3. Configure WebRTC bridge for video streaming
4. Start the game/editor

### 4. Access the Application
- Frontend: http://localhost:3000
- Bridge API: http://localhost:3001
- WebSocket: ws://localhost:8080

## 🔧 Configuration

### WebSocket Bridge (.env)
```env
WEBSOCKET_PORT=8080
TCP_HOST=127.0.0.1
TCP_PORT=7777
SECRET_KEY=your-secret-key
ALLOWED_ORIGINS=https://mannequin.vercel.app,http://localhost:3000
MAX_CONNECTIONS=10
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_WEBSOCKET_URL=ws://localhost:8080
BRIDGE_API_URL=http://localhost:3001
```

## 🚀 Production Deployment

### Vercel (Frontend)
1. Connect GitHub repository to Vercel
2. Configure environment variables:
   - `NEXT_PUBLIC_WEBSOCKET_URL=wss://your-bridge-domain.com`
   - `BRIDGE_API_URL=https://your-bridge-domain.com`
3. Deploy automatically on push

### Bridge Server (VPS/Cloud)
1. Deploy to cloud provider (AWS, Google Cloud, DigitalOcean)
2. Configure SSL/TLS certificates
3. Set up reverse proxy (nginx)
4. Configure firewall rules
5. Use process manager (PM2)

```bash
# PM2 deployment example
pm2 start server.js --name mannequin-bridge
pm2 startup
pm2 save
```

## 🔒 Security Considerations

### Production Security Checklist
- [ ] Use strong SECRET_KEY
- [ ] Configure proper ALLOWED_ORIGINS
- [ ] Enable HTTPS/WSS in production
- [ ] Set up firewall rules
- [ ] Configure rate limiting
- [ ] Monitor connection logs
- [ ] Regular security updates
- [ ] Use reverse proxy with security headers

### Network Security
- WebSocket bridge acts as security barrier
- No direct access to local TCP ports
- Command validation prevents injection
- Rate limiting prevents abuse
- Authentication required for all commands

## 📝 Command Reference

### Camera Commands
```javascript
// Continuous camera positioning
"CAMSTREAM_X_Y_Z_RX_RY_RZ"

// Preset shots
"CAMSHOT.Default"
"CAMSHOT.Close"
"CAMSHOT.WideShot"

// View modes
"View.Desktop"
"View.Mobile"
```

### Character Commands
```javascript
// Facial expressions
"FACE.Happy"
"FACE.Sad"
"FACE.Surprised"

// Outfits
"OF.Kimono"
"OF.SpaceSuit"
"OF.ANIME"

// Physical attributes
"SKIN_0.75"
"HAIR.Red_0.5"
"BONE.Head_1.2"
```

### Animation Commands
```javascript
// Basic animations
"ANIM.Dance"
"startspeaking"
"stopspeaking"

// Emotes
"EMOTE.Wave"
"EMOTE.Bow"
"EMOTE.Salute"
```

### Environment Commands
```javascript
// Scene levels
"LVL.Medieval"
"LVL.Orbit"
"LVL.Classroom"

// Character presets
"PRS.Masc"
"PRS.Fem"
```

## 🛠️ Development

### Adding New Commands
1. Update `VALID_COMMAND_PATTERNS` in bridge server
2. Add UI controls in `MannequinControls.tsx`
3. Implement corresponding logic in Unreal Engine
4. Test end-to-end functionality

### Custom Integrations
- WebSocket bridge supports custom command patterns
- Frontend components are modular and extensible
- Unreal Engine TCP handler can be extended
- Livepeer streaming supports custom configurations

## 🐛 Troubleshooting

### Common Issues

**Bridge Connection Failed**
- Verify bridge server is running
- Check firewall settings
- Confirm TCP server in Unreal Engine is active

**Authentication Errors**
- Check SECRET_KEY configuration
- Verify ALLOWED_ORIGINS includes your domain
- Ensure system time is synchronized

**Streaming Issues**
- Confirm Livepeer playbook ID is correct
- Check WebRTC bridge in Unreal Engine
- Try switching between WebRTC/HLS protocols

**Commands Not Working**
- Verify WebSocket connection is authenticated
- Check command format against patterns
- Monitor bridge server logs for errors

### Debug Mode
Enable debug logging in bridge server:
```javascript
// In server.js, add:
const DEBUG = process.env.DEBUG === 'true'
if (DEBUG) console.log('Debug info:', data)
```

## 📊 Performance Optimization

### Frontend
- Debounce slider updates for smooth performance
- Use React.memo for expensive components
- Implement virtual scrolling for large lists
- Optimize bundle size with code splitting

### Bridge Server
- Connection pooling for TCP connections
- Memory monitoring and cleanup
- Request queuing for high traffic
- Load balancing for multiple instances

### Streaming
- Adjust video quality based on connection
- Implement adaptive bitrate streaming
- Use CDN for global distribution
- Monitor latency and adjust protocols

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

### Development Guidelines
- Follow TypeScript best practices
- Add proper error handling
- Write tests for new features
- Update documentation
- Maintain backward compatibility

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Unreal Engine 5.5** - 3D rendering and character system
- **Livepeer** - Ultra-low latency streaming infrastructure
- **Next.js** - React framework for production
- **WebSocket** - Real-time communication protocol
- **Tailwind CSS** - Utility-first CSS framework

## 📞 Support

- 📧 Email: support@mannequin.app
- 💬 Discord: [Mannequin Community](#)
- 📖 Documentation: [docs.mannequin.app](#)
- 🐛 Issues: [GitHub Issues](https://github.com/mannequin/issues)

---

Built with ❤️ for interactive 3D experiences