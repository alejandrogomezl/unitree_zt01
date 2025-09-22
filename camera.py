import cv2
import numpy as np
import asyncio
import logging
import threading
import time
from queue import Queue
from flask import Flask, Response, render_template_string
from go2_webrtc_driver.webrtc_driver import Go2WebRTCConnection, WebRTCConnectionMethod
from aiortc import MediaStreamTrack

# Enable logging for debugging
logging.basicConfig(level=logging.FATAL)

# Flask app setup
app = Flask(__name__)

# Global variables
frame_queue = Queue()
latest_frame = None
frame_lock = threading.Lock()

# HTML template for the web viewer
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Go2 WebRTC Video Stream</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f0f0f0;
            text-align: center;
        }
        .container {
            max-width: 1280px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        h1 {
            color: #333;
            margin-bottom: 30px;
        }
        .video-container {
            position: relative;
            display: inline-block;
            border: 2px solid #333;
            border-radius: 5px;
        }
        img {
            max-width: 100%;
            height: auto;
            display: block;
        }
        .info {
            margin-top: 20px;
            padding: 10px;
            background-color: #e9e9e9;
            border-radius: 5px;
            font-family: monospace;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Go2 WebRTC Video Stream</h1>
        <div class="video-container">
            <img src="{{ url_for('video_feed') }}" alt="Video Stream">
        </div>
        <div class="info">
            <p>Stream URL: <code>{{ url_for('video_feed', _external=True) }}</code></p>
            <p>Refresh the page if the stream doesn't load</p>
        </div>
    </div>
</body>
</html>
"""

def generate_frames():
    """Generator function to yield video frames for streaming"""
    global latest_frame
    
    while True:
        with frame_lock:
            if latest_frame is not None:
                # Encode frame as JPEG
                ret, buffer = cv2.imencode('.jpg', latest_frame, 
                                         [cv2.IMWRITE_JPEG_QUALITY, 85])
                if ret:
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
        
        time.sleep(0.033)  # ~30 FPS

@app.route('/')
def index():
    """Main page with video viewer"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/video_feed')
def video_feed():
    """Video streaming route"""
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/status')
def status():
    """Status endpoint"""
    with frame_lock:
        has_frame = latest_frame is not None
        frame_shape = latest_frame.shape if has_frame else None
    
    return {
        'status': 'running',
        'has_frame': has_frame,
        'frame_shape': str(frame_shape) if frame_shape else None,
        'queue_size': frame_queue.qsize()
    }

def main():
    global latest_frame
    
    # Choose a connection method (uncomment the correct one)
    conn = Go2WebRTCConnection(WebRTCConnectionMethod.LocalSTA, ip="192.168.8.181")
    # conn = Go2WebRTCConnection(WebRTCConnectionMethod.LocalSTA, serialNumber="B42D2000XXXXXXXX")
    # conn = Go2WebRTCConnection(WebRTCConnectionMethod.Remote, serialNumber="B42D2000XXXXXXXX", username="email@gmail.com", password="pass")
    # conn = Go2WebRTCConnection(WebRTCConnectionMethod.LocalAP)

    # Async function to receive video frames and put them in the queue
    async def recv_camera_stream(track: MediaStreamTrack):
        global latest_frame
        while True:
            try:
                frame = await track.recv()
                # Convert the frame to a NumPy array
                img = frame.to_ndarray(format="bgr24")
                frame_queue.put(img)
                
                # Update latest frame for web streaming
                with frame_lock:
                    latest_frame = img.copy()
                    
            except Exception as e:
                logging.error(f"Error receiving frame: {e}")
                break

    def run_asyncio_loop(loop):
        asyncio.set_event_loop(loop)
        async def setup():
            try:
                # Connect to the device
                await conn.connect()
                print("Connected to Go2 device")

                # Switch video channel on and start receiving video frames
                conn.video.switchVideoChannel(True)
                print("Video channel switched on")

                # Add callback to handle received video frames
                conn.video.add_track_callback(recv_camera_stream)
                print("Video track callback added")
                
            except Exception as e:
                logging.error(f"Error in WebRTC connection: {e}")
                print(f"WebRTC connection error: {e}")

        # Run the setup coroutine and then start the event loop
        loop.run_until_complete(setup())
        loop.run_forever()

    # Create a new event loop for the asyncio code
    loop = asyncio.new_event_loop()

    # Start the asyncio event loop in a separate thread
    asyncio_thread = threading.Thread(target=run_asyncio_loop, args=(loop,))
    asyncio_thread.daemon = True
    asyncio_thread.start()

    # Frame processing thread
    def process_frames():
        while True:
            if not frame_queue.empty():
                img = frame_queue.get()
                print(f"Frame - Shape: {img.shape}, Type: {img.dtype}, Size: {img.size}")
            else:
                time.sleep(0.01)

    # Start frame processing in a separate thread
    processing_thread = threading.Thread(target=process_frames)
    processing_thread.daemon = True
    processing_thread.start()

    # Start Flask web server
    print("Starting web server...")
    print("Video stream will be available at:")
    print("  Local: http://localhost:5000")
    print("  Network: http://0.0.0.0:5000")
    print("  Direct stream: http://localhost:5000/video_feed")
    print("\nPress Ctrl+C to stop")
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        # Stop the asyncio event loop
        loop.call_soon_threadsafe(loop.stop)

if __name__ == "__main__":
    main()