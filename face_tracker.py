import threading
import time
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
                    time.sleep(0.1)
                    continue
                
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))
                
                with self.lock:
                    if len(faces) > 0:
                        self.face_detected = True
                        x, y, w, h = faces[0]
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
                        
                time.sleep(0.1)
        except Exception:
            pass

    def start(self):
        if not FACE_AVAILABLE:
            return
            
        self.cap = cv2.VideoCapture(0)
        self.is_tracking = True
        
        # Reset stats
        self.face_detected = False
        self.face_confidence = 0.0
        self.gaze_stability = 1.0
        self.look_away_count = 0
        self.position_history = []
        
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

    def get_live_frame_ascii(self, width: int, height: int) -> str:
        if not FACE_AVAILABLE:
            return "[SENSOR OFFLINE]"
        with self.lock:
            return "[FACE DETECTED]" if self.face_detected else "[FACE ABSENT]"
