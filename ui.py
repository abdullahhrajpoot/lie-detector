"""
ui.py \u2014 POLYTRUTH v5.0
Edge-to-edge retro-cyberpunk rich dashboard.
Runs the Live render loop in a background thread.
"""

import math
import random
import threading
import time
from typing import Optional

from rich import box
from rich.columns import Columns
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn
from rich.table import Table
from rich.text import Text

from neural_display import NeuralDisplay

# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
# Global console (force terminal width awareness)
# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
console = Console()
_neural_display = NeuralDisplay()

# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
# Thread control
# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
_live: Optional[Live] = None
_render_thread: Optional[threading.Thread] = None
_stop_event = threading.Event()
_state_lock = threading.Lock()
_session_state: dict = {}

# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
# Ticker messages
# \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
_TICKER_MSGS = [
    "POLYTRUTH ENGINE v5.0 // BEHAVIORAL KERNEL ACTIVE",
    "PSI-LINK ESTABLISHED // BIOMETRIC DAEMON RUNNING",
    "LEXICAL TRAP DATABASE: 1,247 PATTERNS LOADED",
    "NEURAL LOAD INDEX: MONITORING",
    "KEYSTROKE PSI SENSORS: CALIBRATED",
    "MEMORY ENCRYPTION: AES-512 // SECURE",
    "UPLINK: SECURE CHANNEL ACTIVE",
    "WARNING: THIS SESSION IS BEING ARCHIVED",
    "SUBJECT INTAKE PROTOCOL: ARMED",
    "VOCAL STRESS ANALYSIS: ACTIVE",
    "MICRO-EXPRESSION GRID: ACTIVE",
    "GALVANIC SKIN RESPONSE: NOMINAL",
    "CORTISOL PROJECTION: ENABLED",
    "TRUTH PROBABILITY ENGINE: READY",
]

_BG_CHECKS = [
    "INTERPOL DB: QUERYING...",
    "FACIAL MATCH: SCANNING...",
    "PRIORS: 0 FOUND",
    "FINANCIAL: FLAGGED",
    "SOCIAL GRAPH: MAPPING...",
    "BIOMETRIC HASH: COMPUTING",
    "VOICE PRINT: INDEXING",
    "TRAVEL HISTORY: PULLING",
    "COMM INTERCEPTS: SEARCHING",
    "KNOWN ASSOCIATES: 14 IDENTIFIED",
    "THREAT LEVEL: MODERATE",
    "EMPLOYMENT: UNVERIFIED",
    "CLEARANCE: REVOKED",
    "DARK WEB FOOTPRINT: DETECTED",
    "LAST KNOWN LOCATION: CONFIRMED",
]

_BIOMARKERS = [
    ("Cortisol", 63),
    ("Pupil Dilation", 79),
    ("Neural Load", 88),
    ("VOC Tension", 41),
    ("Micro-Sweat", 28),
    ("Blood O2", 55),
]
_biomarker_vals = {name: base for name, base in _BIOMARKERS}

def _drift_biomarkers():
    for name, _ in _BIOMARKERS:
        delta = random.randint(-2, 2)
        new_val = _biomarker_vals[name] + delta
        _biomarker_vals[name] = max(5, min(98, new_val))

BRAILLE_LEVELS = [" ", "\u28c0", "\u28e4", "\u28f6", "\u28ff"]
BLOCK_LEVELS = [" ", "\u2581", "\u2582", "\u2583", "\u2584", "\u2585", "\u2586", "\u2587", "\u2588"]

def _wave_value(t: float, x: int, freq: float = 1.0, speed: float = 2.0, noise: float = 0.0) -> float:
    v = 0.5 + 0.5 * math.sin(freq * x * 0.4 - speed * t)
    if noise > 0:
        v += random.uniform(-noise, noise)
    return max(0.0, min(1.0, v))

def _render_wave(width: int, t: float, freq: float, speed: float, noise: float, color: str, label: str) -> Text:
    line = Text(f"{label}: ", style=f"bold {color}")
    for x in range(width - len(label) - 2):
        v = _wave_value(t, x, freq, speed, noise)
        idx = int(v * (len(BRAILLE_LEVELS) - 1))
        line.append(BRAILLE_LEVELS[idx], style=color)
    return line

def _build_left_panel(t: float) -> Panel:
    w = max(20, console.width // 4 - 4)
    lines = Text()
    lines.append("\u2500" * w + "\n", style="dim green")
    lines.append(_render_wave(w, t, 1.0, 3.0, 0.0, "bright_green", "\u2764 CARDIAC"))
    lines.append("\n")
    lines.append(_render_wave(w, t, 0.5, 1.5, 0.0, "cyan", "\u25c9 RESPIR "))
    lines.append("\n")
    lines.append(_render_wave(w, t, 2.0, 5.0, 0.25, "red", "\u26a1 GSR    "))
    lines.append("\n")
    lines.append("\u2500" * w + "\n", style="dim green")

    lines.append(f"  HR: {60 + int(12*math.sin(t*0.7))} BPM\n", style="bright_green")
    lines.append(f"  RR: {14 + int(4*math.sin(t*0.3))} /min\n", style="cyan")
    lines.append(f"  SC: {1.2 + 0.4*math.sin(t*1.1):.2f} \u03bcS\n", style="red")
    lines.append("\u2500" * w + "\n", style="dim green")

    return Panel(
        lines,
        title="[bold bright_green]\u25e2 BIOMETRIC WAVEFORMS \u25e3[/]",
        border_style="green",
        expand=True,
    )

def _build_center_panel(t: float, frame_counter: int) -> Panel:
    with _state_lock:
        state = dict(_session_state)
        
    alert = state.get("contradiction_alert")
    if alert:
        border_color = "red" if (frame_counter % 6) < 3 else "bright_red"
        alert_text = Text(justify="center")
        alert_text.append("\n\n\u26a0 CONTRADICTION DETECTED \u26a0\n\n", style="bold red")
        alert_text.append(f"Prior Q: \"{str(alert.get('prior'))[:30]}...\"\n", style="yellow")
        alert_text.append(f"Conflict: {alert.get('type')}\n", style="yellow")
        alert_text.append(f"Severity: {alert.get('severity')}\n\n", style="bold bright_red")
        
        return Panel(
            alert_text,
            title="[bold red]\u25e2 PRIORITY ALERT \u25e3[/]",
            border_style=border_color,
            expand=True,
        )

    content = Table.grid(expand=True)

    # Top: stats table
    tbl = Table.grid(expand=True, padding=(0, 1))
    tbl.add_column(style="dim cyan", justify="right")
    tbl.add_column(style="bright_green", justify="left")
    
    avg_prob = state.get('avg_lie_prob', 0)
    tbl.add_row("SESSION ID", f"PTH-{abs(hash(str(t)))%99999:05d}")
    tbl.add_row("Q ASKED", str(state.get("questions_asked", 0)))
    tbl.add_row("AVG LIE %", f"{avg_prob:.0f}%")
    tbl.add_row("STATUS", state.get("status", "AWAITING SUBJECT"))
    
    content.add_row(tbl)
    content.add_row(Text("\n\u2500"*20, style="dim green"))
    
    # Middle: Neural Network
    content.add_row(Text("◈ CORTICAL ANALYSIS", style="bold cyan"))
    neural = _neural_display.render(int(avg_prob), frame_counter, 40, 5)
    content.add_row(neural)
    content.add_row(Text("\u2500"*20, style="dim green"))
    
    # Lower: AI Commentary
    content.add_row(Text("◈ AI LINGUISTIC FEED", style="bold yellow"))
    ai_flags = state.get("latest_ai_flags", ["AWAITING DATA..."])
    # display up to 3
    ai_text = Text()
    for flag in ai_flags[-3:]:
        ai_text.append(f"► {flag}\n", style="dim yellow")
    content.add_row(ai_text)
    
    # Bottom: Camera
    cam_lines = Text()
    cam_lines.append("\n[CAMERA LINK: ", style="dim cyan")
    cam_lines.append("ACTIVE", style="bold bright_green")
    cam_lines.append("]\n", style="dim cyan")
    cam_lines.append(f"  FRAMES: {int(t * 30) % 99999:05d}  FPS: {28+int(4*math.sin(t))}\n", style="dim green")
    
    content.add_row(cam_lines)

    return Panel(
        content,
        title="[bold cyan]\u25e2 SUBJECT PROFILE \u25e3[/]",
        border_style="cyan",
        expand=True,
    )

_hex_lines: list = []
_hex_frame_counter = 0

def _next_hex_line() -> str:
    addr = random.randint(0x1000, 0xFFFF)
    data = " ".join(f"{random.randint(0,255):02X}" for _ in range(4))
    return f"0x{addr:04X}: {data}"

def _build_right_panel(t: float) -> Layout:
    with _state_lock:
        state = dict(_session_state)
        
    global _hex_lines, _hex_frame_counter
    _hex_frame_counter += 1
    if _hex_frame_counter % 2 == 0:
        _hex_lines.append(_next_hex_line())
        if len(_hex_lines) > 5:
            _hex_lines.pop(0)
    while len(_hex_lines) < 5:
        _hex_lines.append(_next_hex_line())

    # Voice waveform
    voice_data = state.get("voice_waveform", [0.0] * 30)
    voice_text = Text()
    for i, amp in enumerate(voice_data):
        idx = int(min(1.0, max(0.0, amp)) * (len(BLOCK_LEVELS) - 1))
        # fallback string
        if isinstance(amp, str): 
            voice_text = Text(amp)
            break
        color = "red" if amp > 0.6 else "yellow" if amp > 0.3 else "green"
        voice_text.append(BLOCK_LEVELS[idx], style=color)
    
    top_p = Panel(
        voice_text,
        title="[bold green]\u25c8 ACOUSTIC STRESS SENSOR[/]",
        border_style="green",
    )
    
    # Face tracing
    fst = state.get("face_stats")
    face_text = Text()
    if fst:
        face_str = "DETECTED" if fst.face_detected else "ABSENT"
        f_color = "bright_green" if fst.face_detected else "red"
        face_text.append(f"FACE: [{face_str}]\n", style=f"bold {f_color}")
        
        stab_w = 15
        stab_f = int(stab_w * fst.gaze_stability)
        stab_bar = "█" * stab_f + "░" * (stab_w - stab_f)
        face_text.append(f"STB: [{stab_bar}]\n", style="dim cyan")
        face_text.append(f"AWAY: {fst.look_away_count} ", style="red" if fst.look_away_count > 2 else "green")
    else:
        face_text.append("[SENSOR OFFLINE]", style="dim red")
        
    mid_p = Panel(
        face_text,
        title="[bold cyan]\u25c8 BIOMETRIC VISUAL FEED[/]",
        border_style="cyan",
    )

    hex_text = Text()
    for line in _hex_lines:
        hex_text.append(line + "\n", style="dim green")
        
    bg_idx = int(t * 0.8) % len(_BG_CHECKS)
    bg_text = Text()
    for i, msg in enumerate(_BG_CHECKS):
        if i >= 4: break # Limit height
        act_idx = (bg_idx + i) % len(_BG_CHECKS)
        bg_text.append(f"► {_BG_CHECKS[act_idx]}\n", style="dim green")

    bot_content = Table.grid(expand=True)
    bot_content.add_row(Text("◈ MEMORY HEX", style="bold dim green"))
    bot_content.add_row(hex_text)
    bot_content.add_row(Text("◈ BG CHECK", style="bold dim cyan"))
    bot_content.add_row(bg_text)

    bot_p = Panel(
        bot_content,
        title="[bold green]\u25e2 INTEL FEED \u25e3[/]",
        border_style="green",
    )
    
    lay = Layout()
    lay.split_column(
        Layout(top_p, size=4),
        Layout(mid_p, size=6),
        Layout(bot_p, ratio=1)
    )
    return lay

def _build_biomarker_bar(name: str, value: int) -> Text:
    bar_width = 20
    filled = int(bar_width * value / 100)
    empty = bar_width - filled
    bar = "█" * filled + "░" * empty
    color = "bright_green" if value < 50 else "yellow" if value < 75 else "red"
    t = Text()
    t.append(f"  {name:<16}", style="dim cyan")
    t.append(f"[{bar}]", style=color)
    t.append(f" {value:3d}%", style=f"bold {color}")
    return t

def _build_biomarker_row() -> Panel:
    _drift_biomarkers()
    items = list(_biomarker_vals.items())
    left_col = Table.grid(expand=True)
    right_col = Table.grid(expand=True)
    for i, (name, val) in enumerate(items):
        if i < 3:
            left_col.add_row(_build_biomarker_bar(name, val))
        else:
            right_col.add_row(_build_biomarker_bar(name, val))

    cols = Table.grid(expand=True)
    cols.add_column(ratio=1)
    cols.add_column(ratio=1)
    cols.add_row(left_col, right_col)

    return Panel(
        cols,
        title="[bold bright_green]\u25e2 BIOMARKER ARRAY \u25e3[/]",
        border_style="green",
        expand=True,
    )

def _build_header(t: float) -> Panel:
    ticker_idx = int(t * 0.4) % len(_TICKER_MSGS)
    header_text = Text(justify="center")
    header_text.append(
        "▓▓ POLYTRUTH v5.0 // BEHAVIORAL INTERROGATION SYSTEM // ACTIVE ▓▓\n",
        style="bold bright_green",
    )
    header_text.append(
        f"  ► {_TICKER_MSGS[ticker_idx]}",
        style="dim cyan",
    )
    return Panel(header_text, border_style="green", expand=True)

def _build_status_bar(t: float) -> Panel:
    uptime = int(t)
    h, rem = divmod(uptime, 3600)
    m, s = divmod(rem, 60)
    psi = 14.7 + 0.3 * math.sin(t * 0.7)
    status = Text()
    status.append(f"  PSI: {psi:.2f} kPa  ", style="dim green")
    status.append(f"UPTIME: {h:02d}:{m:02d}:{s:02d}  ", style="dim cyan")
    status.append("DRIVES MOUNTED: 7/7  ", style="bright_green")
    status.append("ENCRYPTION: AES-512  ", style="dim green")
    status.append(f"THREAD COUNT: {7 + int(t)%4}  ", style="dim cyan")
    status.append("SESSION: SECURE", style="bold bright_green")
    return Panel(status, border_style="dim green", expand=True)

_frame_counter = 0

def _build_layout(t: float) -> Layout:
    global _frame_counter
    _frame_counter += 1
    
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=4),
        Layout(name="main", ratio=1),
        Layout(name="biomarkers", size=7),
        Layout(name="statusbar", size=3),
    )
    layout["header"].update(_build_header(t))

    layout["main"].split_row(
        Layout(name="left", ratio=1),
        Layout(name="center", ratio=1),
        Layout(name="right", ratio=1), # 4 column effectively 1:1:1
    )
    layout["main"]["left"].update(_build_left_panel(t))
    layout["main"]["center"].update(_build_center_panel(t, _frame_counter))
    layout["main"]["right"].update(_build_right_panel(t))

    layout["biomarkers"].update(_build_biomarker_row())
    layout["statusbar"].update(_build_status_bar(t))

    return layout

_START_TIME = time.time()

def _render_loop():
    global _live
    with Live(
        _build_layout(0),
        console=console,
        refresh_per_second=6,
        screen=True,
    ) as live:
        _live = live
        while not _stop_event.is_set():
            t = time.time() - _START_TIME
            try:
                live.update(_build_layout(t))
            except Exception:
                pass
            time.sleep(0.16)
    _live = None

def start_dashboard(session_state: dict):
    global _render_thread, _session_state
    with _state_lock:
        _session_state.update(session_state)
    _stop_event.clear()
    _render_thread = threading.Thread(target=_render_loop, daemon=True)
    _render_thread.start()
    time.sleep(0.5)

def stop_dashboard():
    global _live
    _stop_event.set()
    if _render_thread:
        _render_thread.join(timeout=3)
    time.sleep(0.15)
    console.clear()

def update_session_state(key: str, value):
    with _state_lock:
        _session_state[key] = value
        scores = _session_state.get("scores", [])
        if scores:
            _session_state["avg_lie_prob"] = sum(scores) / len(scores)

def update_voice_data(voice_analyzer_instance):
    with _state_lock:
        if voice_analyzer_instance:
            _session_state["voice_waveform"] = voice_analyzer_instance.get_live_waveform(30)

def update_face_data(face_stats):
    with _state_lock:
        if face_stats:
            _session_state["face_stats"] = face_stats

def show_analysis_progress(msg: str):
    console.print(f"  [dim cyan]{msg}[/]")

def show_question(question_text: str):
    console.print()
    console.rule("[bold cyan]◈ SUBJECT QUESTION ◈[/]", style="cyan")
    console.print()
    q_panel = Panel(
        Text(question_text, style="bold bright_green", justify="full"),
        title="[bold yellow]POLYTRUTH QUERY[/]",
        border_style="yellow",
        expand=True,
        padding=(1, 2),
    )
    console.print(q_panel)
    console.print()
    console.print("[dim cyan]  Type your answer and press ENTER (ESC to abort session)[/]")
    console.print()

def show_result(score_dict: dict):
    verdict = score_dict.get("verdict", "INCONCLUSIVE")
    prob = score_dict.get("lie_probability", 0)
    conf = score_dict.get("confidence", "LOW")
    flags = score_dict.get("flags", [])
    
    color_map = {
        "TRUTHFUL": "bold bright_green",
        "DECEPTIVE": "bold red",
        "INCONCLUSIVE": "bold yellow",
    }
    border_map = {"TRUTHFUL": "green", "DECEPTIVE": "red", "INCONCLUSIVE": "yellow"}
    color = color_map.get(verdict, "white")
    border = border_map.get(verdict, "white")

    content = Text()
    content.append(f"\n  VERDICT:          ", style="dim cyan")
    content.append(f"{verdict}\n", style=color)
    content.append(f"  LIE PROBABILITY:  ", style="dim cyan")
    content.append(f"{prob}%\n", style=color)
    content.append(f"  CONFIDENCE:       ", style="dim cyan")
    content.append(f"{conf}\n\n", style="bold white")

    # AI Profile Note
    ai_note = score_dict.get("ai_profile_note")
    if ai_note:
        content.append(f"◈ AI FORENSIC ANALYSIS\n  {ai_note}\n\n", style="bright_green")
        
    tech = score_dict.get("deception_technique")
    if tech:
        content.append(f"◈ DECEPTION TECHNIQUE: [{tech}]\n\n", style="yellow")

    contradiction = score_dict.get("contradiction")
    if contradiction and contradiction.detected:
        content.append(f"◈ CONTRADICTION DETECTED\n  Conflict: {contradiction.contradiction_type}\n  Severity: {contradiction.severity}\n\n", style="bold red")

    # Sources Breakdown
    s_brk = score_dict.get("source_breakdown", {})
    if s_brk:
        content.append("◈ SOURCE BREAKDOWN\n", style="dim cyan")
        def render_bar(name, val):
            val = max(0, min(100, val)) # clamp
            fw = int(20 * (abs(val)/100))
            bar = "█" * fw + "░" * (20 - fw)
            content.append(f"  {name:<13}: {val:>+3}pts  {bar}\n", style="cyan")
            
        render_bar("RULE ENGINE", s_brk.get('rule_based', 0))
        render_bar("AI ANALYSIS", s_brk.get('ai_delta', 0))
        render_bar("VOICE STRESS", s_brk.get('voice_stress', 0))
        render_bar("FACE TRACK", s_brk.get('face_tracking', 0))
        content.append("\n")

    if flags:
        content.append("  ── BEHAVIORAL FLAGS ──\n", style="dim green")
        for flag in flags:
            style = "bold red" if "CONTRADICTION" in flag else "yellow"
            content.append(f"  ► {flag}\n", style=style)

    console.print()
    console.print(Panel(content, title=f"[{color}]\u25e2 ANALYSIS COMPLETE \u25e3[/]", border_style=border, expand=True))
    console.print()
    time.sleep(3)

def show_final_report(report: dict):
    console.clear()
    console.rule("[bold bright_green]\u25e2 POLYTRUTH SESSION REPORT \u25e3[/]", style="green")
    console.print()

    tbl = Table(
        title="SESSION ANALYSIS SUMMARY",
        border_style="green",
        show_header=True,
        header_style="bold cyan",
        expand=True,
    )
    tbl.add_column("METRIC", style="dim cyan")
    tbl.add_column("VALUE", style="bold bright_green")

    tbl.add_row("Total Questions", str(report.get("total_questions", 0)))
    tbl.add_row("Avg Lie Probability", f"{report.get('avg_lie_probability', 0):.1f}%")
    tbl.add_row("Max Lie Probability", f"{report.get('max_lie_probability', 0)}%")
    tbl.add_row("Deceptive Responses", str(report.get("deceptive_count", 0)))
    tbl.add_row("Truthful Responses", str(report.get("truthful_count", 0)))

    overall = report.get("overall_verdict", "ANALYSIS INCONCLUSIVE")
    ov_color = "bright_green" if overall == "SUBJECT CLEARED" else "red" if overall == "SUBJECT FLAGGED" else "yellow"
    tbl.add_row("OVERALL VERDICT", f"[{ov_color}]{overall}[/]")

    console.print(tbl)
    console.print()

    bsum = report.get("behavioral_summary", "")
    if bsum:
        console.print(Panel(Text(bsum, justify="full"), title="[cyan]AI FORENSIC BEHAVIORAL PROFILE[/]", border_style="cyan", expand=True))
        console.print()
        
    timeline = report.get("timeline", [])
    if timeline:
        t_tbl = Table(title="CONTRADICTION TIMELINE", border_style="yellow", expand=True)
        t_tbl.add_column("Q#", justify="right")
        t_tbl.add_column("Score")
        t_tbl.add_column("Verdict")
        
        for i, item in enumerate(timeline):
            s = item.get("score", {})
            t_tbl.add_row(
                str(i+1), 
                f"{s.get('lie_probability', 0)}pts", 
                s.get("verdict", "")
            )
        console.print(t_tbl)
        console.print()

    console.rule(style="green")
    console.print()
