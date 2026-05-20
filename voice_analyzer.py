import threading
import time
from dataclasses import dataclass, field
import numpy as np

VOICE_AVAILABLE = False
try:
    import sounddevice as sd
    VOICE_AVAILABLE = True
except ImportError:
    pass

@dataclass
class VoiceResult:
    avg_amplitude: float
    peak_amplitude: float
    amplitude_variance: float
    silence_ratio: float
    stress_score: int
    stress_flags: list

def VoiceResult_empty():
    return VoiceResult(
        avg_amplitude=0.0,
        peak_amplitude=0.0,
        amplitude_variance=0.0,
        silence_ratio=1.0,
        stress_score=0,
        stress_flags=["ACOUSTIC SENSOR OFFLINE"]
    )

class VoiceAnalyzer:
    def __init__(self):
        self.is_recording = False
        self.thread = None
        self.buffer = []
        self.lock = threading.Lock()
        self.sample_rate = 44100
        self.chunk_size = 1024
        
    def _record_loop(self):
        try:
            with sd.InputStream(samplerate=self.sample_rate, channels=1, blocksize=self.chunk_size) as stream:
                while self.is_recording:
                    data, _ = stream.read(self.chunk_size)
                    amplitude = np.abs(data).mean()
                    with self.lock:
                        self.buffer.append(float(amplitude))
                        # Keep last 3 seconds (approx 44100 / 1024 = 43 chunks per sec)
                        if len(self.buffer) > 43 * 3:
                            self.buffer.pop(0)
                        
                    time.sleep(0.01)
        except Exception:
            pass

    def start_recording(self):
        if not VOICE_AVAILABLE:
            return
        self.is_recording = True
        self.buffer = []
        self.thread = threading.Thread(target=self._record_loop, daemon=True)
        self.thread.start()

    def stop_monitoring(self):
        """Stop live mic capture without scoring (used on DISARM)."""
        if not VOICE_AVAILABLE:
            return
        self.is_recording = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        with self.lock:
            self.buffer = []

    def stop_recording(self) -> VoiceResult:
        if not VOICE_AVAILABLE:
            return VoiceResult_empty()
            
        self.is_recording = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
            
        with self.lock:
            data = list(self.buffer)
            
        if not data:
            return VoiceResult_empty()
            
        avg_amp = float(np.mean(data))
        peak_amp = float(np.max(data))
        variance = float(np.var(data))
        silence_ratio = float(sum(1 for x in data if x < 0.01) / len(data))
        
        # normalize for scoring logic (heuristic assuming peak absolute around 1.0 but sd stream can be lower, so we scale it reasonably)
        # raw amplitude from sounddevice is usually between 0.0 and 1.0
        
        score = 0
        flags = []
        
        if avg_amp > 0.4:
            score += 10
            flags.append("ELEVATED AMBIENT STRESS SIGNAL")
            
        if variance > 0.15:
            score += 8
            flags.append("ERRATIC ACOUSTIC SIGNATURE")
            
        if silence_ratio < 0.3:
            score += 7
            flags.append("CONTINUOUS VOCALIZATION DETECTED")
            
        if peak_amp > 0.8:
            score += 5
            flags.append("ACUTE STRESS SPIKE RECORDED")
            
        return VoiceResult(
            avg_amplitude=avg_amp,
            peak_amplitude=peak_amp,
            amplitude_variance=variance,
            silence_ratio=silence_ratio,
            stress_score=min(30, score),
            stress_flags=flags
        )

    def get_live_waveform(self, width: int) -> list:
        if not VOICE_AVAILABLE:
            return [0.0] * width
            
        with self.lock:
            data = list(self.buffer)
            
        if not data:
            return [0.0] * width
            
        # resample or pad to match width
        if len(data) >= width:
            return data[-width:]
        else:
            return [0.0] * (width - len(data)) + data
