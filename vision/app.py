import os
import threading
import time
import cv2
from flask import Flask, Response, jsonify, render_template

app = Flask(__name__, template_folder="templates", static_folder="static")
state = {
    "gesture": "детектор не подключён",
    "target_locked": False,
    "distance_m": None,
    "motion": "STOP",
    "emergency_stop": True,
}
lock = threading.Lock()
camera = None


def get_camera():
    global camera
    if camera is None:
        camera = cv2.VideoCapture(int(os.getenv("CAMERA_INDEX", "0")))
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    return camera


def frames():
    cap = get_camera()
    while True:
        ok, frame = cap.read()
        if not ok:
            time.sleep(0.1)
            continue
        ok, jpg = cv2.imencode(".jpg", frame)
        if ok:
            yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + jpg.tobytes() + b"\r\n"


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/video")
def video():
    return Response(frames(), mimetype="multipart/x-mixed-replace; boundary=frame")


@app.get("/api/status")
def status():
    with lock:
        return jsonify(dict(state))


@app.post("/api/stop")
def stop():
    with lock:
        state["emergency_stop"] = True
        state["motion"] = "STOP"
    return jsonify({"ok": True, "emergency_stop": True})


@app.post("/api/enable")
def enable():
    with lock:
        state["emergency_stop"] = False
    return jsonify({"ok": True, "emergency_stop": False})


if __name__ == "__main__":
    app.run(host=os.getenv("WEB_HOST", "0.0.0.0"),
            port=int(os.getenv("WEB_PORT", "5000")), threaded=True)
