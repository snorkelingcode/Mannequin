/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    domains: ['livepeercdn.studio'],
  },
  env: {
    WEBSOCKET_URL: process.env.WEBSOCKET_URL || 'ws://localhost:8080',
    BRIDGE_API_URL: process.env.BRIDGE_API_URL || 'http://localhost:3001',
  },
  // Strip console logs in production
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production' ? {
      exclude: ['error', 'warn'],
    } : false,
  },
}

module.exports = nextConfig