"""
scoring.py — POLYTRUTH v5.0
Additive lie-probability scorer from AnalysisResult metrics + lexical traps.
"""

from analyzer import AnalysisResult
from typing import Dict, Any, List


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

    def score(self, result: AnalysisResult) -> Dict[str, Any]:
        pts = 15
        flags: List[str] = []
        answer_lower = result.answer.lower()

        # ── Cognitive delay ──────────────────────────────────
        if result.cognitive_delay > 6:
            pts += 25
            flags.append("EXTENDED PRE-RESPONSE COGNITIVE LOAD DETECTED")
        elif result.cognitive_delay >= 4:
            pts += 15
            flags.append("ELEVATED NARRATIVE FABRICATION LATENCY")
        elif result.cognitive_delay >= 2:
            pts += 5
        elif result.cognitive_delay < 1:
            pts -= 5  # unusually fast = possibly rehearsed (but not suspicious by itself)

        # ── WPM ─────────────────────────────────────────────
        if result.wpm > 80:
            pts += 10
            flags.append("ANOMALOUS TYPING VELOCITY - REHEARSED SCRIPT?")
        elif result.wpm < 15 and result.wpm > 0:
            pts += 8
            flags.append("SEVERE MOTOR HESITATION PATTERN")

        # ── Burst volatility ─────────────────────────────────
        if result.burst_volatility > 0.8:
            pts += 20
            flags.append("HIGH KEYSTROKE VARIANCE - ACTIVE STORY EDITING")
        elif result.burst_volatility > 0.5:
            pts += 10
            flags.append("MODERATE EDITING BEHAVIOUR DETECTED")

        # ── Backspaces ───────────────────────────────────────
        if result.backspace_count > 8:
            pts += 15
            flags.append("EXCESSIVE CORRECTION ACTIVITY")
        elif result.backspace_count > 4:
            pts += 8
            flags.append("NOTABLE SELF-CENSORSHIP DETECTED")

        # ── Word count ───────────────────────────────────────
        if result.word_count < 20:
            pts += 12
            flags.append("EVASIVE RESPONSE - NARRATIVE AVOIDANCE")
        elif result.word_count > 80:
            pts -= 8  # verbose answers are less likely deceptive

        # ── Uncertainty markers ──────────────────────────────
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

        # ── Clamp ────────────────────────────────────────────
        lie_probability = max(0, min(100, pts))

        # ── Verdict ──────────────────────────────────────────
        if lie_probability <= 35:
            verdict = "TRUTHFUL"
        elif lie_probability <= 60:
            verdict = "INCONCLUSIVE"
        else:
            verdict = "DECEPTIVE"

        # ── Confidence ───────────────────────────────────────
        if len(flags) >= 4:
            confidence = "HIGH"
        elif len(flags) >= 2:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"

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
            
        verdict = "TRUTHFUL" if final_score <= 35 else \
                  "INCONCLUSIVE" if final_score <= 60 else "DECEPTIVE"
                  
        sources_active = sum([
            bool(ai_analysis.get("ai_lie_score_delta") != 0),
            voice_result.avg_amplitude > 0,
            face_stats.face_detected,
            len(base_score["flags"]) > 0
        ])
        confidence = "HIGH" if sources_active >= 3 else \
                     "MEDIUM" if sources_active >= 2 else "LOW"
                     
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
