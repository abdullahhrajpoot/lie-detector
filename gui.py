import os
import sys
import time
import threading
import random
import math
import webbrowser
import json
import hashlib
from collections import deque
from flask import Flask, render_template_string
from flask_socketio import SocketIO, emit

# Load .env if present
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Import existing backend modules with graceful fallback
try:
    from analyzer import AnalysisResult, SessionAbortException
    ANALYZER_OK = True
except Exception as e:
    ANALYZER_OK = False

try:
    from scoring import LieScorer
    SCORER_OK = True
except Exception:
    SCORER_OK = False

try:
    from ai_analyst import AIAnalyst, AI_AVAILABLE
    _ai = AIAnalyst()
except Exception:
    AI_AVAILABLE = False
    _ai = None

try:
    from voice_analyzer import VoiceAnalyzer, VOICE_AVAILABLE
    _voice = VoiceAnalyzer()
except Exception:
    VOICE_AVAILABLE = False
    _voice = None

try:
    from face_tracker import FaceTracker, FACE_AVAILABLE
    _face = FaceTracker()
except Exception:
    FACE_AVAILABLE = False
    _face = None

try:
    from contradiction_engine import ContradictionEngine
    _contradiction = ContradictionEngine()
except Exception:
    _contradiction = None

try:
    from questions import QUESTION_BANK, FOLLOWUP_DECEPTIVE, FOLLOWUP_TRUTHFUL, USED_QUESTIONS
except Exception:
    QUESTION_BANK = ["Describe the last time you lied to someone close to you."]
    FOLLOWUP_DECEPTIVE = ["Be more specific about the timeline."]
    FOLLOWUP_TRUTHFUL = ["How did that experience affect you?"]
    USED_QUESTIONS = set()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'polytruth_gui_v5'
socketio = SocketIO(app, cors_allowed_origins='*', async_mode='threading')
scorer = LieScorer() if SCORER_OK else None

# \u2500\u2500 Global session state \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
_state = {
    "phase": "menu",          # menu | question | analyzing | result | report
    "current_question": "",
    "questions_asked": 0,
    "mode": 0,
    "scores": [],
    "avg_lie": 0,
    "deceptive_count": 0,
    "truthful_count": 0,
    "inconclusive_count": 0,
    "last_score": None,
    "last_flags": [],
    "last_ai_note": "",
    "last_technique": "",
    "voice_waveform": [0.0] * 40,
    "face_detected": False,
    "face_stability": 0.0,
    "look_away_count": 0,
    "contradiction_alert": None,
    "session_history": [],
    "final_report": None,
    "uptime_start": time.time(),
    "session_id": f"PTH-{random.randint(10000,99999)}",
}
_state_lock = threading.Lock()
_feature_lock = threading.Lock()
_BASELINE_PATH = "baseline_profiles.json"

_FEATURE_DEFS = {
    "camera_feed": {"label": "Live Camera Feed", "manual_arm": True, "available": FACE_AVAILABLE},
    "microphone_sensor": {"label": "Microphone Sensor", "manual_arm": True, "available": VOICE_AVAILABLE},
    "ai_forensics": {"label": "AI Forensic Analysis", "manual_arm": False, "available": AI_AVAILABLE},
    "temporal_fusion": {"label": "Temporal Fusion Model", "manual_arm": False, "available": True},
    "face_mesh_lock": {"label": "Face Lock Polygon Engine", "manual_arm": False, "available": FACE_AVAILABLE},
    "audio_forensics": {"label": "Audio Forensics Layer", "manual_arm": False, "available": VOICE_AVAILABLE},
    "contradiction_graph": {"label": "Contradiction Knowledge Graph", "manual_arm": False, "available": True},
    "adaptive_interrogation": {"label": "Adaptive Interrogation Policy", "manual_arm": False, "available": True},
    "explainability": {"label": "Confidence + Explainability", "manual_arm": False, "available": True},
    "replay_timeline": {"label": "Forensic Replay Timeline", "manual_arm": False, "available": True},
    "anti_spoof": {"label": "Anti-Spoof & Liveness", "manual_arm": False, "available": FACE_AVAILABLE or VOICE_AVAILABLE},
    "evidence_chain": {"label": "Evidence Integrity Chain", "manual_arm": False, "available": True},
    "privacy_guard": {"label": "Local Privacy Guard", "manual_arm": False, "available": True},
    "subject_baseline": {"label": "Subject Baseline Profiles", "manual_arm": False, "available": True},
    "model_lifecycle": {"label": "Model Lifecycle Telemetry", "manual_arm": False, "available": True},
}

_feature_state = {
    k: {"enabled": None, "armed": False, "available": bool(v["available"])}
    for k, v in _FEATURE_DEFS.items()
}

_fusion_window = deque(maxlen=8)
_timeline = []
_evidence_chain_tip = "GENESIS"
_baseline_profiles = {}

def _load_baselines():
    global _baseline_profiles
    try:
        if os.path.exists(_BASELINE_PATH):
            with open(_BASELINE_PATH, "r", encoding="utf-8") as f:
                _baseline_profiles = json.load(f)
    except Exception:
        _baseline_profiles = {}

def _save_baselines():
    try:
        with open(_BASELINE_PATH, "w", encoding="utf-8") as f:
            json.dump(_baseline_profiles, f, indent=2)
    except Exception:
        pass

def _log_timeline(event_type: str, payload: dict):
    global _evidence_chain_tip
    now = time.time()
    item = {"ts": now, "type": event_type, "payload": payload}
    raw = json.dumps(item, sort_keys=True, default=str).encode("utf-8")
    _evidence_chain_tip = hashlib.sha256((_evidence_chain_tip + raw.hex()).encode("utf-8")).hexdigest()
    item["chain"] = _evidence_chain_tip
    _timeline.append(item)
    if len(_timeline) > 1200:
        del _timeline[:300]

def _feature_matrix():
    out = []
    with _feature_lock:
        for key, meta in _FEATURE_DEFS.items():
            st = _feature_state[key]
            enabled = st["enabled"]
            armed = st["armed"]
            available = st["available"]
            if enabled is None:
                status = "UNSET"
            elif enabled is False:
                status = "OFF"
            elif not available:
                status = "UNAVAILABLE"
            elif meta["manual_arm"] and not armed:
                status = "NEEDS_ARM"
            else:
                status = "READY"
            out.append({
                "key": key,
                "label": meta["label"],
                "enabled": enabled,
                "armed": armed,
                "available": available,
                "manual_arm": meta["manual_arm"],
                "status": status,
            })
    return out

def _broadcast_feature_matrix():
    matrix = _feature_matrix()
    blocking = [m for m in matrix if m["status"] in ("UNSET", "UNAVAILABLE", "NEEDS_ARM")]
    socketio.emit("feature_matrix", {
        "features": matrix,
        "can_start": len(blocking) == 0,
        "blocking": blocking,
    })

def _validate_feature_readiness():
    matrix = _feature_matrix()
    blocking = [m for m in matrix if m["status"] in ("UNSET", "UNAVAILABLE", "NEEDS_ARM")]
    return len(blocking) == 0, blocking

def _feature_enabled(key: str) -> bool:
    with _feature_lock:
        return _feature_state.get(key, {}).get("enabled") is True

def _feature_armed(key: str) -> bool:
    with _feature_lock:
        return _feature_state.get(key, {}).get("armed") is True

def _arm_feature(feature_key: str):
    if feature_key == "camera_feed" and FACE_AVAILABLE and _face:
        if not _face.is_tracking:
            _face.start()
    if feature_key == "microphone_sensor" and VOICE_AVAILABLE and _voice:
        # Manual arm intent; recording still starts per question.
        pass

_load_baselines()

def _used_questions():
    global USED_QUESTIONS
    return USED_QUESTIONS

def _pick_question(pool):
    used = _used_questions()
    avail = [q for q in pool if q not in used]
    if not avail:
        return random.choice(pool)
    q = random.choice(avail)
    used.add(q)
    return q

# \u2500\u2500 Live sensor push thread \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
def _sensor_loop():
    t0 = time.time()
    while True:
        t = time.time() - t0

        mic_enabled = _feature_enabled("microphone_sensor")
        mic_armed = _feature_armed("microphone_sensor")
        cam_enabled = _feature_enabled("camera_feed")
        cam_armed = _feature_armed("camera_feed")

        # Voice waveform
        if mic_enabled and mic_armed and VOICE_AVAILABLE and _voice:
            try:
                wf = _voice.get_live_waveform(40)
            except Exception:
                wf = [abs(math.sin(t * 2 + i * 0.4)) * 0.3 for i in range(40)]
        else:
            wf = [abs(math.sin(t * 3 + i * 0.5)) * 0.15 + random.uniform(0, 0.05)
                  for i in range(40)]

        # Face stats
        if cam_enabled and cam_armed and FACE_AVAILABLE and _face:
            try:
                if not _face.is_tracking:
                    _face.start()
                fs = _face.get_current_stats()
                overlay = _face.get_overlay_state()
                face_data = {
                    "detected": fs.face_detected,
                    "stability": fs.gaze_stability,
                    "look_away": fs.look_away_count,
                    "variance": fs.face_position_variance,
                    "box": overlay.get("box"),
                    "centered": overlay.get("centered", False),
                    "distance": overlay.get("distance", 1.0),
                }
            except Exception:
                face_data = {
                    "detected": False,
                    "stability": 0,
                    "look_away": 0,
                    "variance": 0,
                    "box": None,
                    "centered": False,
                    "distance": 1.0,
                }
        else:
            face_data = {
                "detected": False,
                "stability": 0.0,
                "look_away": 0,
                "variance": 0.0,
                "box": None,
                "centered": False,
                "distance": 1.0,
            }

        # Biomarkers (always animated)
        biomarkers = {
            "cortisol":  50 + int(20 * math.sin(t * 0.7)),
            "pupil":     60 + int(15 * math.sin(t * 0.4 + 1)),
            "neural":    70 + int(18 * math.sin(t * 0.9 + 2)),
            "voc":       40 + int(12 * math.sin(t * 0.5 + 3)),
            "sweat":     30 + int(10 * math.sin(t * 1.1 + 4)),
            "o2":        55 + int(8  * math.sin(t * 0.6 + 5)),
        }

        # Heart rate
        hr = 72 + int(8 * math.sin(t * 1.3))
        rr = 15 + int(3 * math.sin(t * 0.4))

        with _state_lock:
            state_copy = dict(_state)

        socketio.emit('sensor_update', {
            'voice_waveform': wf,
            'face': face_data,
            'biomarkers': biomarkers,
            'hr': hr, 'rr': rr,
            'uptime': int(time.time() - state_copy['uptime_start']),
            'session_id': state_copy['session_id'],
            'avg_lie': state_copy['avg_lie'],
            'questions_asked': state_copy['questions_asked'],
            'deceptive': state_copy['deceptive_count'],
            'truthful': state_copy['truthful_count'],
            'phase': state_copy['phase'],
            'contradiction_alert': state_copy['contradiction_alert'],
            'last_score': state_copy['last_score'],
            'last_flags': state_copy['last_flags'],
            'last_ai_note': state_copy['last_ai_note'],
            'last_technique': state_copy['last_technique'],
            'evidence_tip': _evidence_chain_tip[:16] if _feature_enabled("evidence_chain") else "",
        })

        if _feature_enabled("replay_timeline"):
            _log_timeline("sensor", {
                "hr": hr,
                "rr": rr,
                "face_detected": face_data.get("detected", False),
                "voice_energy": round(float(sum(wf) / max(1, len(wf))), 4),
            })

        if cam_enabled and cam_armed and FACE_AVAILABLE and _face:
            try:
                frame_jpg = _face.get_latest_frame_jpeg(max_width=720, quality=65)
                if frame_jpg:
                    socketio.emit('face_frame', {'jpg': frame_jpg})
            except Exception:
                pass
        time.sleep(0.1)

# \u2500\u2500 Answer processing (runs in background thread) \u2500\u2500\u2500\u2500\u2500
def _process_answer(answer_text, question_text):
    with _state_lock:
        _state['phase'] = 'analyzing'

    try:
        # Build fake AnalysisResult from web input
        # (No keystroke hooks in browser \u2014 we use timing from JS)
        words = answer_text.split()
        word_count = len(words)
        
        result = AnalysisResult(
            answer=answer_text,
            word_count=word_count,
            cognitive_delay=random.gauss(4.5, 1.5),  # simulated for web
            wpm=max(10, min(120, word_count * 4)),
            burst_volatility=random.gauss(0.6, 0.15),
            backspace_count=0,
            duration=max(5.0, word_count * 0.6)
        )

        # Voice
        if _feature_enabled("microphone_sensor") and _feature_armed("microphone_sensor") and VOICE_AVAILABLE and _voice:
            try:
                voice_result = _voice.stop_recording()
            except Exception:
                voice_result = _get_empty_voice()
        else:
            voice_result = _get_empty_voice()

        # Face
        if _feature_enabled("camera_feed") and _feature_armed("camera_feed") and FACE_AVAILABLE and _face:
            try:
                face_stats = _face.get_current_stats()
            except Exception:
                face_stats = _get_empty_face()
        else:
            face_stats = _get_empty_face()

        # Contradiction
        if _feature_enabled("contradiction_graph") and _contradiction:
            contradiction = _contradiction.check_contradiction(answer_text)
        else:
            contradiction = _get_empty_contradiction()

        # AI analysis
        socketio.emit('status_msg', {'msg': 'RUNNING FORENSIC LINGUISTIC ANALYSIS...'})
        if _feature_enabled("ai_forensics") and _ai and AI_AVAILABLE:
            history = _contradiction.get_timeline() if _contradiction else []
            ai_result = _ai.analyze(answer_text, question_text, history)
        else:
            ai_result = _get_empty_ai()

        # Score
        if scorer:
            score = scorer.score_multimodal(
                result, ai_result, voice_result, face_stats, contradiction
            )
        else:
            score = {"lie_probability": 50, "verdict": "INCONCLUSIVE",
                     "confidence": "LOW", "flags": [], "source_breakdown": {}}

        score['question'] = question_text
        score['addon_signals'] = {}

        # Anti-spoof / liveness heuristics.
        if _feature_enabled("anti_spoof"):
            spoof_risk = 0
            if getattr(face_stats, "face_detected", False) and getattr(face_stats, "gaze_stability", 0.0) > 0.995:
                spoof_risk += 12
            if getattr(voice_result, "amplitude_variance", 0.0) < 0.0004 and _feature_enabled("microphone_sensor"):
                spoof_risk += 10
            if spoof_risk >= 12:
                score['flags'] = list(score.get('flags', [])) + ["LIVENESS ALERT: POSSIBLE SPOOF SIGNATURE"]
                score['lie_probability'] = min(99, int(score['lie_probability'] + spoof_risk * 0.4))
            score['addon_signals']['spoof_risk'] = spoof_risk

        # Temporal fusion model (lightweight online sequence fusion).
        if _feature_enabled("temporal_fusion"):
            _fusion_window.append(float(score['lie_probability']))
            fused = sum(_fusion_window) / len(_fusion_window)
            spread = max(_fusion_window) - min(_fusion_window) if len(_fusion_window) > 1 else 0.0
            uncertainty = max(0.0, min(1.0, spread / 60.0))
            score['addon_signals']['fused_lie_probability'] = round(fused, 2)
            score['addon_signals']['uncertainty'] = round(uncertainty, 3)
            score['lie_probability'] = int(round((0.65 * score['lie_probability']) + (0.35 * fused)))
            if uncertainty > 0.55:
                score['flags'] = list(score.get('flags', [])) + ["HIGH TEMPORAL UNCERTAINTY"]

        if _feature_enabled("audio_forensics"):
            score['addon_signals']['audio_forensics'] = {
                "variance": round(float(getattr(voice_result, "amplitude_variance", 0.0)), 6),
                "silence_ratio": round(float(getattr(voice_result, "silence_ratio", 1.0)), 4),
            }

        if _feature_enabled("face_mesh_lock"):
            score['addon_signals']['face_lock'] = {
                "stability": round(float(getattr(face_stats, "gaze_stability", 0.0)), 4),
                "look_away_count": int(getattr(face_stats, "look_away_count", 0)),
            }

        if _feature_enabled("explainability"):
            score['explainability'] = [
                f"Fusion P(X): {score['addon_signals'].get('fused_lie_probability', score['lie_probability'])}%",
                f"Sensor stability: face={round(float(getattr(face_stats, 'gaze_stability', 0.0)), 3)} voice_var={round(float(getattr(voice_result, 'amplitude_variance', 0.0)), 5)}",
                f"Evidence chain tip: {_evidence_chain_tip[:12]}",
            ]

        if _feature_enabled("contradiction_graph") and _contradiction:
            _contradiction.add_answer(question_text, answer_text, score)

        # Update state
        with _state_lock:
            _state['scores'].append(score['lie_probability'])
            _state['avg_lie'] = sum(_state['scores']) / len(_state['scores'])
            _state['questions_asked'] += 1
            v = score.get('verdict', 'INCONCLUSIVE')
            if v == 'DECEPTIVE':   _state['deceptive_count'] += 1
            elif v == 'TRUTHFUL':  _state['truthful_count'] += 1
            else:                  _state['inconclusive_count'] += 1
            _state['last_score'] = score['lie_probability']
            _state['last_flags'] = score.get('flags', [])[:8]
            _state['last_ai_note'] = score.get('ai_profile_note', '')
            _state['last_technique'] = score.get('deception_technique', '') or ''
            stored_answer = answer_text
            if _feature_enabled("privacy_guard"):
                stored_answer = f"[REDACTED:{hashlib.sha256(answer_text.encode('utf-8')).hexdigest()[:12]}]"
            _state['session_history'].append({
                'question': question_text,
                'answer': stored_answer,
                'score': score
            })
            if contradiction and hasattr(contradiction, 'detected') and contradiction.detected:
                _state['contradiction_alert'] = {
                    'type': contradiction.contradiction_type,
                    'severity': contradiction.severity,
                    'prior': contradiction.prior_question or '',
                }
            _state['last_score_full'] = score
            _state['phase'] = 'result'

        if _feature_enabled("replay_timeline"):
            _log_timeline("answer_scored", {
                "question": question_text[:120],
                "lie_probability": score.get("lie_probability"),
                "verdict": score.get("verdict"),
            })

        socketio.emit('answer_scored', {
            'lie_probability': score['lie_probability'],
            'verdict': score.get('verdict', 'INCONCLUSIVE'),
            'confidence': score.get('confidence', 'LOW'),
            'flags': score.get('flags', [])[:8],
            'ai_note': score.get('ai_profile_note', ''),
            'technique': score.get('deception_technique', '') or '',
            'source_breakdown': score.get('source_breakdown', {}),
            'contradiction': contradiction.detected if contradiction and hasattr(contradiction,'detected') else False,
            'addon_signals': score.get('addon_signals', {}),
            'explainability': score.get('explainability', []),
        })

    except Exception as e:
        with _state_lock:
            _state['phase'] = 'result'
        socketio.emit('error_msg', {'msg': str(e)})

# \u2500\u2500 Empty result factories \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
def _get_empty_voice():
    try:
        from voice_analyzer import VoiceResult
        return VoiceResult(0,0,0,1.0,0,[])
    except Exception:
        class V: avg_amplitude=0; peak_amplitude=0; amplitude_variance=0
        class V2(V): silence_ratio=1.0; stress_score=0; stress_flags=[]
        return V2()

def _get_empty_face():
    try:
        from face_tracker import FaceStats
        return FaceStats(False,0.0,0.5,0,0.0,0,[])
    except Exception:
        class F: face_detected=False; face_confidence=0; gaze_stability=0.5
        class F2(F): look_away_count=0; face_position_variance=0; face_score=0; face_flags=[]
        return F2()

def _get_empty_contradiction():
    class C:
        detected=False; prior_question=None; prior_excerpt=None
        new_excerpt=None; contradiction_type=None; severity="LOW"
    return C()

def _get_empty_ai():
    return {
        "ai_lie_score_delta": 0,
        "linguistic_flags": ["AI ANALYSIS UNAVAILABLE \u2014 RULE ENGINE ACTIVE"],
        "contradiction_detected": False,
        "contradiction_detail": None,
        "psychological_profile_note": "Insufficient data for AI profile.",
        "deception_technique": None
    }

# \u2500\u2500 SocketIO events \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
@socketio.on('connect')
def on_connect():
    emit('connected', {
        'ai': AI_AVAILABLE,
        'voice': VOICE_AVAILABLE,
        'face': FACE_AVAILABLE,
        'session_id': _state['session_id'],
        'model_lifecycle': {
            'scorer_loaded': SCORER_OK,
            'analyzer_loaded': ANALYZER_OK,
            'ai_model': 'gemini-1.5-flash' if AI_AVAILABLE else 'offline',
            'build': 'polytruth-v5-addon-pack',
        },
    })
    emit('feature_matrix', {
        'features': _feature_matrix(),
        'can_start': _validate_feature_readiness()[0],
        'blocking': _validate_feature_readiness()[1],
    })

@socketio.on('set_feature')
def on_set_feature(data):
    key = str(data.get('key', '')).strip()
    action = str(data.get('action', '')).strip().lower()
    if key not in _FEATURE_DEFS:
        emit('error_msg', {'msg': f'Unknown feature: {key}'})
        return

    with _feature_lock:
        st = _feature_state[key]
        if action == 'enable':
            st['enabled'] = True
        elif action == 'disable':
            st['enabled'] = False
            st['armed'] = False
        elif action == 'arm':
            st['armed'] = True
        elif action == 'disarm':
            st['armed'] = False
        else:
            emit('error_msg', {'msg': f'Unknown action: {action}'})
            return

    if action == 'arm':
        try:
            _arm_feature(key)
        except Exception:
            pass

    _broadcast_feature_matrix()

@socketio.on('bulk_feature_action')
def on_bulk_feature_action(data):
    action = str(data.get('action', '')).strip().lower()
    with _feature_lock:
        for key, st in _feature_state.items():
            if action == 'disable_all':
                st['enabled'] = False
                st['armed'] = False
            elif action == 'enable_all_available':
                st['enabled'] = bool(_FEATURE_DEFS[key]["available"])
                if not st['enabled']:
                    st['armed'] = False
            elif action == 'reset':
                st['enabled'] = None
                st['armed'] = False
    if action == 'enable_all_available':
        for key in _FEATURE_DEFS:
            if _FEATURE_DEFS[key]["manual_arm"]:
                continue
            # non-manual features are considered armed by design
            pass
    _broadcast_feature_matrix()

@socketio.on('request_feature_matrix')
def on_request_feature_matrix(_data=None):
    _broadcast_feature_matrix()

@socketio.on('start_session')
def on_start_session(data):
    ready, blocking = _validate_feature_readiness()
    if not ready:
        emit('session_blocked', {
            'reason': 'Enable or disable every promised add-on, and arm required hardware first.',
            'blocking': blocking,
        })
        _broadcast_feature_matrix()
        return

    mode = int(data.get('mode', 1))
    _fusion_window.clear()
    _timeline.clear()
    global _evidence_chain_tip
    _evidence_chain_tip = "GENESIS"
    with _state_lock:
        _state['mode'] = mode
        _state['phase'] = 'question'
        _state['questions_asked'] = 0
        _state['scores'] = []
        _state['session_history'] = []
        _state['avg_lie'] = 0
        _state['deceptive_count'] = 0
        _state['truthful_count'] = 0
        _state['inconclusive_count'] = 0
        _state['final_report'] = None
    if _feature_enabled("camera_feed") and _feature_armed("camera_feed") and FACE_AVAILABLE and _face:
        try: _face.start()
        except Exception: pass
    q = _pick_question(QUESTION_BANK)
    with _state_lock:
        _state['current_question'] = q
    emit('new_question', {'question': q, 'number': _state['questions_asked'] + 1})

@socketio.on('submit_answer')
def on_submit_answer(data):
    answer = data.get('answer', '').strip()
    question = data.get('question', '')
    if len(answer.split()) < 15:
        emit('answer_rejected', {'reason': 'MINIMUM 15 WORDS REQUIRED. SYSTEM DEMANDS FULL NARRATIVE.'})
        return
    if _feature_enabled("microphone_sensor") and _feature_armed("microphone_sensor") and VOICE_AVAILABLE and _voice:
        try: _voice.start_recording()
        except Exception: pass
    t = threading.Thread(target=_process_answer, args=(answer, question), daemon=True)
    t.start()

@socketio.on('next_question')
def on_next_question(data):
    with _state_lock:
        asked = _state['questions_asked']
        mode = _state['mode']
        last = _state.get('last_score_full')
        _state['contradiction_alert'] = None

    max_q = {1: 6, 2: 5, 3: 1, 4: 1}.get(mode, 4)
    if asked >= max_q:
        _generate_final_report()
        return

    # Interrogation mode branching
    pool = QUESTION_BANK
    if mode == 2 and last:
        if _feature_enabled("adaptive_interrogation"):
            uncertainty = float(last.get("addon_signals", {}).get("uncertainty", 0.4))
            if uncertainty > 0.5:
                pool = QUESTION_BANK
            else:
                v = last.get('verdict','')
                if v == 'DECEPTIVE':
                    pool = FOLLOWUP_DECEPTIVE
                elif v == 'TRUTHFUL':
                    pool = FOLLOWUP_TRUTHFUL
        else:
            v = last.get('verdict','')
            if v == 'DECEPTIVE': pool = FOLLOWUP_DECEPTIVE
            elif v == 'TRUTHFUL': pool = FOLLOWUP_TRUTHFUL

    q = _pick_question(pool)
    with _state_lock:
        _state['current_question'] = q
        _state['phase'] = 'question'

    emit('new_question', {'question': q, 'number': asked + 1})

@socketio.on('end_session')
def on_end_session(data):
    _generate_final_report()

@socketio.on('reset_session')
def on_reset_session(data=None):
    global USED_QUESTIONS
    USED_QUESTIONS.clear()
    _fusion_window.clear()
    new_id = f"PTH-{random.randint(10000,99999)}"
    with _state_lock:
        _state['phase'] = 'menu'
        _state['mode'] = 0
        _state['questions_asked'] = 0
        _state['scores'] = []
        _state['session_history'] = []
        _state['avg_lie'] = 0
        _state['deceptive_count'] = 0
        _state['truthful_count'] = 0
        _state['inconclusive_count'] = 0
        _state['final_report'] = None
        _state['last_score'] = None
        _state['last_score_full'] = None
        _state['last_flags'] = []
        _state['last_ai_note'] = ''
        _state['last_technique'] = ''
        _state['contradiction_alert'] = None
        _state['session_id'] = new_id
        _state['uptime_start'] = time.time()
    emit('session_reset', {'session_id': new_id})

def _generate_final_report():
    with _state_lock:
        _state['phase'] = 'report'
        history = list(_state['session_history'])
        scores = list(_state['scores'])
        session_id = _state['session_id']

    socketio.emit('status_msg', {'msg': 'GENERATING FORENSIC PROFILE...'})

    profile = "Session complete. Behavioral profile archived."
    if _feature_enabled("ai_forensics") and _ai and AI_AVAILABLE:
        try:
            answers = [h['answer'] for h in history]
            all_scores = [h['score'] for h in history]
            profile = _ai.generate_final_profile(all_scores, answers)
        except Exception:
            pass

    avg = sum(scores) / len(scores) if scores else 0
    dec = sum(1 for h in history if h['score'].get('verdict') == 'DECEPTIVE')
    tru = sum(1 for h in history if h['score'].get('verdict') == 'TRUTHFUL')

    if avg > 60 or dec > len(history) // 2:
        overall = "SUBJECT FLAGGED"
    elif avg < 35 and dec == 0:
        overall = "SUBJECT CLEARED"
    else:
        overall = "ANALYSIS INCONCLUSIVE"

    baseline_note = None
    if _feature_enabled("subject_baseline"):
        prior = _baseline_profiles.get(session_id, {})
        prior_avg = float(prior.get("avg_lie", avg))
        delta = round(avg - prior_avg, 2)
        baseline_note = {
            "prior_avg_lie": round(prior_avg, 2),
            "current_avg_lie": round(avg, 2),
            "delta": delta,
        }
        _baseline_profiles[session_id] = {
            "avg_lie": round(avg, 2),
            "updated_at": time.time(),
            "sessions": int(prior.get("sessions", 0)) + 1,
        }
        _save_baselines()

    report = {
        'total': len(history),
        'avg': round(avg, 1),
        'max': max(scores) if scores else 0,
        'deceptive': dec,
        'truthful': tru,
        'overall': overall,
        'profile': profile,
        'history': [
            {'q': h['question'][:80], 'score': h['score'].get('lie_probability', 0),
             'verdict': h['score'].get('verdict', '')} for h in history
        ],
        'baseline': baseline_note,
        'evidence_tip': _evidence_chain_tip[:24] if _feature_enabled("evidence_chain") else None,
        'timeline_tail': _timeline[-20:] if _feature_enabled("replay_timeline") else [],
        'addons': _feature_matrix(),
    }
    with _state_lock:
        _state['final_report'] = report

    socketio.emit('final_report', report)

# \u2500\u2500 HTML template (the entire frontend) \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500

@app.route('/')
def index():
    try:
        html = open('gui_template.html', encoding='utf-8').read()
    except Exception:
        html = "<html><body><h1>Missing gui_template.html</h1></body></html>"
    return html

# \u2500\u2500 Launch \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
if __name__ == '__main__':
    sensor_thread = threading.Thread(target=_sensor_loop, daemon=True)
    sensor_thread.start()
    print("\n  POLYTRUTH GUI v5.0 \u2014 LAUNCHING")
    print("  Opening browser at http://localhost:5000")
    print("  Press Ctrl+C to shut down\n")
    def open_browser():
        try:
            webbrowser.open('http://localhost:5000')
        except:
            pass
    threading.Timer(1.5, open_browser).start()
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)
