import os
import json
import logging

AI_AVAILABLE = False
try:
    import google.generativeai as genai
    # Or just use the standard API check
    if os.environ.get("GEMINI_API_KEY"):
        genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
        AI_AVAILABLE = True
except ImportError:
    pass

class AIAnalyst:
    def __init__(self):
        pass

    def analyze(self, answer: str, question: str, session_history: list) -> dict:
        def get_fallback():
            return {
                "ai_lie_score_delta": 0,
                "linguistic_flags": ["AI ANALYSIS UNAVAILABLE \u2014 RULE ENGINE ACTIVE"],
                "contradiction_detected": False,
                "contradiction_detail": None,
                "psychological_profile_note": "Insufficient data for AI profile.",
                "deception_technique": None
            }

        if not AI_AVAILABLE:
            return get_fallback()

        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            history_str = ""
            for item in session_history:
                prior_q = item.get("question", "")
                prior_a = item.get("answer", "")
                history_str += f"Q: {prior_q}\nA: {prior_a}\n\n"

            system_instruction = "You are a forensic behavioral linguist and deception analyst. You analyze text for psychological deception markers with clinical precision. You return only valid JSON, nothing else. No preamble, no explanation, no markdown fences."
            
            user_prompt = f"""INTERROGATION CONTEXT:
Question asked: {question}

Subject's answer: {answer}

Prior session answers for contradiction analysis:
{history_str}

Analyze this answer and return a JSON object with these exact keys:

{{
    "ai_lie_score_delta": <integer -20 to +40, how much to adjust the base lie score up or down based on linguistic analysis alone>,
    "linguistic_flags": [<list of strings, max 5, each a specific clinical observation about the language used. Be specific \u2014 reference actual words or phrases from the answer. Examples: "Passive voice construction in 'it happened' removes subject from agency", "Unprompted alibi volunteered before question was completed \u2014 pre-rehearsed response pattern", "Hedge cluster detected: 3 uncertainty markers within 12 words">],
    "contradiction_detected": <true or false>,
    "contradiction_detail": <null or string describing exactly which prior answer this contradicts and how>,
    "psychological_profile_note": <one sentence, clinical tone, describing what this answer reveals about the subject's psychological state or deception strategy>,
    "deception_technique": <null or one of: "OMISSION", "DEFLECTION", "MINIMIZATION", "FABRICATION", "MISDIRECTION", "DENIAL", "RATIONALIZATION", "TRUTH_MIXED_WITH_LIE">
}}"""

            # Trying to use JSON generation config if supported
            try:
                response = model.generate_content(
                    system_instruction + "\n\n" + user_prompt,
                    generation_config={"response_mime_type": "application/json"}
                )
                text = response.text.strip()
                if text.startswith("```json"):
                    text = text[7:]
                if text.endswith("```"):
                    text = text[:-3]
                return json.loads(text.strip())
            except Exception:
                # Fallback to standard prompt
                response = model.generate_content(system_instruction + "\n\n" + user_prompt)
                text = response.text.strip()
                if text.startswith("```json"):
                    text = text[7:]
                elif text.startswith("```"):
                    text = text[3:]
                if text.endswith("```"):
                    text = text[:-3]
                return json.loads(text.strip())
                
        except Exception as e:
            return get_fallback()

    def generate_final_profile(self, all_scores: list, all_answers: list) -> str:
        if not AI_AVAILABLE:
            return "BEHAVIORAL PROFILE UNAVAILABLE: PSYCH-ANALYSIS MODULE OFFLINE."

        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            session_data = ""
            for i, ans in enumerate(all_answers):
                session_data += f"Answer {i+1}: {ans}\n"
                
            prompt = f"""You are writing a classified forensic behavioral assessment.
Based on the following interrogation session data, write a 3-paragraph psychological profile of the subject.

Be specific \u2014 reference their actual words and phrases.
Use clinical language. Identify their dominant deception strategy if applicable. Comment on their emotional regulation patterns.
Do not use lists or headers. Pure prose. Max 200 words.

SESSION DATA:
{session_data}"""
            
            response = model.generate_content(prompt)
            return response.text.strip()
        except Exception:
            return "ERROR GENERATING FINAL PROFILE. PSYCH-ANALYSIS MODULE FAILED."
