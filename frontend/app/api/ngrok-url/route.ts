import { NextResponse } from 'next/server'

export async function GET() {
  try {
    // This only works when running locally (development)
    // In production, this will fail gracefully
    const response = await fetch('http://localhost:4040/api/tunnels', {
      headers: {
        'Accept': 'application/json',
      },
    })
    
    if (!response.ok) {
      throw new Error(`ngrok API error: ${response.status}`)
    }
    
    const data = await response.json()
    
    // Find the HTTPS tunnel for port 8001
    const httpTunnel = data.tunnels.find((tunnel: any) => 
      tunnel.proto === 'https' && tunnel.config.addr === 'http://localhost:8001'
    )
    
    if (httpTunnel) {
      return NextResponse.json({ 
        url: httpTunnel.public_url,
        status: 'success' 
      })
    } else {
      return NextResponse.json({ 
        error: 'No HTTPS tunnel found for port 8001',
        status: 'not_found' 
      }, { status: 404 })
    }
    
  } catch (error) {
    // This is expected in production when ngrok isn't running locally
    return NextResponse.json({ 
      error: 'ngrok not available',
      status: 'unavailable',
      message: 'This is normal when not streaming locally'
    }, { status: 503 })
  }
}