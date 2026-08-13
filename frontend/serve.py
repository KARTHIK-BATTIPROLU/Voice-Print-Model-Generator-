"""Simple HTTP server to serve the frontend"""
import http.server
import socketserver
import os

PORT = 5173
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

if __name__ == '__main__':
    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        print("=" * 80)
        print(f"🌐 Frontend Server Starting...")
        print("=" * 80)
        print(f"\n✅ Server running at: http://localhost:{PORT}")
        print(f"✅ Open this URL in your browser: http://localhost:{PORT}/index.html")
        print(f"\n📁 Serving files from: {DIRECTORY}")
        print(f"\n⚠️  Make sure backend is running on: http://localhost:8000")
        print(f"\nPress Ctrl+C to stop the server")
        print("=" * 80)
        print()
        httpd.serve_forever()
