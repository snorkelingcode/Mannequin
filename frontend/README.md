# Mannequin Frontend

A Next.js React application for controlling your 3D Unreal Engine mannequin in real-time through a secure WebSocket bridge.

## Features

🎮 **Real-time Controls**
- Camera positioning and rotation
- Facial expressions and emotions
- Character customization (outfits, hair, skin)
- Body proportions and bone scaling
- Animations and emotes
- Environment/scene selection

🚀 **Ultra-Low Latency Streaming**
- Livepeer integration with WebRTC/HLS
- Sub-3 second latency from Unreal Engine
- Automatic protocol fallback
- Real-time video controls

🔒 **Secure Communication**
- Authenticated WebSocket connection
- Token-based security
- Command validation
- Rate limiting protection

## Quick Start

### 1. Install Dependencies
```bash
cd frontend
npm install
```

### 2. Configure Environment
```bash
cp .env.local.example .env.local
# Edit .env.local with your WebSocket bridge URLs
```

### 3. Start Development Server
```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view the application.

## Project Structure

```
frontend/
├── app/                    # Next.js 14 App Router
│   ├── api/auth/          # Authentication API route
│   ├── globals.css        # Global styles with Tailwind
│   ├── layout.tsx         # Root layout
│   └── page.tsx           # Main page
├── components/            # React components
│   ├── LivepeerPlayer.tsx # Video streaming component
│   └── MannequinControls.tsx # Control interface
├── hooks/                 # Custom React hooks
│   └── useWebSocket.ts    # WebSocket connection hook
└── public/               # Static assets
```

## Environment Variables

### Development
- `NEXT_PUBLIC_WEBSOCKET_URL`: WebSocket bridge URL (client-side)
- `BRIDGE_API_URL`: Bridge API URL for server-side requests

### Production
Update your Vercel environment variables:
- `NEXT_PUBLIC_WEBSOCKET_URL=wss://your-bridge.domain.com`
- `BRIDGE_API_URL=https://your-bridge.domain.com`

## Component Overview

### LivepeerPlayer
- Displays the Unreal Engine stream
- Supports both WebRTC and HLS protocols
- Automatic quality adjustment and error handling
- Real-time status indicators

### MannequinControls
- Comprehensive character customization interface
- Real-time camera controls with smooth updates
- Collapsible sections for organized UI
- Command validation and error handling

### useWebSocket Hook
- Manages WebSocket connection lifecycle
- Handles authentication automatically
- Provides error handling and reconnection
- Rate limiting and security features

## Commands Reference

The app sends structured commands to your Unreal Engine via the WebSocket bridge:

### Camera Controls
- `CAMSTREAM_X_Y_Z_RX_RY_RZ` - Continuous camera positioning
- `CAMSHOT.Default`, `CAMSHOT.Close` - Preset camera shots
- `View.Desktop`, `View.Mobile` - View mode switching

### Character Customization
- `FACE.Happy`, `FACE.Sad` - Facial expressions
- `OF.Kimono`, `OF.SpaceSuit` - Outfit changes
- `HAIR.Red_0.5` - Hair color adjustments
- `SKIN_0.75` - Skin tone modifications

### Animations
- `ANIM.Dance` - Dance animation
- `EMOTE.Wave`, `EMOTE.Bow` - Gesture emotes
- `startspeaking`, `stopspeaking` - Speech animations

### Environment
- `LVL.Medieval`, `LVL.Orbit` - Scene changes
- `PRS.Masc`, `PRS.Fem` - Character presets

## Deployment

### Vercel (Recommended)
1. Connect your GitHub repository to Vercel
2. Set environment variables in Vercel dashboard
3. Deploy automatically on git push

### Manual Deploy
```bash
npm run build
npm start
```

## Development

### Available Scripts
- `npm run dev` - Start development server
- `npm run build` - Build production bundle
- `npm run start` - Start production server
- `npm run lint` - Run ESLint

### Styling
- Tailwind CSS with custom design system
- Dark theme optimized for streaming
- Responsive design for mobile/desktop
- Custom component classes in `globals.css`

## Security

### Client-Side Security
- Environment variable validation
- Input sanitization
- CSP headers via Vercel configuration
- Secure WebSocket connections (WSS in production)

### WebSocket Security
- Automatic token-based authentication
- Command validation before sending
- Connection status monitoring
- Error handling with user feedback

## Troubleshooting

### Common Issues

**WebSocket Connection Failed**
- Check if the bridge server is running
- Verify WebSocket URL in environment variables
- Ensure firewall allows WebSocket connections

**Authentication Failed**
- Bridge server may not be responding
- Check BRIDGE_API_URL configuration
- Verify bridge server has proper CORS settings

**Stream Not Loading**
- Confirm Unreal Engine is running and streaming
- Check Livepeer playback ID configuration
- Try switching between WebRTC and HLS protocols

**Controls Not Working**
- Ensure WebSocket is connected and authenticated
- Check browser console for command errors
- Verify Unreal Engine TCP server is accepting commands

### Browser Support
- Chrome/Chromium 90+ (recommended)
- Firefox 88+
- Safari 14+
- Edge 90+

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT License - see LICENSE file for details