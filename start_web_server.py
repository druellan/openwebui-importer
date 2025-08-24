#!/usr/bin/env python3
"""Startup script for the ChatGPT to Open-WebUI converter web server."""

import os
import sys
import subprocess
import webbrowser
import time
from threading import Timer

def check_dependencies():
    """Check if required files and dependencies exist."""
    required_files = ['webserver/index.html', 'convert_chatgpt.py', 'webserver/server.py']
    missing_files = []
    
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"Error: Missing required files: {', '.join(missing_files)}")
        return False
    
    # Check if uv is available
    try:
        subprocess.run(['uv', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Warning: 'uv' command not found. Make sure uv is installed and in your PATH.")
        print("You can install it with: pip install uv")
        return False
    
    return True

def open_browser(url, delay=2):
    """Open the browser after a delay."""
    time.sleep(delay)
    try:
        webbrowser.open(url)
        print(f"Opened browser at {url}")
    except Exception as e:
        print(f"Could not open browser automatically: {e}")
        print(f"Please manually open {url} in your browser.")

def main():
    """Main function to start the web server."""
    print("ChatGPT to Open-WebUI Converter Web Server")
    print("=" * 45)
    
    # Check dependencies
    if not check_dependencies():
        print("\nPlease fix the above issues and try again.")
        return 1
    
    # Get port from command line or use default
    port = 3010
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Invalid port number: {sys.argv[1]}")
            return 1

    # Start browser opener in background
    url = f"http://localhost:{port}"
    Timer(2, open_browser, args=(url,)).start()

    print(f"\nStarting web server on port {port}...")
    print(f"Access the converter at: {url}")
    print("Press Ctrl+C to stop the server\n")

    # Start the web server
    try:
        subprocess.run([sys.executable, 'webserver/server.py', '--port', str(port)])
    except KeyboardInterrupt:
        print("\nServer stopped by user.")
    except Exception as e:
        print(f"Error starting server: {e}")
        return 1

    return 0

if __name__ == '__main__':
    sys.exit(main())