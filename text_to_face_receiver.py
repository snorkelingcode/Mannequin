"""
Text-to-Face Receiver with CORS support for production
Receives chat responses and triggers facial animations
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import socket
import threading
import time

app = Flask(__name__)

# Enable CORS for all origins (you can restrict this to specific domains)
CORS(app, origins=["https://www.mannequin.live", "https://mannequin.live", "http://localhost:3000", "http://localhost:3001"])

# Configuration
UNREAL_HOST = '127.0.0.1'  # Unreal Engine host
UNREAL_PORT = 7777         # Unreal Engine TCP port

def send_to_unreal(text):
    """Send text to Unreal Engine for facial animation"""
    try:
        # Connect to Unreal Engine
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        sock.connect((UNREAL_HOST, UNREAL_PORT))
        
        # Send the text (you might need to format this according to your Unreal setup)
        # Example: sending as a speaking command
        command = f"startspeaking"
        sock.send(command.encode('utf-8'))
        time.sleep(0.1)
        
        # Send the actual text (adjust format as needed for your system)
        sock.send(text.encode('utf-8'))
        
        sock.close()
        return True
    except Exception as e:
        print(f"Error sending to Unreal: {e}")
        return False

@app.route('/chat_response', methods=['POST', 'OPTIONS'])
def receive_chat():
    # Handle preflight OPTIONS request for CORS
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', request.headers.get('Origin', '*'))
        response.headers.add('Access-Control-Allow-Methods', 'POST, OPTIONS')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        return response
    
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        print(f"\n🎭 Received AI response: {text}")
        
        # Send to Unreal Engine in a separate thread to avoid blocking
        thread = threading.Thread(target=send_to_unreal, args=(text,))
        thread.start()
        
        # Log for debugging
        print(f"✅ Processing text for facial animation")
        print(f"   Length: {len(text)} characters")
        
        response = jsonify({
            'status': 'success',
            'message': 'Text received and processing',
            'text_length': len(text)
        })
        
        # Add CORS headers to response
        response.headers.add('Access-Control-Allow-Origin', request.headers.get('Origin', '*'))
        
        return response
        
    except Exception as e:
        print(f"❌ Error processing request: {e}")
        error_response = jsonify({'error': str(e)})
        error_response.headers.add('Access-Control-Allow-Origin', request.headers.get('Origin', '*'))
        return error_response, 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'text-to-face-receiver',
        'unreal_target': f"{UNREAL_HOST}:{UNREAL_PORT}"
    })

if __name__ == '__main__':
    print("🎭 Text-to-Face Receiver Starting...")
    print(f"📡 Will forward to Unreal at {UNREAL_HOST}:{UNREAL_PORT}")
    print(f"🌐 Listening on http://localhost:8001")
    print(f"🔒 CORS enabled for production domains")
    print("\n✅ Ready to receive AI responses!\n")
    
    # Run the Flask app
    app.run(host='0.0.0.0', port=8001, debug=True)