"""
scoring.py — POLYTRUTH v5.0
Additive lie-probability scorer from AnalysisResult metrics + lexical traps.
Binary verdict only: TRUTHFUL or DECEPTIVE (no inconclusive band).
"""

from analyzer import AnalysisResult
from typing import Dict, Any, List

# ── Published thresholds (aligned with deception-literature heuristics) ──
VERDICT_THRESHOLD = 50          # score <= 50 → TRUTHFUL; score > 50 → DECEPTIVE
BASE_SCORE = 15                 # neutral starting points before signal accumulation
COGNITIVE_DELAY_HIGH_SEC = 6.0  # extended pre-response load (literature: pause ↑ under fabrication)
COGNITIVE_DELAY_MED_SEC = 4.0
COGNITIVE_DELAY_LOW_SEC = 2.0
WPM_FAST = 80                   # rehearsed / rapid script
WPM_SLOW = 15                   # motor hesitation
BURST_VOLATILITY_HIGH = 0.8     # high inter-key variance → editing under load
BURST_VOLATILITY_MED = 0.5
BACKSPACE_HIGH = 8
BACKSPACE_MED = 4
MIN_WORDS_EVASIVE = 20


class LieScorer:
    """
    Converts an AnalysisResult into a structured score dict.
    All scoring is additive from a base score; clamped to [0, 100].
    """

    # ── Lexical trap word-lists ──────────────────────────────
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

    def score(self, result: AnalysisResult) -> Dict[str, Any]:
        pts = BASE_SCORE
        flags: List[str] = []
        answer_lower = result.answer.lower()

        # ── Cognitive delay ──────────────────────────────────
        if result.cognitive_delay > COGNITIVE_DELAY_HIGH_SEC:
            pts += 25
            flags.append("EXTENDED PRE-RESPONSE COGNITIVE LOAD DETECTED")
        elif result.cognitive_delay >= COGNITIVE_DELAY_MED_SEC:
            pts += 15
            flags.append("ELEVATED NARRATIVE FABRICATION LATENCY")
        elif result.cognitive_delay >= COGNITIVE_DELAY_LOW_SEC:
            pts += 5
            flags.append("ELEVATED RESPONSE LATENCY")
        elif result.cognitive_delay < 1:
            pts += 5
            flags.append("ABNORMALLY FAST RESPONSE ONSET")

        # ── WPM ─────────────────────────────────────────────
        if result.wpm > WPM_FAST:
            pts += 10
            flags.append("ANOMALOUS TYPING VELOCITY - REHEARSED SCRIPT")
        elif 0 < result.wpm < WPM_SLOW:
            pts += 8
            flags.append("SEVERE MOTOR HESITATION PATTERN")

        # ── Burst volatility ─────────────────────────────────
        if result.burst_volatility > BURST_VOLATILITY_HIGH:
            pts += 20
            flags.append("HIGH KEYSTROKE VARIANCE - ACTIVE STORY EDITING")
        elif result.burst_volatility > BURST_VOLATILITY_MED:
            pts += 10
            flags.append("MODERATE EDITING BEHAVIOUR DETECTED")

        # ── Backspaces ───────────────────────────────────────
        if result.backspace_count > BACKSPACE_HIGH:
            pts += 15
            flags.append("EXCESSIVE CORRECTION ACTIVITY")
        elif result.backspace_count > BACKSPACE_MED:
            pts += 8
            flags.append("NOTABLE SELF-CENSORSHIP DETECTED")

        # ── Word count ───────────────────────────────────────
        if result.word_count < MIN_WORDS_EVASIVE:
            pts += 12
            flags.append("EVASIVE RESPONSE - NARRATIVE AVOIDANCE")

        # ── Uncertainty markers (each hit is explicit) ───────
        for word in self.UNCERTAINTY_WORDS:
            if word in answer_lower:
                pts += 6
                flags.append(f"UNCERTAINTY MARKER: '{word}'")

        # ── Distancing language ──────────────────────────────
        for phrase in self.DISTANCING_PHRASES:
            if phrase in answer_lower:
                pts += 7
                flags.append(f"PSYCHOLOGICAL DISTANCING: '{phrase}'")

        # ── Over-justification ───────────────────────────────
        oj_count = sum(answer_lower.count(w) for w in self.OVER_JUSTIFICATION_WORDS)
        if oj_count > 3:
            pts += 10
            flags.append("OVER-JUSTIFICATION PATTERN ACTIVE")

        lie_probability = max(0, min(100, pts))
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
        contradiction: Any
    ) -> dict:
        base_score = self.score(result)
        pts = base_score["lie_probability"]
        
        # AI analysis delta
        ai_delta = max(-15, min(35, ai_analysis.get("ai_lie_score_delta", 0)))
        pts += ai_delta
        
        # Voice stress
        pts += voice_result.stress_score
        
        # Face tracking
        pts += face_stats.face_score
        
        # Contradiction penalty
        if contradiction.detected:
            sev = {"LOW": 8, "MEDIUM": 18, "HIGH": 30}
            pts += sev.get(contradiction.severity, 8)
            
        final_score = max(0, min(100, pts))
        
        all_flags = (
            base_score["flags"] +
            ai_analysis.get("linguistic_flags", []) +
            voice_result.stress_flags +
            face_stats.face_flags
        )
        if contradiction.detected:
            all_flags.append(
                f"CONTRADICTION DETECTED: {contradiction.contradiction_type} \u2014 "
                f"SEVERITY: {contradiction.severity}"
            )
            
        verdict = self.verdict_from_score(final_score)

        sources_active = sum([
            bool(ai_analysis.get("ai_lie_score_delta", 0) != 0),
            voice_result.avg_amplitude > 0,
            face_stats.face_detected,
            len(base_score["flags"]) > 0,
        ])
        confidence = "HIGH" if sources_active >= 2 else "LOW"
                     
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
                "voice_stress": voice_result.stress_score,
                "face_tracking": face_stats.face_score,
            }
        }
