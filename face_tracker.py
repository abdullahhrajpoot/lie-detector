import threading
import time
import base64
from dataclasses import dataclass, field
import numpy as np

FACE_AVAILABLE = False
try:
    import cv2
    FACE_AVAILABLE = True
except ImportError:
    pass

@dataclass
class FaceStats:
    face_detected: bool
    face_confidence: float
    gaze_stability: float
    look_away_count: int
    face_position_variance: float
    face_score: int
    face_flags: list

def FaceStats_empty():
    return FaceStats(
        face_detected=False,
        face_confidence=0.0,
        gaze_stability=0.0,
        look_away_count=0,
        face_position_variance=0.0,
        face_score=0,
        face_flags=["VISUAL SENSOR OFFLINE"]
    )

class FaceTracker:
    def __init__(self):
        self.is_tracking = False
        self.thread = None
        self.lock = threading.Lock()
        
        self.face_detected = False
        self.face_confidence = 0.0
        self.gaze_stability = 1.0
        self.look_away_count = 0
        self.position_history = []
        self.last_face_box = None
        self.frame_size = (0, 0)
        self.latest_frame = None
        self.cap = None
        
        if FACE_AVAILABLE:
            self.cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            self.face_cascade = cv2.CascadeClassifier(self.cascade_path)

    def _track_loop(self):
        try:
            while self.is_tracking:
                if self.cap is None:
                    time.sleep(0.1)
                    continue
                
                ret, frame = self.cap.read()
                if not ret:
                    with self.lock:
                        self.face_detected = False
                        self.look_away_count += 1
                        self.latest_frame = None
                        self.last_face_box = None
                    time.sleep(0.1)
                    continue
                
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
                
                with self.lock:
                    self.frame_size = (int(frame.shape[1]), int(frame.shape[0]))
                    self.latest_frame = frame.copy()
                    if len(faces) > 0:
                        self.face_detected = True
                        x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
                        self.last_face_box = (int(x), int(y), int(w), int(h))
                        # Confidence normalized by arbitrary image size ratio
                        self.face_confidence = min(1.0, (w * h) / (frame.shape[0] * frame.shape[1] * 0.5))
                        center = (x + w/2, y + h/2)
                        self.position_history.append(center)
                        
                        if len(self.position_history) > 30:
                            self.position_history.pop(0)
                            
                        if len(self.position_history) > 1:
                            pts = np.array(self.position_history)
                            var = np.var(pts, axis=0).mean() / 1000.0  # arbitrary scale
                            self.gaze_stability = max(0.0, 1.0 - var)
                    else:
                        if self.face_detected:
                            self.look_away_count += 1
                        self.face_detected = False
                        self.last_face_box = None
                        
                time.sleep(0.1)
        except Exception:
            pass

    def start(self):
        if not FACE_AVAILABLE:
            return
        if self.is_tracking:
            return
            
        self.cap = cv2.VideoCapture(0)
        self.is_tracking = True
        
        # Reset stats
        self.face_detected = False
        self.face_confidence = 0.0
        self.gaze_stability = 1.0
        self.look_away_count = 0
        self.position_history = []
        self.last_face_box = None
        self.frame_size = (0, 0)
        self.latest_frame = None
        
        self.thread = threading.Thread(target=self._track_loop, daemon=True)
        self.thread.start()

    def stop(self):
        if not FACE_AVAILABLE:
            return
            
        self.is_tracking = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
            
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        with self.lock:
            self.latest_frame = None
            self.last_face_box = None

    def get_current_stats(self) -> FaceStats:
        if not FACE_AVAILABLE:
            return FaceStats_empty()
            
        with self.lock:
            if len(self.position_history) > 1:
                pts = np.array(self.position_history)
                # arbitrary scale relative to camera frame
                var = np.var(pts, axis=0).mean() / 1000.0
            else:
                var = 0.0
            
            score = 0
            flags = []
            
            if self.look_away_count > 3:
                score += 15
                flags.append("REPEATED VISUAL FIELD AVOIDANCE")
            elif self.look_away_count > 1:
                score += 8
                flags.append("GAZE AVERSION DETECTED")
                
            if var > 0.08:
                score += 10
                flags.append("HIGH MICRO-MOVEMENT \u2014 POSTURAL ANXIETY")
                
            if not self.face_detected:
                score += 5
                flags.append("FACE OBSCURED AT ANALYSIS POINT")
                
            stats = FaceStats(
                face_detected=self.face_detected,
                face_confidence=self.face_confidence,
                gaze_stability=self.gaze_stability,
                look_away_count=self.look_away_count,
                face_position_variance=var,
                face_score=min(25, score),
                face_flags=flags
            )
            
            # Reset counters for the next question cycle
            self.look_away_count = 0
            self.position_history = []
            
            return stats

    def get_overlay_state(self) -> dict:
        if not FACE_AVAILABLE:
            return {"detected": False, "box": None, "centered": False, "distance": 1.0}

        with self.lock:
            detected = bool(self.face_detected)
            box = self.last_face_box
            fw, fh = self.frame_size

        if not detected or not box or fw <= 0 or fh <= 0:
            return {"detected": False, "box": None, "centered": False, "distance": 1.0}

        x, y, w, h = box
        cx = (x + (w / 2.0)) / fw
        cy = (y + (h / 2.0)) / fh
        tx, ty = 0.5, 0.5
        dist = float(np.sqrt((cx - tx) ** 2 + (cy - ty) ** 2))

        return {
            "detected": True,
            "box": {
                "x": x / fw,
                "y": y / fh,
                "w": w / fw,
                "h": h / fh,
                "cx": cx,
                "cy": cy,
            },
            "centered": dist <= 0.08,
            "distance": dist,
        }

    def get_latest_frame_jpeg(self, max_width: int = 640, quality: int = 70):
        if not FACE_AVAILABLE:
            return None

        with self.lock:
            frame = None if self.latest_frame is None else self.latest_frame.copy()

        if frame is None:
            return None

        try:
            h, w = frame.shape[:2]
            if max_width > 0 and w > max_width:
                scale = max_width / float(w)
                frame = cv2.resize(frame, (max_width, int(h * scale)))
            ok, encoded = cv2.imencode(
                ".jpg",
                frame,
                [int(cv2.IMWRITE_JPEG_QUALITY), int(max(30, min(95, quality)))]
            )
            if not ok:
                return None
            return base64.b64encode(encoded.tobytes()).decode("ascii")
        except Exception:
            return None

    def get_live_frame_ascii(self, width: int, height: int) -> str:
        if not FACE_AVAILABLE:
            return "[SENSOR OFFLINE]"
        with self.lock:
            return "[FACE DETECTED]" if self.face_detected else "[FACE ABSENT]"
