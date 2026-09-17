# Webcam Streaming & Viewer Web App

A versatile camera application designed for Google Chrome and modern browsers. It supports:
- **Local viewing** on a single laptop
- **Local network streaming** between laptops, phones, or tablets over Wi-Fi/LAN
- **Worldwide Internet streaming** with secure password protection

---

## 1. View Camera Locally on This Laptop

If you just want to see your webcam on this machine:

1. Run a local web server:
   ```bash
   python3 -m http.server 8000
   ```
2. Open Chrome to [http://localhost:8000](http://localhost:8000).
3. Click **"Turn On Camera"** and allow camera access.

---

## 2. Stream to Another Laptop / Device (Local Wi-Fi / LAN)

To turn this laptop into a live streaming camera and watch it on another laptop, phone, or TV on the same Wi-Fi:

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
     `http://<THIS-LAPTOP-IP>:8080` (e.g., `http://192.168.1.50:8080`)
   - The live feed will stream with low latency!
   - **No HTTPS issues**: Remote viewers receive standard image frames, so Chrome does not block or require special permissions on the viewing laptop.

---

## 3. Streaming Over the Internet (Access from Anywhere in the World)

To view your camera feed from outside your home/office network (over cellular data or a different Wi-Fi), expose your local port `8080` using a secure tunnel.

### 🔒 Security First: Password Protection
When exposing a live camera to the internet, always protect it with a password. `server.py` includes built-in HTTP Basic Authentication:

```bash
python3 server.py --port 8080 --auth admin:yourpassword123
```
Anyone visiting the stream will be required to enter this username and password before seeing any video.

---

### Option A: Cloudflare Tunnel (Recommended — Free, Fast & Most Reliable)
Cloudflare provides a free, secure public HTTPS URL without needing router port-forwarding or an account.

1. **Install `cloudflared`**:
   - **macOS**: `brew install cloudflared`
   - **Linux**: `sudo apt install cloudflared` (or download from [Cloudflare](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/))
   - **Windows**: `winget install --id Cloudflare.cloudflared`

2. **Start your streaming server with password protection**:
   ```bash
   python3 server.py --port 8080 --auth admin:yourpassword123
   ```

3. **In a second terminal, start the Cloudflare tunnel**:
   ```bash
   cloudflared tunnel --url http://localhost:8080
   ```

4. Cloudflare will generate a secure public URL, for example:
   `https://random-words-1234.trycloudflare.com`

5. Open that URL on any device, anywhere in the world!

---

### Option B: Zero-Install SSH Tunnel (Instant — No New Software Needed)
If you don't want to install anything, you can create a public HTTPS tunnel using standard `ssh`:

1. Start your server:
   ```bash
   python3 server.py --port 8080 --auth admin:yourpassword123
   ```

2. In a second terminal, run:
   ```bash
   ssh -p 443 -R0:localhost:8080 a.pinggy.io
   ```
   *(or `ssh -R 80:localhost:8080 nokey@localhost.run`)*

3. It will display a temporary public `https://...` link right in your terminal.

---

### Option C: Ngrok
1. Download and authenticate [ngrok](https://ngrok.com/).
2. Run:
   ```bash
   ngrok http 8080
   ```
3. Copy the provided public URL (e.g. `https://xxxx.ngrok-free.app`).

---

### Option D: Tailscale (Best for Private Personal Use)
If you only want access between your own devices (e.g., your laptop and your phone) without making anything public on the internet:
1. Install [Tailscale](https://tailscale.com/) on both devices.
2. Sign in with the same account.
3. Access the camera stream using the laptop's private 100.x.x.x IP address.

---

## 4. Direct OpenCV Hardware Mode (Optional)

If you install `opencv-python`, Python can directly access your laptop's camera hardware without needing to open the `/broadcast` browser tab:

```bash
pip install -r requirements.txt
python3 server.py --opencv
```

---

## File Structure

- [server.py](file:///usr/local/google/home/nabira/camera-feed-web/server.py): Multi-threaded Python streaming server (supports Web Broadcaster, OpenCV capture, and HTTP Basic Auth).
- [broadcast.html](file:///usr/local/google/home/nabira/camera-feed-web/broadcast.html): Broadcaster interface to stream webcam frames from the source laptop.
- [viewer.html](file:///usr/local/google/home/nabira/camera-feed-web/viewer.html): Remote viewer page with live stream, FPS counter, and snapshot tool.
- [index.html](file:///usr/local/google/home/nabira/camera-feed-web/index.html): Standalone single-machine camera viewer.
- [style.css](file:///usr/local/google/home/nabira/camera-feed-web/style.css): Dark-mode stylesheet used across all pages.
- [app.js](file:///usr/local/google/home/nabira/camera-feed-web/app.js): WebRTC camera logic for local index page.
- [requirements.txt](file:///usr/local/google/home/nabira/camera-feed-web/requirements.txt): Optional dependencies for direct OpenCV hardware capture.
