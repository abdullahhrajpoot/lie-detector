"""
voice_analyzer.py — POLYTRUTH v5.0
Microphone amplitude capture for acoustic stress heuristics.

Grounded in voice-stress literature (see documentation_and_working.txt).
LIMITATION: coarse amplitude stats only — not MFCC/F0/jitter ML (Fatma et al. 2024).
Commercial VSA accuracy is often near chance; this layer is demonstrative.
Accuracy is not claimed.
"""

import threading
import time
from dataclasses import dataclass
import numpy as np

from scoring import (
    VOICE_AVG_AMP_THRESHOLD,
    VOICE_VARIANCE_THRESHOLD,
    VOICE_SILENCE_RATIO_THRESHOLD,
    VOICE_PEAK_THRESHOLD,
    VOICE_STRESS_CAP,
)

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
    """Hardware unavailable — zero contribution to scorer."""
    return VoiceResult(
        avg_amplitude=0.0,
        peak_amplitude=0.0,
        amplitude_variance=0.0,
        silence_ratio=1.0,
        stress_score=0,
        stress_flags=[],
    )


def VoiceResult_disarmed():
    """Mic not armed — zero contribution (not an error state)."""
    return VoiceResult_empty()


def compute_voice_stress(
    avg_amp: float,
    peak_amp: float,
    variance: float,
    silence_ratio: float,
) -> tuple[int, list]:
    """All thresholds imported from scoring.py — single source of truth."""
    score = 0
    flags = []

    if avg_amp > VOICE_AVG_AMP_THRESHOLD:
        score += 10
        flags.append("ELEVATED AMBIENT STRESS SIGNAL")

    if variance > VOICE_VARIANCE_THRESHOLD:
        score += 8
        flags.append("ERRATIC ACOUSTIC SIGNATURE")

    if silence_ratio < VOICE_SILENCE_RATIO_THRESHOLD:
        score += 7
        flags.append("CONTINUOUS VOCALIZATION DETECTED")

    if peak_amp > VOICE_PEAK_THRESHOLD:
        score += 5
        flags.append("ACUTE STRESS SPIKE RECORDED")

    return min(VOICE_STRESS_CAP, score), flags


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
            with sd.InputStream(
                samplerate=self.sample_rate,
                channels=1,
                blocksize=self.chunk_size,
            ) as stream:
                while self.is_recording:
                    data, _ = stream.read(self.chunk_size)
                    amplitude = np.abs(data).mean()
                    with self.lock:
                        self.buffer.append(float(amplitude))
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
        """Stop live mic capture without scoring (DISARM)."""
        if not VOICE_AVAILABLE:
            return
        self.is_recording = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1.0)
        with self.lock:
            self.buffer = []

    def stop_recording(self, armed: bool = True) -> VoiceResult:
        if not VOICE_AVAILABLE or not armed:
            return VoiceResult_disarmed()

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

        stress_score, flags = compute_voice_stress(
            avg_amp, peak_amp, variance, silence_ratio
        )

        return VoiceResult(
            avg_amplitude=avg_amp,
            peak_amplitude=peak_amp,
            amplitude_variance=variance,
            silence_ratio=silence_ratio,
            stress_score=stress_score,
            stress_flags=flags,
        )

    def get_live_waveform(self, width: int) -> list:
        if not VOICE_AVAILABLE:
            return [0.0] * width

        with self.lock:
            data = list(self.buffer)

        if not data:
            return [0.0] * width

        if len(data) >= width:
            return data[-width:]
        return [0.0] * (width - len(data)) + data
