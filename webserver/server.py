#!/usr/bin/env python3
"""Simple web server for ChatGPT to Open-WebUI converter."""

import os
import tempfile
import zipfile
import subprocess
import shutil
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import cgi
import json
import traceback

class ConvertHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Serve the HTML form."""
        if self.path == '/' or self.path == '/webserver/index.html' or self.path == '/':
            try:
                with open('webserver/index.html', 'r', encoding='utf-8') as f:
                    content = f.read()
                self.send_response(200)
                self.send_header('Content-type', 'text/html; charset=utf-8')
                self.end_headers()
                self.wfile.write(content.encode('utf-8'))
            except FileNotFoundError:
                self.send_error(404, "index.html not found")
        else:
            self.send_error(404, "File not found")

    def do_POST(self):
        """Handle form submission and conversion."""
        if self.path == '/convert':
            try:
                # Parse multipart form data
                content_type = self.headers['content-type']
                if not content_type.startswith('multipart/form-data'):
                    self.send_error(400, "Expected multipart/form-data")
                    return

                # Parse the form data
                form = cgi.FieldStorage(
                    fp=self.rfile,
                    headers=self.headers,
                    environ={'REQUEST_METHOD': 'POST'}
                )

                # Get user ID
                if 'userId' not in form:
                    self.send_error(400, "Missing userId field")
                    return
                user_id = form['userId'].value

                # Get uploaded file
                if 'chatFile' not in form:
                    self.send_error(400, "Missing chatFile field")
                    return
                
                file_item = form['chatFile']
                if not file_item.filename:
                    self.send_error(400, "No file selected")
                    return

                # Create temporary directory for processing
                with tempfile.TemporaryDirectory() as temp_dir:
                    # Save uploaded file
                    input_file = os.path.join(temp_dir, 'conversations.json')
                    with open(input_file, 'wb') as f:
                        f.write(file_item.file.read())

                    # Validate JSON file
                    try:
                        with open(input_file, 'r', encoding='utf-8') as f:
                            json.load(f)
                    except json.JSONDecodeError as e:
                        self.send_error(400, f"Invalid JSON file: {e}")
                        return

                    # Create output directory
                    output_dir = os.path.join(temp_dir, 'output')
                    os.makedirs(output_dir, exist_ok=True)

                    # Run the conversion script
                    try:
                        cmd = [
                            'uv', 'run', 'convert_chatgpt.py',
                            '--userid', user_id,
                            '--output-dir', output_dir,
                            input_file
                        ]
                        
                        result = subprocess.run(
                            cmd,
                            capture_output=True,
                            text=True,
                            cwd=os.getcwd(),
                            timeout=60
                        )

                        if result.returncode != 0:
                            error_msg = result.stderr or result.stdout or "Conversion failed"
                            self.send_error(500, f"Conversion error: {error_msg}")
                            return

                    except subprocess.TimeoutExpired:
                        self.send_error(500, "Conversion timeout")
                        return
                    except FileNotFoundError:
                        self.send_error(500, "uv command not found. Please install uv.")
                        return

                    # Create ZIP file with results
                    chatgpt_output_dir = os.path.join(output_dir, 'chatgpt')
                    if not os.path.exists(chatgpt_output_dir):
                        self.send_error(500, "No output files generated")
                        return

                    zip_path = os.path.join(temp_dir, f'chatgpt_converted_{user_id}.zip')
                    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                        for root, dirs, files in os.walk(chatgpt_output_dir):
                            for file in files:
                                file_path = os.path.join(root, file)
                                arcname = os.path.relpath(file_path, chatgpt_output_dir)
                                zipf.write(file_path, arcname)

                    # Send ZIP file
                    with open(zip_path, 'rb') as f:
                        zip_content = f.read()

                    self.send_response(200)
                    self.send_header('Content-Type', 'application/zip')
                    self.send_header('Content-Disposition', 
                                   f'attachment; filename="chatgpt_converted_{user_id}.zip"')
                    self.send_header('Content-Length', str(len(zip_content)))
                    self.end_headers()
                    self.wfile.write(zip_content)

            except Exception as e:
                print(f"Error processing request: {e}")
                print(traceback.format_exc())
                self.send_error(500, f"Internal server error: {str(e)}")
        else:
            self.send_error(404, "Endpoint not found")

    def log_message(self, format, *args):
        """Override to customize logging."""
        print(f"{self.address_string()} - {format % args}")


def run_server(port=3010):
    """Start the web server."""
    server_address = ('', port)
    httpd = HTTPServer(server_address, ConvertHandler)

    print(f"Starting server on http://localhost:{port}")
    print("Press Ctrl+C to stop the server")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        httpd.server_close()


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description="ChatGPT to Open-WebUI converter web server")
    parser.add_argument('--port', type=int, default=3010, help='Port to run the server on (default: 3010)')
    args = parser.parse_args()

    # Check if index.html exists
    if not os.path.exists('webserver/index.html'):
        print("Error: webserver/index.html not found")
        exit(1)

    # Check if convert_chatgpt.py exists
    if not os.path.exists(os.path.join(os.path.dirname(__file__), '..', 'convert_chatgpt.py')):
        print("Error: convert_chatgpt.py not found in project root")
        exit(1)

    run_server(args.port)