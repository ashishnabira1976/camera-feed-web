// DOM Elements
const videoFeed = document.getElementById('videoFeed');
const placeholder = document.getElementById('placeholder');
const quickStartBtn = document.getElementById('quickStartBtn');
const toggleCameraBtn = document.getElementById('toggleCameraBtn');
const mirrorBtn = document.getElementById('mirrorBtn');
const snapshotBtn = document.getElementById('snapshotBtn');
const fullscreenBtn = document.getElementById('fullscreenBtn');
const cameraSelect = document.getElementById('cameraSelect');
const statusBadge = document.getElementById('statusBadge');
const statusText = document.getElementById('statusText');
const errorBanner = document.getElementById('errorBanner');
const errorMessage = document.getElementById('errorMessage');
const insecureWarning = document.getElementById('insecureWarning');
const resolutionOverlay = document.getElementById('resolutionOverlay');
const resolutionText = document.getElementById('resolutionText');
const snapshotSection = document.getElementById('snapshotSection');
const snapshotCanvas = document.getElementById('snapshotCanvas');
const snapshotPreview = document.getElementById('snapshotPreview');
const downloadPhotoBtn = document.getElementById('downloadPhotoBtn');
const closeSnapshotBtn = document.getElementById('closeSnapshotBtn');

// State
let currentStream = null;
let isStreaming = false;
let isMirrored = false;

// Check security context
if (!window.isSecureContext && location.hostname !== 'localhost' && location.hostname !== '127.0.0.1') {
  insecureWarning.classList.remove('hidden');
}

// Check WebRTC support
if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
  showError('Your browser does not support camera access (mediaDevices.getUserMedia). Please use a modern version of Chrome.');
  toggleCameraBtn.disabled = true;
  quickStartBtn.disabled = true;
}

// Event Listeners
quickStartBtn.addEventListener('click', () => startCamera());
toggleCameraBtn.addEventListener('click', () => {
  if (isStreaming) {
    stopCamera();
  } else {
    startCamera();
  }
});

mirrorBtn.addEventListener('click', toggleMirror);
snapshotBtn.addEventListener('click', captureSnapshot);
fullscreenBtn.addEventListener('click', toggleFullscreen);
closeSnapshotBtn.addEventListener('click', () => {
  snapshotSection.classList.add('hidden');
});

cameraSelect.addEventListener('change', () => {
  if (isStreaming) {
    // Restart with selected camera
    startCamera(cameraSelect.value);
  }
});

// Update resolution overlay when video metadata is loaded
videoFeed.addEventListener('loadedmetadata', () => {
  if (videoFeed.videoWidth && videoFeed.videoHeight) {
    resolutionText.textContent = `${videoFeed.videoWidth} × ${videoFeed.videoHeight}`;
    resolutionOverlay.classList.remove('hidden');
  }
});

/**
 * Start the camera stream
 */
async function startCamera(deviceId = null) {
  hideError();
  setStatus('starting', 'Connecting...');

  // Stop any existing stream
  if (currentStream) {
    stopTracks(currentStream);
  }

  const constraints = {
    video: {
      width: { ideal: 1920 },
      height: { ideal: 1080 }
    },
    audio: false
  };

  if (deviceId) {
    constraints.video.deviceId = { exact: deviceId };
  }

  try {
    const stream = await navigator.mediaDevices.getUserMedia(constraints);
    currentStream = stream;
    videoFeed.srcObject = stream;
    isStreaming = true;

    // UI Updates
    placeholder.classList.add('hidden');
    videoFeed.classList.remove('hidden');
    setStatus('live', 'Live');
    updateToggleButton(true);
    mirrorBtn.disabled = false;
    snapshotBtn.disabled = false;
    fullscreenBtn.disabled = false;
    cameraSelect.disabled = false;

    // Populate camera list (labels become visible after permission is granted)
    await listVideoDevices();

  } catch (err) {
    handleCameraError(err);
    setStatus('error', 'Camera Error');
    updateToggleButton(false);
  }
}

/**
 * Stop the camera stream
 */
function stopCamera() {
  if (currentStream) {
    stopTracks(currentStream);
    currentStream = null;
  }

  videoFeed.srcObject = null;
  isStreaming = false;

  // UI Updates
  placeholder.classList.remove('hidden');
  resolutionOverlay.classList.add('hidden');
  setStatus('idle', 'Camera Off');
  updateToggleButton(false);
  mirrorBtn.disabled = true;
  snapshotBtn.disabled = true;
  fullscreenBtn.disabled = true;
}

/**
 * Helper to stop all tracks in a MediaStream
 */
function stopTracks(stream) {
  stream.getTracks().forEach(track => {
    track.stop();
  });
}

/**
 * Enumerate connected video input devices
 */
async function listVideoDevices() {
  try {
    const devices = await navigator.mediaDevices.enumerateDevices();
    const videoDevices = devices.filter(d => d.kind === 'videoinput');

    const currentSelected = cameraSelect.value;
    cameraSelect.innerHTML = '';

    if (videoDevices.length === 0) {
      const opt = document.createElement('option');
      opt.text = 'Default Camera';
      opt.value = '';
      cameraSelect.appendChild(opt);
      return;
    }

    videoDevices.forEach((device, index) => {
      const option = document.createElement('option');
      option.value = device.deviceId;
      option.text = device.label || `Camera ${index + 1}`;

      // Mark the active track device as selected if possible
      const currentTrack = currentStream && currentStream.getVideoTracks()[0];
      const activeDeviceId = currentTrack && currentTrack.getSettings().deviceId;

      if (activeDeviceId === device.deviceId || (!activeDeviceId && index === 0)) {
        option.selected = true;
      }

      cameraSelect.appendChild(option);
    });
  } catch (err) {
    console.warn('Could not enumerate devices:', err);
  }
}

/**
 * Toggle horizontal mirror mode
 */
function toggleMirror() {
  isMirrored = !isMirrored;
  if (isMirrored) {
    videoFeed.classList.add('mirrored');
    mirrorBtn.classList.add('btn-primary');
    mirrorBtn.classList.remove('btn-secondary');
  } else {
    videoFeed.classList.remove('mirrored');
    mirrorBtn.classList.remove('btn-primary');
    mirrorBtn.classList.add('btn-secondary');
  }
}

/**
 * Take snapshot from video feed
 */
function captureSnapshot() {
  if (!isStreaming || !videoFeed.videoWidth) return;

  const width = videoFeed.videoWidth;
  const height = videoFeed.videoHeight;

  snapshotCanvas.width = width;
  snapshotCanvas.height = height;
  const ctx = snapshotCanvas.getContext('2d');

  if (isMirrored) {
    ctx.translate(width, 0);
    ctx.scale(-1, 1);
  }

  ctx.drawImage(videoFeed, 0, 0, width, height);

  const dataUrl = snapshotCanvas.toDataURL('image/png');
  snapshotPreview.src = dataUrl;
  downloadPhotoBtn.href = dataUrl;
  downloadPhotoBtn.download = `snapshot-${new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-')}.png`;

  snapshotSection.classList.remove('hidden');
  snapshotSection.scrollIntoView({ behavior: 'smooth' });
}

/**
 * Fullscreen toggle
 */
function toggleFullscreen() {
  if (!document.fullscreenElement) {
    videoFeed.requestFullscreen().catch(err => {
      console.error(`Fullscreen request failed: ${err.message}`);
    });
  } else {
    document.exitFullscreen();
  }
}

/**
 * Set status badge UI
 */
function setStatus(state, label) {
  statusBadge.className = `status-badge ${state}`;
  statusText.textContent = label;
}

/**
 * Update the Start / Stop button UI
 */
function updateToggleButton(active) {
  if (active) {
    toggleCameraBtn.innerHTML = `
      <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <rect x="6" y="4" width="4" height="16"></rect>
        <rect x="14" y="4" width="4" height="16"></rect>
      </svg>
      <span>Stop Camera</span>
    `;
    toggleCameraBtn.classList.remove('btn-primary');
    toggleCameraBtn.classList.add('btn-danger');
  } else {
    toggleCameraBtn.innerHTML = `
      <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polygon points="5 3 19 12 5 21 5 3"></polygon>
      </svg>
      <span>Start Camera</span>
    `;
    toggleCameraBtn.classList.remove('btn-danger');
    toggleCameraBtn.classList.add('btn-primary');
  }
}

/**
 * Handle user media errors with friendly messages
 */
function handleCameraError(error) {
  console.error('Camera access error:', error);
  let message = 'An unexpected error occurred while accessing the camera.';

  if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
    message = 'Camera permission was denied. Please click the lock or camera icon in Chrome\'s address bar and set Camera to "Allow", then try again.';
  } else if (error.name === 'NotFoundError' || error.name === 'DevicesNotFoundError') {
    message = 'No camera device found. Please make sure your laptop webcam is enabled or an external camera is plugged in.';
  } else if (error.name === 'NotReadableError' || error.name === 'TrackStartError') {
    message = 'Could not access the camera. It might already be in use by another application (e.g., Zoom, Google Meet).';
  } else if (error.name === 'OverconstrainedError') {
    message = 'The requested camera resolution or device is not supported.';
  } else if (error.message) {
    message = `Camera error: ${error.message}`;
  }

  showError(message);
}

function showError(msg) {
  errorMessage.textContent = msg;
  errorBanner.classList.remove('hidden');
}

function hideError() {
  errorBanner.classList.add('hidden');
}
