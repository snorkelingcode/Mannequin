import { NextResponse } from 'next/server'

export async function POST() {
  try {
    const bridgeUrl = process.env.BRIDGE_API_URL || 'http://localhost:3001'
    
    const response = await fetch(`${bridgeUrl}/api/auth`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    })
    
    if (!response.ok) {
      throw new Error(`Bridge API error: ${response.status}`)
    }
    
    const data = await response.json()
    
    return NextResponse.json(data)
  } catch (error) {
    console.error('Auth API error:', error)
    return NextResponse.json(
      { error: 'Failed to get authentication token' },
      { status: 500 }
    )
  }
}