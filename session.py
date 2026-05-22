"""
session.py \u2014 POLYTRUTH v5.0
Game-loop logic for all 4 interrogation modes.
"""

import random
import time
from typing import List, Optional

import ui
from analyzer import analyze_answer, SessionAbortException, AnalysisResult
from questions import QUESTION_BANK, FOLLOWUP_DECEPTIVE, FOLLOWUP_TRUTHFUL, USED_QUESTIONS
from scoring import LieScorer, is_gibberish_answer

from ai_analyst import AIAnalyst, AI_AVAILABLE
from voice_analyzer import VoiceAnalyzer, VOICE_AVAILABLE, VoiceResult_empty
from face_tracker import FaceTracker, FACE_AVAILABLE, FaceStats_empty
from contradiction_engine import ContradictionEngine

_ai = AIAnalyst()
_voice = VoiceAnalyzer()
_face = FaceTracker()
_contradiction = ContradictionEngine()

# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
# Helpers
# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
def _pick_question(pool: List[str], used: set) -> Optional[str]:
    available = [q for q in pool if q not in used]
    if not available:
        return None
    chosen = random.choice(available)
    used.add(chosen)
    return chosen


def _run_single_question(question: str, scorer: LieScorer) -> dict:
    ui.stop_dashboard()
    
    if VOICE_AVAILABLE:
        _voice.start_recording()
    
    q_display_time = time.time()
    ui.show_question(question)
    
    try:
        result = analyze_answer(q_display_time)
    except SessionAbortException:
        if VOICE_AVAILABLE:
            _voice.stop_recording()
        raise

    if is_gibberish_answer(result.answer):
        if VOICE_AVAILABLE:
            _voice.stop_recording()
        ui.show_analysis_progress("VALIDATING RESPONSE INTEGRITY...")
        time.sleep(0.4)
        ui.stop_dashboard()
        from rich.console import Console
        Console().print(
            "\n  [bold red]INPUT FLAGGED:[/] Gibberish / non-narrative text detected. "
            "Re-answer with a coherent 15+ word response.\n"
        )
        ui.start_dashboard(ui._session_state)
        return _run_single_question(question, scorer)
    
    voice_result = _voice.stop_recording() if VOICE_AVAILABLE else VoiceResult_empty()
    face_stats = _face.get_current_stats() if FACE_AVAILABLE else FaceStats_empty()
    
    contradiction = _contradiction.check_contradiction(result.answer)
    
    ui.show_analysis_progress("RUNNING FORENSIC LINGUISTIC ANALYSIS...")
    session_history = _contradiction.get_timeline()
    ai_analysis = _ai.analyze(result.answer, question, session_history)
    
    if ai_analysis.get("linguistic_flags"):
        ui.update_session_state("latest_ai_flags", ai_analysis["linguistic_flags"])
    
    score = scorer.score_multimodal(
        result, ai_analysis, voice_result, face_stats, contradiction
    )
    score["question"] = question
    score["result"] = result
    
    _contradiction.add_answer(question, result.answer, score)
    
    if contradiction.detected:
        ui.update_session_state("contradiction_alert", {
            "prior": contradiction.prior_question,
            "type": contradiction.contradiction_type,
            "severity": contradiction.severity
        })
        
    ui.show_result(score)
    
    ui.update_session_state("contradiction_alert", None)
    
    ui.start_dashboard(ui._session_state)
    return score


def _build_behavioral_summary(scores: List[dict]) -> str:
    if not scores:
        return "Insufficient data for behavioral profile."

    avg = sum(s["lie_probability"] for s in scores) / len(scores)
    dec_count = sum(1 for s in scores if s["verdict"] == "DECEPTIVE")
    tru_count = sum(1 for s in scores if s["verdict"] == "TRUTHFUL")

    all_flags = []
    for s in scores:
        all_flags.extend(s.get("flags", []))

    flag_summary = ""
    if all_flags:
        from collections import Counter
        flag_cats = Counter(f.split(":")[0].split("\u2014")[0].strip() for f in all_flags)
        top_flag, freq = flag_cats.most_common(1)[0]
        flag_summary = f" Dominant behavioral marker: {top_flag} (appeared {freq}x)."

    from scoring import VERDICT_THRESHOLD
    if avg > VERDICT_THRESHOLD:
        profile = (
            f"Subject exceeded deception threshold (avg {avg:.0f}%). "
            f"{dec_count} of {len(scores)} responses classified DECEPTIVE.{flag_summary}"
        )
    else:
        profile = (
            f"Subject behavioral profile appears consistent with truthful disclosure. "
            f"Average lie probability: {avg:.0f}%. "
            f"{tru_count} of {len(scores)} responses were classified TRUTHFUL.{flag_summary}"
        )
    return profile


def _build_report(scores: List[dict], mode_label: str = "") -> dict:
    if not scores:
        return {
            "total_questions": 0,
            "avg_lie_probability": 0.0,
            "max_lie_probability": 0,
            "deceptive_count": 0,
            "truthful_count": 0,
            "inconclusive_count": 0,
            "most_suspicious_answer": None,
            "behavioral_summary": "No data.",
            "overall_verdict": "SUBJECT CLEARED",
            "timeline": []
        }

    avg = sum(s["lie_probability"] for s in scores) / len(scores)
    max_score = max(scores, key=lambda s: s["lie_probability"])
    dec = sum(1 for s in scores if s["verdict"] == "DECEPTIVE")
    tru = sum(1 for s in scores if s["verdict"] == "TRUTHFUL")
    from scoring import VERDICT_THRESHOLD
    if avg > VERDICT_THRESHOLD or dec > 0:
        overall = "SUBJECT FLAGGED"
    else:
        overall = "SUBJECT CLEARED"

    # AI overwrite for profile if available
    ai_profile = _ai.generate_final_profile(
        scores, 
        [item["answer"] for item in _contradiction.get_timeline()]
    )
    if not ai_profile or "UNAVAILABLE" in ai_profile or "ERROR" in ai_profile:
        ai_profile = _build_behavioral_summary(scores)

    return {
        "total_questions": len(scores),
        "avg_lie_probability": round(avg, 1),
        "max_lie_probability": max_score["lie_probability"],
        "deceptive_count": dec,
        "truthful_count": tru,
        "inconclusive_count": 0,
        "most_suspicious_answer": {"question": max_score.get("question", ""), "score": max_score},
        "behavioral_summary": ai_profile,
        "overall_verdict": overall,
        "timeline": _contradiction.get_timeline()
    }


# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
# Session class
# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
class Session:
    def __init__(self, mode: int):
        self.mode = mode
        self.scorer = LieScorer()
        self.scores: List[dict] = []
        _contradiction.timeline = []

        # Start dynamic updaters
        self._update_thread = None
        self._updater_running = False

    def _ui_data_updater(self):
        while self._updater_running:
            if VOICE_AVAILABLE:
                ui.update_voice_data(_voice)
            if FACE_AVAILABLE:
                ui.update_face_data(_face.get_current_stats())
            time.sleep(0.1)

    def run(self) -> dict:
        if FACE_AVAILABLE:
            _face.start()
            
        self._updater_running = True
        self._update_thread = threading.Thread(target=self._ui_data_updater, daemon=True)
        self._update_thread.start()
        
        try:
            if self.mode == 1:
                return self._run_honesty_test()
            elif self.mode == 2:
                return self._run_interrogation()
            elif self.mode == 3:
                return self._run_friend_test()
            elif self.mode == 4:
                return self._run_single()
            else:
                return {}
        finally:
            self._updater_running = False
            if FACE_AVAILABLE:
                _face.stop()
            if self._update_thread:
                self._update_thread.join(timeout=1.0)

    # \u2500\u2500 Mode 1: Honesty Test \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    def _run_honesty_test(self) -> dict:
        ui.update_session_state("mode", 1)
        ui.update_session_state("status", "HONESTY TEST ACTIVE")

        for i in range(6):
            q = _pick_question(QUESTION_BANK, USED_QUESTIONS)
            if not q:
                break
            try:
                score = _run_single_question(q, self.scorer)
                self.scores.append(score)
                self._update_state_from_score(score)
            except SessionAbortException:
                break

        report = _build_report(self.scores)
        ui.stop_dashboard()
        ui.show_final_report(report)
        input("\n  [Press ENTER to return to menu]")
        return report

    # \u2500\u2500 Mode 2: Interrogation \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    def _run_interrogation(self) -> dict:
        ui.update_session_state("mode", 2)
        ui.update_session_state("status", "INTERROGATION ACTIVE")

        followup_count = 0

        for i in range(3):
            q = _pick_question(QUESTION_BANK, USED_QUESTIONS)
            if not q:
                break
            try:
                score = _run_single_question(q, self.scorer)
                self.scores.append(score)
                self._update_state_from_score(score)

                if score["verdict"] == "DECEPTIVE" and followup_count < 2:
                    fu_q = _pick_question(FOLLOWUP_DECEPTIVE, USED_QUESTIONS)
                    if fu_q:
                        fu_score = _run_single_question(fu_q, self.scorer)
                        self.scores.append(fu_score)
                        self._update_state_from_score(fu_score)
                        followup_count += 1
                elif score["verdict"] == "TRUTHFUL" and followup_count < 2:
                    fu_q = _pick_question(FOLLOWUP_TRUTHFUL, USED_QUESTIONS)
                    if fu_q:
                        fu_score = _run_single_question(fu_q, self.scorer)
                        self.scores.append(fu_score)
                        self._update_state_from_score(fu_score)
                        followup_count += 1

            except SessionAbortException:
                break

        report = _build_report(self.scores)
        ui.stop_dashboard()
        ui.show_final_report(report)
        input("\n  [Press ENTER to return to menu]")
        return report

    # \u2500\u2500 Mode 3: Friend Test \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    def _run_friend_test(self) -> dict:
        ui.update_session_state("mode", 3)
        ui.update_session_state("status", "FRIEND TEST ACTIVE")

        ui.stop_dashboard()

        from rich.console import Console
        con = Console()
        con.clear()
        con.print()
        con.rule("[bold cyan]◈ OPERATOR INPUT \u2014 UNMONITORED ◈[/]", style="cyan")
        con.print()
        con.print(
            "[dim cyan]OPERATOR: Enter your custom question for the subject "
            "(this input is not monitored):[/]"
        )
        con.print()
        try:
            custom_q = input("  OPERATOR >>> ").strip()
        except (KeyboardInterrupt, EOFError):
            custom_q = ""

        if not custom_q:
            custom_q = _pick_question(QUESTION_BANK, USED_QUESTIONS) or QUESTION_BANK[0]

        con.clear()
        ui.start_dashboard(ui._session_state)

        try:
            score = _run_single_question(custom_q, self.scorer)
            self.scores.append(score)
            self._update_state_from_score(score)
        except SessionAbortException:
            pass

        report = _build_report(self.scores, mode_label="FRIEND TEST")
        ui.stop_dashboard()
        ui.show_final_report(report)
        input("\n  [Press ENTER to return to menu]")
        return report

    # \u2500\u2500 Mode 4: Single Question \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    def _run_single(self) -> dict:
        ui.update_session_state("mode", 4)
        ui.update_session_state("status", "SINGLE QUERY ACTIVE")

        q = _pick_question(QUESTION_BANK, USED_QUESTIONS) or QUESTION_BANK[0]

        try:
            score = _run_single_question(q, self.scorer)
            self.scores.append(score)
            self._update_state_from_score(score)
        except SessionAbortException:
            pass

        report = _build_report(self.scores)
        ui.stop_dashboard()
        ui.show_final_report(report)
        input("\n  [Press ENTER to return to menu]")
        return report

    # \u2500\u2500 Shared state updater \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
    def _update_state_from_score(self, score: dict):
        ui.update_session_state(
            "questions_asked",
            ui._session_state.get("questions_asked", 0) + 1,
        )
        scores_list = ui._session_state.get("scores", [])
        scores_list.append(score["lie_probability"])
        ui.update_session_state("scores", scores_list)

        if score["verdict"] == "DECEPTIVE":
            ui.update_session_state(
                "deceptive_count",
                ui._session_state.get("deceptive_count", 0) + 1,
            )
        else:
            ui.update_session_state(
                "truthful_count",
                ui._session_state.get("truthful_count", 0) + 1,
            )
