"""
scoring.py — POLYTRUTH v5.0
SINGLE SOURCE OF TRUTH for all lie-probability thresholds and verdict policy.

Rule-based + heuristic demonstration system — not a validated forensic instrument.
Thresholds are heuristically inspired by published deception literature; they are
NOT calibrated on an external labeled corpus in this repository.

Binary verdict only: TRUTHFUL (<= VERDICT_THRESHOLD) or DECEPTIVE (> VERDICT_THRESHOLD).
No INCONCLUSIVE band.
"""

from analyzer import AnalysisResult
from typing import Dict, Any, List

# ── Verdict & session ─────────────────────────────────────────────────────────
VERDICT_THRESHOLD = 50
BASE_SCORE = 15
MIN_ANSWER_WORDS = 15  # validation gate (web + CLI); not the evasive-content penalty

# ── Keystroke / timing (Banerjee EMNLP 2014; Monaro Sci Rep 2018; Tomas ACP 2021) ─
COGNITIVE_DELAY_HIGH_SEC = 6.0
COGNITIVE_DELAY_MED_SEC = 4.0
COGNITIVE_DELAY_LOW_SEC = 2.0
COGNITIVE_DELAY_FAST_SEC = 1.0
WPM_FAST = 80
WPM_SLOW = 15
BURST_VOLATILITY_HIGH = 0.8
BURST_VOLATILITY_MED = 0.5
BACKSPACE_HIGH = 8
BACKSPACE_MED = 4
MIN_WORDS_EVASIVE = 20

# ── Lexical (DePaulo 2003; Hauch meta-analysis 2015 — rule approximations only) ─
UNCERTAINTY_POINTS = 6
DISTANCING_POINTS = 7
OVER_JUSTIFICATION_MIN_COUNT = 3
OVER_JUSTIFICATION_POINTS = 10

# ── AI overlay (Pérez-Rosas Sci Rep 2023 — additive only) ─────────────────────
AI_DELTA_MIN = -15
AI_DELTA_MAX = 35

# ── Voice (Fatma 2024 MFCC/LSTM cited in docs; coarse amplitude heuristics here) ─
# LIMITATION: not MFCC/F0 pipeline; commercial VSA often near chance — demonstrative only.
VOICE_AVG_AMP_THRESHOLD = 0.4
VOICE_VARIANCE_THRESHOLD = 0.15
VOICE_SILENCE_RATIO_THRESHOLD = 0.3
VOICE_PEAK_THRESHOLD = 0.8
VOICE_STRESS_CAP = 30

# ── Face (Gallardo-Antolín MDPI 2021 multimodal context) ─────────────────────
# LIMITATION: gaze aversion is a weak cue (DePaulo 2003); not pupilometry.
FACE_LOOK_AWAY_HIGH = 3
FACE_LOOK_AWAY_MED = 1
FACE_POSITION_VAR_THRESHOLD = 0.08
FACE_STRESS_CAP = 25

# ── Contradiction (Vrij & Granhag 2012; Buller & Burgoon 1996 IDT) ───────────
CONTRADICTION_POINTS = {"LOW": 8, "MEDIUM": 18, "HIGH": 30}

# ── Confidence ───────────────────────────────────────────────────────────────
CONFIDENCE_HIGH_MIN_SOURCES = 2


class LieScorer:
    """
    Converts an AnalysisResult into a structured score dict.
    All scoring is additive from BASE_SCORE; final clamped [0, 100].
    """

    UNCERTAINTY_WORDS = [
        "maybe", "probably", "i think", "i guess", "sort of",
        "kind of", "more or less", "to be honest", "honestly",
        "i believe", "if i recall", "i'm not sure",
    ]

    DISTANCING_PHRASES = [
        "that person", "the situation", "those people",
        "someone", "they just", "it happened", "at that point",
    ]

    OVER_JUSTIFICATION_WORDS = [
        "because", "since", "therefore", "that's why",
        "the reason", "which is why", "due to",
    ]

    @staticmethod
    def verdict_from_score(lie_probability: int) -> str:
        return "TRUTHFUL" if lie_probability <= VERDICT_THRESHOLD else "DECEPTIVE"

    @staticmethod
    def clamp_score(raw: int) -> int:
        return max(0, min(100, int(raw)))

    @staticmethod
    def clamp_ai_delta(delta) -> int:
        try:
            d = int(delta)
        except (TypeError, ValueError):
            d = 0
        return max(AI_DELTA_MIN, min(AI_DELTA_MAX, d))

    def score(self, result: AnalysisResult) -> Dict[str, Any]:
        pts = BASE_SCORE
        flags: List[str] = []
        answer_lower = result.answer.lower()

        if result.cognitive_delay > COGNITIVE_DELAY_HIGH_SEC:
            pts += 25
            flags.append("EXTENDED PRE-RESPONSE COGNITIVE LOAD DETECTED")
        elif result.cognitive_delay >= COGNITIVE_DELAY_MED_SEC:
            pts += 15
            flags.append("ELEVATED NARRATIVE FABRICATION LATENCY")
        elif result.cognitive_delay >= COGNITIVE_DELAY_LOW_SEC:
            pts += 5
            flags.append("ELEVATED RESPONSE LATENCY")
        elif result.cognitive_delay < COGNITIVE_DELAY_FAST_SEC:
            pts += 5
            flags.append("ABNORMALLY FAST RESPONSE ONSET")

        if result.wpm > WPM_FAST:
            pts += 10
            flags.append("ANOMALOUS TYPING VELOCITY - REHEARSED SCRIPT")
        elif 0 < result.wpm < WPM_SLOW:
            pts += 8
            flags.append("SEVERE MOTOR HESITATION PATTERN")

        if result.burst_volatility > BURST_VOLATILITY_HIGH:
            pts += 20
            flags.append("HIGH KEYSTROKE VARIANCE - ACTIVE STORY EDITING")
        elif result.burst_volatility > BURST_VOLATILITY_MED:
            pts += 10
            flags.append("MODERATE EDITING BEHAVIOUR DETECTED")

        if result.backspace_count > BACKSPACE_HIGH:
            pts += 15
            flags.append("EXCESSIVE CORRECTION ACTIVITY")
        elif result.backspace_count > BACKSPACE_MED:
            pts += 8
            flags.append("NOTABLE SELF-CENSORSHIP DETECTED")

        if result.word_count < MIN_WORDS_EVASIVE:
            pts += 12
            flags.append("EVASIVE RESPONSE - NARRATIVE AVOIDANCE")

        for word in self.UNCERTAINTY_WORDS:
            if word in answer_lower:
                pts += UNCERTAINTY_POINTS
                flags.append(f"UNCERTAINTY MARKER: '{word}'")

        for phrase in self.DISTANCING_PHRASES:
            if phrase in answer_lower:
                pts += DISTANCING_POINTS
                flags.append(f"PSYCHOLOGICAL DISTANCING: '{phrase}'")

        oj_count = sum(answer_lower.count(w) for w in self.OVER_JUSTIFICATION_WORDS)
        if oj_count > OVER_JUSTIFICATION_MIN_COUNT:
            pts += OVER_JUSTIFICATION_POINTS
            flags.append("OVER-JUSTIFICATION PATTERN ACTIVE")

        lie_probability = self.clamp_score(pts)
        verdict = self.verdict_from_score(lie_probability)
        confidence = "HIGH" if len(flags) >= 2 else "LOW"

        return {
            "lie_probability": lie_probability,
            "confidence": confidence,
            "flags": flags,
            "verdict": verdict,
        }

    def score_multimodal(
        self,
        result: AnalysisResult,
        ai_analysis: dict,
        voice_result: Any,
        face_stats: Any,
        contradiction: Any,
    ) -> dict:
        base_score = self.score(result)
        pts = base_score["lie_probability"]

        ai_delta = self.clamp_ai_delta(ai_analysis.get("ai_lie_score_delta", 0))
        pts += ai_delta
        pts += int(getattr(voice_result, "stress_score", 0) or 0)
        pts += int(getattr(face_stats, "face_score", 0) or 0)

        if getattr(contradiction, "detected", False):
            sev = getattr(contradiction, "severity", "LOW")
            pts += CONTRADICTION_POINTS.get(sev, CONTRADICTION_POINTS["LOW"])

        final_score = self.clamp_score(pts)

        all_flags = (
            base_score["flags"]
            + list(ai_analysis.get("linguistic_flags", []) or [])
            + list(getattr(voice_result, "stress_flags", []) or [])
            + list(getattr(face_stats, "face_flags", []) or [])
        )
        if getattr(contradiction, "detected", False):
            all_flags.append(
                f"CONTRADICTION DETECTED: {contradiction.contradiction_type} — "
                f"SEVERITY: {contradiction.severity}"
            )

        verdict = self.verdict_from_score(final_score)

        sources_active = sum([
            ai_delta != 0,
            float(getattr(voice_result, "avg_amplitude", 0) or 0) > 0,
            bool(getattr(face_stats, "face_detected", False)),
            len(base_score["flags"]) > 0,
        ])
        confidence = (
            "HIGH" if sources_active >= CONFIDENCE_HIGH_MIN_SOURCES else "LOW"
        )

        return {
            "lie_probability": final_score,
            "confidence": confidence,
            "flags": all_flags,
            "verdict": verdict,
            "ai_profile_note": ai_analysis.get("psychological_profile_note"),
            "deception_technique": ai_analysis.get("deception_technique"),
            "contradiction": contradiction,
            "source_breakdown": {
                "rule_based": base_score["lie_probability"],
                "ai_delta": ai_delta,
                "voice_stress": int(getattr(voice_result, "stress_score", 0) or 0),
                "face_tracking": int(getattr(face_stats, "face_score", 0) or 0),
            },
        }
