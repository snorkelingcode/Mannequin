"""
Automatically update .env.local with current ngrok HTTP tunnel URL
"""
import requests
import json
import os
import time

def get_ngrok_http_url():
    """Get the current ngrok HTTP tunnel URL"""
    try:
        # ngrok exposes its API on localhost:4040
        response = requests.get('http://localhost:4040/api/tunnels', timeout=10)
        tunnels = response.json()['tunnels']
        
        # Find the HTTP tunnel
        for tunnel in tunnels:
            if tunnel['proto'] == 'https' and tunnel['config']['addr'] == 'http://localhost:8001':
                return tunnel['public_url']
        
        print("❌ No HTTP tunnel found for port 8001")
        return None
        
    except Exception as e:
        print(f"❌ Error getting ngrok URL: {e}")
        return None

def update_env_file(ngrok_url):
    """Update .env.local with the new ngrok URL"""
    try:
        env_file = 'frontend/.env.local'
        
        # Read current file
        with open(env_file, 'r') as f:
            lines = f.readlines()
        
        # Update the line with NEXT_PUBLIC_TEXT_TO_FACE_URL
        updated = False
        for i, line in enumerate(lines):
            if line.startswith('NEXT_PUBLIC_TEXT_TO_FACE_URL='):
                lines[i] = f'NEXT_PUBLIC_TEXT_TO_FACE_URL={ngrok_url}/chat_response\n'
                updated = True
                break
        
        # If line doesn't exist, add it
        if not updated:
            lines.append(f'NEXT_PUBLIC_TEXT_TO_FACE_URL={ngrok_url}/chat_response\n')
        
        # Write updated file
        with open(env_file, 'w') as f:
            f.writelines(lines)
        
        print(f"✅ Updated {env_file} with: {ngrok_url}/chat_response")
        return True
        
    except Exception as e:
        print(f"❌ Error updating .env.local: {e}")
        return False

def main():
    print("🔍 Waiting for ngrok to start...")
    
    # Wait up to 30 seconds for ngrok to be ready
    for attempt in range(30):
        ngrok_url = get_ngrok_http_url()
        if ngrok_url:
            print(f"🔒 Found ngrok URL: {ngrok_url}")
            if update_env_file(ngrok_url):
                print("✅ Environment file updated successfully!")
                print("🔄 You can now restart the frontend to use the new URL")
                return True
            break
        
        print(f"⏳ Waiting for ngrok... (attempt {attempt + 1}/30)")
        time.sleep(1)
    
    print("❌ Failed to get ngrok URL after 30 seconds")
    print("💡 Make sure ngrok is running and the HTTP tunnel is active")
    return False

if __name__ == "__main__":
    main()
    input("Press Enter to close...")