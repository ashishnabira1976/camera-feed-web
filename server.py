#!/usr/bin/env python3
"""
Python Camera Streaming Server
Allows viewing this laptop's camera feed from another laptop, phone, or browser on the network.

Supports two capture modes:
1. Direct OpenCV Mode: Uses cv2.VideoCapture to capture webcam directly in Python.
2. Web Broadcaster Mode: Zero-dependency fallback using browser camera capture via /broadcast.
"""

import argparse
import io
import json
import os
import socket
import sys
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler, ThreadingHTTPServer

# Optional OpenCV support
try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Global streaming state
class StreamHub:
    def __init__(self):
        self.lock = threading.Lock()
        self.condition = threading.Condition(self.lock)
        self.latest_frame = None
        self.frame_timestamp = 0
        self.mode = "none"  # "opencv" or "web"
        self.viewer_count = 0
        self.frame_count = 0
        self.fps = 0.0
        self._last_fps_calc = time.time()
        self._frames_since_calc = 0

    def update_frame(self, frame_bytes, mode="web"):
        with self.condition:
            self.latest_frame = frame_bytes
            self.frame_timestamp = time.time()
            self.mode = mode
            self.frame_count += 1
            self._frames_since_calc += 1

            now = time.time()
            elapsed = now - self._last_fps_calc
            if elapsed >= 1.0:
                self.fps = round(self._frames_since_calc / elapsed, 1)
                self._frames_since_calc = 0
                self._last_fps_calc = now

            self.condition.notify_all()

    def get_latest_frame(self):
        with self.lock:
            return self.latest_frame

    def wait_for_frame(self, last_timestamp, timeout=1.0):
        with self.condition:
            if self.frame_timestamp > last_timestamp:
                return self.latest_frame, self.frame_timestamp
            self.condition.wait(timeout=timeout)
            if self.frame_timestamp > last_timestamp:
                return self.latest_frame, self.frame_timestamp
            return None, last_timestamp

hub = StreamHub()

def get_local_ips():
    """Find local network IP addresses for easy remote connection."""
    ips = set()
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('10.255.255.255', 1))
        ips.add(s.getsockname()[0])
        s.close()
    except Exception:
        pass
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None):
            ip = info[4][0]
            if not ip.startswith('127.'):
                ips.add(ip)
    except Exception:
        pass
    return sorted(list(ips)) or ['127.0.0.1']


class StreamingHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Format message safely
        try:
            msg = format % args
        except Exception:
            msg = str(format)
        # Silence high-frequency stream and upload logs
        if "/stream" in msg or "/upload" in msg or "/status" in msg:
            return
        sys.stderr.write(f"[{self.log_date_time_string()}] {msg}\n")

    def do_HEAD(self):
        path = self.path.split('?')[0]
        if path in ['/', '/index.html', '/viewer', '/broadcast', '/style.css', '/status']:
            self.send_response(200)
            self.end_headers()
        else:
            self.send_error(404, 'Not Found')

    def do_GET(self):
        path = self.path.split('?')[0]

        # 1. Main Viewer Page
        if path == '/' or path == '/index.html' or path == '/viewer':
            self.serve_file(os.path.join(BASE_DIR, 'viewer.html'), 'text/html')
            return

        # 2. Broadcaster Page (used when capturing from browser)
        if path == '/broadcast':
            self.serve_file(os.path.join(BASE_DIR, 'broadcast.html'), 'text/html')
            return

        # 3. Static CSS / JS
        if path == '/style.css':
            self.serve_file(os.path.join(BASE_DIR, 'style.css'), 'text/css')
            return

        # 4. Status API
        if path == '/status':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            data = {
                "active": hub.latest_frame is not None and (time.time() - hub.frame_timestamp < 3.0),
                "mode": hub.mode,
                "fps": hub.fps,
                "viewers": hub.viewer_count,
                "totalFrames": hub.frame_count,
                "opencvAvailable": OPENCV_AVAILABLE
            }
            self.wfile.write(json.dumps(data).encode('utf-8'))
            return

        # 5. Snapshot (single JPEG frame)
        if path == '/snapshot':
            frame = hub.get_latest_frame()
            if frame:
                self.send_response(200)
                self.send_header('Content-Type', 'image/jpeg')
                self.send_header('Content-Length', str(len(frame)))
                self.send_header('Cache-Control', 'no-cache')
                self.end_headers()
                self.wfile.write(frame)
            else:
                self.send_error(503, 'No camera frame available yet')
            return

        # 6. MJPEG Stream Endpoint
        if path == '/stream' or path == '/video_feed':
            self.handle_mjpeg_stream()
            return

        self.send_error(404, 'Not Found')

    def do_POST(self):
        path = self.path.split('?')[0]

        # Ingestion endpoint for browser broadcaster
        if path == '/upload':
            try:
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length > 0:
                    frame_bytes = self.rfile.read(content_length)
                    hub.update_frame(frame_bytes, mode="web")
                    self.send_response(200)
                    self.send_header('Content-Type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(b'OK')
                else:
                    self.send_error(400, 'Empty body')
            except Exception as e:
                self.send_error(500, f'Error receiving frame: {e}')
            return

        self.send_error(404, 'Not Found')

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def handle_mjpeg_stream(self):
        """Streams continuous multipart/x-mixed-replace JPEG frames to the client."""
        self.send_response(200)
        self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=frame')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate, pre-check=0, post-check=0, max-age=0')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Connection', 'close')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

        with hub.lock:
            hub.viewer_count += 1

        last_timestamp = 0
        try:
            while True:
                frame, last_timestamp = hub.wait_for_frame(last_timestamp, timeout=1.0)
                if frame is not None:
                    header = (
                        b'--frame\r\n'
                        b'Content-Type: image/jpeg\r\n'
                        b'Content-Length: ' + str(len(frame)).encode() + b'\r\n'
                        b'\r\n'
                    )
                    self.wfile.write(header)
                    self.wfile.write(frame)
                    self.wfile.write(b'\r\n')
                else:
                    # Keep-alive ping if no frames arriving
                    self.wfile.write(b'--frame\r\n\r\n')
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            with hub.lock:
                hub.viewer_count = max(0, hub.viewer_count - 1)

    def serve_file(self, filepath, content_type):
        if not os.path.isfile(filepath):
            self.send_error(404, f'File not found: {os.path.basename(filepath)}')
            return
        try:
            with open(filepath, 'rb') as f:
                content = f.read()
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(500, f'Internal error reading file: {e}')


def opencv_capture_worker(device_index=0, width=1280, height=720, fps=30):
    """Worker thread that directly captures from local webcam via OpenCV."""
    print(f"[OpenCV] Opening camera index {device_index}...")
    cap = cv2.VideoCapture(device_index)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    cap.set(cv2.CAP_PROP_FPS, fps)

    if not cap.isOpened():
        print(f"[OpenCV] Warning: Could not open camera {device_index}.")
        print("[OpenCV] Switching to Web Broadcaster mode. Open /broadcast in your browser to capture webcam.")
        return

    print(f"[OpenCV] Camera active! Capturing at {width}x{height} @ {fps}fps...")
    encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), 80]

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.05)
                continue
            ret, jpeg = cv2.imencode('.jpg', frame, encode_params)
            if ret:
                hub.update_frame(jpeg.tobytes(), mode="opencv")
            time.sleep(1.0 / fps)
    except Exception as e:
        print(f"[OpenCV] Error in capture loop: {e}")
    finally:
        cap.release()


def main():
    parser = argparse.ArgumentParser(description="Python Webcam Streaming Server")
    parser.add_argument('--port', type=int, default=8080, help="Port to listen on (default: 8080)")
    parser.add_argument('--host', type=str, default='0.0.0.0', help="Host interface (default: 0.0.0.0)")
    parser.add_argument('--opencv', action='store_true', help="Force OpenCV direct hardware capture")
    parser.add_argument('--camera', type=int, default=0, help="OpenCV camera device index (default: 0)")
    args = parser.parse_args()

    local_ips = get_local_ips()
    primary_ip = local_ips[0]

    use_opencv = args.opencv
    if not use_opencv and OPENCV_AVAILABLE:
        # Check if a camera can be opened
        test_cap = cv2.VideoCapture(args.camera)
        if test_cap.isOpened():
            test_cap.release()
            use_opencv = True

    if use_opencv and OPENCV_AVAILABLE:
        capture_thread = threading.Thread(
            target=opencv_capture_worker,
            args=(args.camera,),
            daemon=True
        )
        capture_thread.start()
        mode_label = "Direct Hardware (OpenCV)"
    else:
        mode_label = "Web Broadcaster (/broadcast)"

    server = ThreadingHTTPServer((args.host, args.port), StreamingHandler)

    print("=" * 65)
    print("  PYTHON WEBCAM STREAMING SERVER")
    print("=" * 65)
    print(f" Mode: {mode_label}")
    print()
    print(" [1] On THIS laptop (Camera Source):")
    if use_opencv and OPENCV_AVAILABLE:
        print(f"     -> OpenCV is streaming camera {args.camera} automatically in background!")
    else:
        print(f"     -> Open Chrome to broadcast your camera:")
        print(f"        http://localhost:{args.port}/broadcast")
    print()
    print(" [2] On the OTHER laptop or phone (Remote Viewer):")
    print(f"     -> Open Chrome / Safari / Edge to watch the live feed:")
    for ip in local_ips:
        print(f"        http://{ip}:{args.port}")
    print()
    print(" [3] Raw MJPEG Stream URL (e.g. for VLC, scripts, or embedding):")
    print(f"        http://{primary_ip}:{args.port}/stream")
    print("=" * 65)
    print("Press Ctrl+C to stop the server.\n")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down streaming server.")
        server.server_close()


if __name__ == '__main__':
    main()
