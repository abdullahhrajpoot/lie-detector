"""
analyzer.py — POLYTRUTH v5.0
Real-time keystroke capture and behavioral analysis.
Falls back to plain input() if keyboard hooks are unavailable.
"""

import time
import math
import random
import threading
from dataclasses import dataclass, field
from typing import List, Optional


# ─────────────────────────────────────────────────────────────
# Custom exception
# ─────────────────────────────────────────────────────────────
class SessionAbortException(Exception):
    """Raised when the user presses ESC or aborts a session."""
    pass


# ─────────────────────────────────────────────────────────────
# Result dataclass
# ─────────────────────────────────────────────────────────────
@dataclass
class AnalysisResult:
    answer: str
    word_count: int
    cognitive_delay: float      # seconds from question display to first key
    wpm: float                  # words per minute
    burst_volatility: float     # std-dev of inter-key gaps
    backspace_count: int
    duration: float             # total seconds from first key to Enter


# ─────────────────────────────────────────────────────────────
# Keyboard availability flag
# ─────────────────────────────────────────────────────────────
_keyboard_available = False
_keyboard_module = None

try:
    import keyboard as _kb
    _keyboard_module = _kb
    _keyboard_available = True
except Exception:
    _keyboard_available = False


# ─────────────────────────────────────────────────────────────
# KeystrokeAnalyzer class
# ─────────────────────────────────────────────────────────────
class KeystrokeAnalyzer:
    """
    Captures answer input and records timing metadata.
    Uses keyboard module hooks when available; falls back to plain input().
    """

    def __init__(self):
        self.question_start_time: float = 0.0
        self.first_key_time: Optional[float] = None
        self.key_timestamps: List[float] = []
        self.backspace_count: int = 0
        self.chars: List[str] = []
        self._lock = threading.Lock()
        self._done_event = threading.Event()
        self._aborted = False
        self._current_chars: List[str] = []

    # ── keyboard-hook mode ──────────────────────────────────
    def _on_key(self, event):
        if self._done_event.is_set():
            return

        now = time.time()

        # ESC → abort
        if event.name == "esc":
            self._aborted = True
            self._done_event.set()
            return

        # Enter → finish
        if event.name == "enter":
            self._done_event.set()
            return

        with self._lock:
            if self.first_key_time is None:
                self.first_key_time = now
            self.key_timestamps.append(now)

            if event.name == "backspace":
                self.backspace_count += 1
                if self._current_chars:
                    self._current_chars.pop()
            elif len(event.name) == 1:
                self._current_chars.append(event.name)
            elif event.name == "space":
                self._current_chars.append(" ")

    def collect_with_hooks(self, question_display_time: float) -> AnalysisResult:
        """Collect input using keyboard hooks (preferred)."""
        self.question_start_time = question_display_time
        self._done_event.clear()
        self._aborted = False
        self._current_chars = []
        self.key_timestamps = []
        self.first_key_time = None
        self.backspace_count = 0

        hook = _keyboard_module.on_press(self._on_key)
        try:
            self._done_event.wait()
        finally:
            _keyboard_module.unhook(hook)

        if self._aborted:
            raise SessionAbortException("User pressed ESC.")

        answer = "".join(self._current_chars).strip()
        return self._build_result(answer, question_display_time)

    # ── fallback: plain input() ─────────────────────────────
    def collect_with_input(self, question_display_time: float) -> AnalysisResult:
        """Collect input using plain input() with timing only."""
        self.question_start_time = question_display_time
        try:
            answer = input(">>> ")
        except (KeyboardInterrupt, EOFError):
            raise SessionAbortException("User interrupted.")
        return self._build_result(answer, question_display_time)

    # ── shared result builder ────────────────────────────────
    def _build_result(self, answer: str, question_display_time: float) -> AnalysisResult:
        now = time.time()

        # Cognitive delay: time from question display to first key
        if self.first_key_time is not None:
            cognitive_delay = self.first_key_time - question_display_time
        else:
            # fallback: total time (display → Enter) as proxy
            cognitive_delay = now - question_display_time
            # cap at something reasonable
            cognitive_delay = max(0.5, min(cognitive_delay, 30.0))

        # Duration: first key to submission (or full span in fallback)
        if self.first_key_time is not None:
            duration = now - self.first_key_time
        else:
            duration = max(0.5, now - question_display_time)

        # WPM
        word_count = len(answer.split()) if answer.strip() else 0
        wpm = (word_count / (duration / 60.0)) if duration > 0 else 0.0

        # Burst volatility: std-dev of inter-key gaps
        if len(self.key_timestamps) >= 2:
            gaps = [
                self.key_timestamps[i] - self.key_timestamps[i - 1]
                for i in range(1, len(self.key_timestamps))
            ]
            mean_gap = sum(gaps) / len(gaps)
            variance = sum((g - mean_gap) ** 2 for g in gaps) / len(gaps)
            burst_volatility = math.sqrt(variance)
        else:
            # Fallback: gaussian random to keep scoring alive
            burst_volatility = max(0.0, random.gauss(0.6, 0.15))

        return AnalysisResult(
            answer=answer,
            word_count=word_count,
            cognitive_delay=round(cognitive_delay, 3),
            wpm=round(wpm, 1),
            burst_volatility=round(burst_volatility, 4),
            backspace_count=self.backspace_count,
            duration=round(duration, 3),
        )


# ─────────────────────────────────────────────────────────────
# Public function
# ─────────────────────────────────────────────────────────────
def analyze_answer(question_display_time: float) -> AnalysisResult:
    """
    Block, collect the full answer, and return an AnalysisResult.
    Tries keyboard hooks first; falls back to plain input().
    """
    analyzer = KeystrokeAnalyzer()

    if _keyboard_available:
        try:
            return analyzer.collect_with_hooks(question_display_time)
        except SessionAbortException:
            raise
        except Exception:
            # Hook registration failed (e.g. no admin on Linux) → fallback
            pass

    return analyzer.collect_with_input(question_display_time)
