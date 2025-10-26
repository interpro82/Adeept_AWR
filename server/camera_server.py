from flask import Flask, Response
from picamera2 import Picamera2
import threading
import cv2


class CameraStreamer:
    def __init__(self, width=640, height=480, fps=25, host="0.0.0.0", port=5000):
        self.width = width
        self.height = height
        self.fps = fps
        self.host = host
        self.port = port
        self.camera = None
        self.app = Flask(__name__)
        self._thread = None

        # Register Flask routes
        self.app.add_url_rule("/", "index", self.index)
        self.app.add_url_rule("/video_feed", "video_feed", self.video_feed)

    def _init_camera(self):
        """Initialize the PiCamera2 if not already started."""
        if self.camera is None:
            self.camera = Picamera2()
            self.camera.configure(
                self.camera.create_preview_configuration(main={"size": (self.width, self.height)})
            )
            self.camera.start()

    def gen_frames(self):
        """Generator that yields JPEG frames."""
        self._init_camera()
        while True:
            frame = self.camera.capture_array()
            ret, jpeg = cv2.imencode(".jpg", frame)
            if not ret:
                continue
            yield (b"--frame\r\n"
                   b"Content-Type: image/jpeg\r\n\r\n" + jpeg.tobytes() + b"\r\n")

    def video_feed(self):
        """Flask route for video stream."""
        return Response(self.gen_frames(), mimetype="multipart/x-mixed-replace; boundary=frame")

    def index(self):
        """Flask home page."""
        return "<h1>🤖 Robot Camera Stream</h1><img src='/video_feed'>"

    def start(self):
        """Start the Flask server in a background thread."""
        if self._thread and self._thread.is_alive():
            print("Camera stream already running.")
            return

        def _run():
            self.app.run(host=self.host, port=self.port, debug=False, use_reloader=False)

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()
        print(f"📷 Camera streaming started at http://{self.host}:{self.port}/")

    def stop(self):
        """Stop the camera."""
        if self.camera:
            self.camera.stop()
            self.camera = None
            print("📷 Camera stopped.")


if __name__ == "__main__":
    # Example usage
    stream = CameraStreamer()
    stream.start()

    try:
        while True:
            pass
    except KeyboardInterrupt:
        stream.stop()
