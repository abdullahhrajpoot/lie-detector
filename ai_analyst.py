"""
ai_analyst.py — POLYTRUTH v5.0
Optional Gemini linguistic overlay — additive delta only; never replaces LieScorer.

Grounded in: Pérez-Rosas et al. (2023) Sci Rep; Adkins et al. (2025) Frontiers in AI.
If API unavailable, delta=0 and rule engine is authoritative.
"""

import os
import json

from scoring import AI_DELTA_MIN, AI_DELTA_MAX, LieScorer

AI_AVAILABLE = False
try:
    import google.generativeai as genai
    if os.environ.get("GEMINI_API_KEY"):
        genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
        AI_AVAILABLE = True
except ImportError:
    pass


def _safe_fallback():
    return {
        "ai_lie_score_delta": 0,
        "linguistic_flags": ["AI ANALYSIS UNAVAILABLE — RULE ENGINE ACTIVE"],
        "contradiction_detected": False,
        "contradiction_detail": None,
        "psychological_profile_note": "AI unavailable.",
        "deception_technique": None,
        "technique_tag": "rule_only",
    }


class AIAnalyst:
    def __init__(self):
        pass

    def analyze(self, answer: str, question: str, session_history: list) -> dict:
        if not AI_AVAILABLE:
            return _safe_fallback()

        try:
            model = genai.GenerativeModel("gemini-1.5-flash")

            history_str = ""
            for item in session_history:
                prior_q = item.get("question", "")
                prior_a = item.get("answer", "")
                history_str += f"Q: {prior_q}\nA: {prior_a}\n\n"

            system_instruction = (
                "You are a forensic behavioral linguist. Return only valid JSON."
            )

            user_prompt = f"""INTERROGATION CONTEXT:
Question asked: {question}

Subject's answer: {answer}

Prior session answers:
{history_str}

Return JSON with keys:
{{
    "ai_lie_score_delta": <integer -20 to +40>,
    "linguistic_flags": [<max 5 strings>],
    "contradiction_detected": <bool>,
    "contradiction_detail": <null or string>,
    "psychological_profile_note": <one sentence>,
    "deception_technique": <null or OMISSION|DEFLECTION|MINIMIZATION|FABRICATION|MISDIRECTION|DENIAL|RATIONALIZATION|TRUTH_MIXED_WITH_LIE>
}}"""

            try:
                response = model.generate_content(
                    system_instruction + "\n\n" + user_prompt,
                    generation_config={"response_mime_type": "application/json"},
                )
                text = response.text.strip()
            except Exception:
                response = model.generate_content(
                    system_instruction + "\n\n" + user_prompt
                )
                text = response.text.strip()

            if text.startswith("```json"):
                text = text[7:]
            elif text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]

            parsed = json.loads(text.strip())
            parsed["ai_lie_score_delta"] = LieScorer.clamp_ai_delta(
                parsed.get("ai_lie_score_delta", 0)
            )
            parsed["technique_tag"] = parsed.get("deception_technique") or "ai"
            return parsed

        except Exception:
            return _safe_fallback()

    def generate_final_profile(self, all_scores: list, all_answers: list) -> str:
        if not AI_AVAILABLE:
            return "BEHAVIORAL PROFILE UNAVAILABLE: PSYCH-ANALYSIS MODULE OFFLINE."

        try:
            model = genai.GenerativeModel("gemini-1.5-flash")

            session_data = ""
            for i, ans in enumerate(all_answers):
                session_data += f"Answer {i+1}: {ans}\n"

            prompt = f"""Write a forensic behavioral assessment (max 200 words, prose only).
SESSION DATA:
{session_data}"""

            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception:
            return "ERROR GENERATING FINAL PROFILE. PSYCH-ANALYSIS MODULE FAILED."
