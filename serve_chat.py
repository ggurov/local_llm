#!/usr/bin/env python3
"""
Simple HTTP server to serve the chat interface HTML file
"""

import http.server
import socketserver
import os
import sys
from pathlib import Path

# Configuration
HOST = "192.168.1.30"
PORT = 9090  # Different port to avoid conflicts
CHAT_FILE = "chat_interface.html"

class ChatHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom handler to serve the chat interface."""
    
    def do_GET(self):
        """Handle GET requests."""
        if self.path == "/" or self.path == "/chat":
            # Serve the chat interface
            self.path = f"/{CHAT_FILE}"
        elif self.path == f"/{CHAT_FILE}":
            # Serve the chat interface file
            pass
        else:
            # For any other path, serve the chat interface
            self.path = f"/{CHAT_FILE}"
        
        return super().do_GET()
    
    def end_headers(self):
        """Add CORS headers to allow cross-origin requests."""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def main():
    """Start the HTTP server."""
    # Change to the directory containing the chat interface
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Check if chat interface file exists
    if not os.path.exists(CHAT_FILE):
        print(f"❌ Error: {CHAT_FILE} not found in {script_dir}")
        print("Please make sure the chat interface file exists.")
        sys.exit(1)
    
    # Create the server
    with socketserver.TCPServer((HOST, PORT), ChatHTTPRequestHandler) as httpd:
        print(f"🌐 Chat Interface Server")
        print(f"======================================")
        print(f"📍 Host: {HOST}")
        print(f"🔌 Port: {PORT}")
        print(f"📄 Serving: {CHAT_FILE}")
        print(f"🌍 Access URL: http://{HOST}:{PORT}")
        print(f"")
        print(f"✅ Server is running...")
        print(f"Press Ctrl+C to stop")
        print(f"")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print(f"\n🛑 Server stopped by user")
            httpd.shutdown()

if __name__ == "__main__":
    main()
