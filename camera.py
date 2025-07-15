import cv2
import numpy as np
import asyncio
import logging
import threading
import time
from queue import Queue
from flask import Flask, Response
from go2_webrtc_driver.webrtc_driver import Go2WebRTCConnection, WebRTCConnectionMethod
from aiortc import MediaStreamTrack

# === CONFIGURACIÓN ===
IP_UNITREE = "192.168.4.15"  # Cambia esto por la IP de tu robot
PORT = 5001

# === LOGGING ===
logging.basicConfig(level=logging.FATAL)

# === FLASK APP ===
app = Flask(__name__)
frame_queue = Queue()

# === WEBRTC CONNECTION ===
conn = Go2WebRTCConnection(WebRTCConnectionMethod.LocalSTA, ip=IP_UNITREE)

async def recv_camera_stream(track: MediaStreamTrack):
    while True:
        frame = await track.recv()
        img = frame.to_ndarray(format="bgr24")
        frame_queue.put(img)

def run_asyncio_loop(loop):
    asyncio.set_event_loop(loop)

    async def setup():
        try:
            await conn.connect()
            conn.video.switchVideoChannel(True)
            conn.video.add_track_callback(recv_camera_stream)
        except Exception as e:
            logging.error(f"Error in WebRTC connection: {e}")

    loop.run_until_complete(setup())
    loop.run_forever()

loop = asyncio.new_event_loop()
asyncio_thread = threading.Thread(target=run_asyncio_loop, args=(loop,))
asyncio_thread.start()

# === STREAMING LOGIC ===
def generate_stream():
    while True:
        if not frame_queue.empty():
            frame = frame_queue.get()
            ret, jpeg = cv2.imencode('.jpg', frame)
            if ret:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')
        else:
            time.sleep(0.01)

# === ROUTES ===
@app.route('/')
def index():
    return '<h1>Unitree Go2 Streaming</h1><img src="/video_feed">'

@app.route('/video_feed')
def video_feed():
    return Response(generate_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')

# === RUN FLASK ===
if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=PORT, threaded=True)
    finally:
        loop.call_soon_threadsafe(loop.stop)
        asyncio_thread.join()
