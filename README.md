# Webcam Streaming & Viewer Web App

A versatile camera application designed for Google Chrome and modern browsers. It supports both **local viewing** and **network streaming** to view a laptop's camera from another laptop, phone, or tablet.

---

## Quick Start: Two Ways to Use

### 1. View Camera Locally on This Laptop
If you just want to see your webcam on this machine:
1. Run a local web server:
   ```bash
   python3 -m http.server 8000
   ```
2. Open Chrome to [http://localhost:8000](http://localhost:8000).
3. Click **"Turn On Camera"** and allow camera access.

---

### 2. Stream This Laptop's Camera to ANOTHER Laptop / Device
To turn this laptop into a live streaming camera and watch it on another laptop, phone, or TV:

1. **Start the streaming server on this laptop (Source)**:
   ```bash
   cd ~/camera-feed-web
   python3 server.py --port 8080
   ```
   The terminal will display your local IP address (e.g., `http://192.168.1.50:8080`).

2. **On THIS laptop (Camera Source)**:
   - Open Google Chrome and go to:
     [http://localhost:8080/broadcast](http://localhost:8080/broadcast)
   - Click **"Start Broadcasting"** and allow camera access.

3. **On the OTHER laptop or phone (Remote Viewer)**:
   - Open any browser (Chrome, Edge, Safari, Firefox) and navigate to:
     `http://<THIS-LAPTOP-IP>:8080` (e.g. `http://192.168.1.50:8080`)
   - The live feed will stream with low latency!
   - **No HTTPS issues**: Remote viewers receive standard image frames, so Chrome does not block or require special permissions on the viewing laptop.

---

## Direct OpenCV Hardware Mode (Optional)

If you install `opencv-python`, Python can directly access your laptop's camera hardware without needing to open the `/broadcast` browser tab:

```bash
pip install -r requirements.txt
python3 server.py --opencv
```

---

## File Structure

- [server.py](file:///usr/local/google/home/nabira/camera-feed-web/server.py): Multi-threaded Python streaming server (supports Web and OpenCV capture).
- [viewer.html](file:///usr/local/google/home/nabira/camera-feed-web/viewer.html): Remote viewer page with live MJPEG stream, FPS counter, and snapshot tool.
- [broadcast.html](file:///usr/local/google/home/nabira/camera-feed-web/broadcast.html): Broadcaster page that captures webcam and pushes frames to `server.py`.
- [index.html](file:///usr/local/google/home/nabira/camera-feed-web/index.html): Standalone single-machine camera viewer.
- [style.css](file:///usr/local/google/home/nabira/camera-feed-web/style.css): Dark-mode stylesheet used across all pages.


  ### Repository URL

  https://github.com/ashishnabira1976/camera-feed-web
  ──────
  ### What's in the Repository

  • index.html — Standalone single-machine camera feed viewer.
  • style.css — Dark-mode stylesheet with responsive layout.
  • app.js — WebRTC / MediaDevices camera handler with snapshot & mirror features.
  • server.py — Python streaming server for multi-device Wi-Fi/LAN streaming.
  • broadcast.html — Broadcaster interface to stream webcam frames from the source laptop.
  • viewer.html — Remote viewer page for other laptops, phones, or tablets.
  • requirements.txt — Optional dependencies for direct OpenCV hardware capture.
  • README.md — Documentation with quick-start guides for both local viewing and network streaming.
  
