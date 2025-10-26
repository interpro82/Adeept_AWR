from flask import Flask, Response
from picamera import PiCamera
import threading
import io

class LegacyCameraStreamer:
    def __init__(self, width=640, height=480, fps=25, host="0.0.0.0", port=5000):
        self.width = width
        self.height = height
        self.fps = fps
        self.host = host
        self.port = port
        self.camera = PiCamera(resolution=(self.width, self.height), framerate=self.fps)
        self.app = Flask(__name__)
        self._thread = None

        self.app.add_url_rule("/", "index", self.index)
        self.app.add_url_rule("/video_feed", "video_feed", self.video_feed)

    def gen_frames(self):
        """Generator that yields JPEG frames from the camera stream."""
        stream = io.BytesIO()
        for _ in self.camera.capture_continuous(stream, format='jpeg', use_video_port=True):
            stream.seek(0)
            frame = stream.read()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            stream.seek(0)
            stream.truncate()

    def video_feed(self):
        return Response(self.gen_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")

    def index(self):
        return "<h1>🤖 Robot Camera Stream (Legacy)</h1><img src='/video_feed'>"

    def start(self):
        """Run Flask app in a background thread."""
        if self._thread and self._thread.is_alive():
            print("Camera stream already running.")
            return

        def _run():
            self.app.run(host=self.host, port=self.port, debug=False, use_reloader=False)

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()
        print(f"📷 Legacy camera stream started at http://{self.host}:{self.port}/")

    def stop(self):
        self.camera.close()
        print("📷 Camera stopped.")


if __name__ == "__main__":
    stream = LegacyCameraStreamer()
    stream.start()

    try:
        while True:
            pass
    except KeyboardInterrupt:
        stream.stop()

