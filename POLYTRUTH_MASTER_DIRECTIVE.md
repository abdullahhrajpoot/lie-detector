# POLYTRUTH v5.0 — MASTER CODING DIRECTIVE (NUKE PROMPT)

This file is the canonical project directive for all contributors and AI agents.
Cursor loads a summary from `.cursor/rules/polytruth-v5-master-directive.mdc` (`alwaysApply: true`).

**Companion docs:** `documentation_and_working.txt` (architecture, dataset, research comparison).

---

## Compliance checklist (codebase must satisfy)

| Requirement | Location |
|-------------|----------|
| All thresholds | `scoring.py` constants only |
| Web typing (no random) | `analyzer.analysis_from_web_metrics()` |
| Voice stress caps/thresholds | `voice_analyzer.compute_voice_stress()` imports `scoring` |
| Face stress caps/thresholds | `face_tracker.compute_face_stress()` imports `scoring` |
| AI delta clamp [-15, +35] | `LieScorer.clamp_ai_delta()` + `ai_analyst.py` |
| ARM camera | `FaceTracker.start()` |
| DISARM camera | `FaceTracker.stop()` |
| ARM mic | `VoiceAnalyzer.start_recording()` |
| DISARM mic | `VoiceAnalyzer.stop_monitoring()` |
| Binary verdict ≤50 / >50 | `LieScorer.verdict_from_score()` |
| Min 15 words before score | `MIN_ANSWER_WORDS` in `scoring.py` |
| Session history fields | `gui.py` append with timestamp |
| No INCONCLUSIVE verdict | Removed from scorer + UI defaults |
| Cosmetic biomarkers | `gui_template.html` / sensor loop — not scored |

---

## Verdict policy

- `lie_probability <= 50` → **TRUTHFUL**
- `lie_probability > 50` → **DECEPTIVE**
- Session: **SUBJECT CLEARED** if avg ≤ 50 and zero DECEPTIVE; else **SUBJECT FLAGGED**

---

## Scoring constants (do not drift — edit only `scoring.py`)

See `scoring.py` for: `VERDICT_THRESHOLD`, `BASE_SCORE`, `COGNITIVE_DELAY_*`, `WPM_*`,
`BURST_VOLATILITY_*`, `BACKSPACE_*`, `MIN_WORDS_EVASIVE`, `MIN_ANSWER_WORDS`,
`AI_DELTA_MIN/MAX`, `VOICE_*`, `FACE_*`, `CONTRADICTION_POINTS`.

---

## Research grounding (do not invent citations)

- **Keystroke / delay / WPM / volatility:** Zuckerman et al. (1981); DePaulo et al. (2003);
  Banerjee et al. EMNLP 2014; Monaro et al. Sci Rep 2018; Tomas et al. ACP 2021;
  Grimes et al. ACM TMIS 2013; Brennan et al. ACP 2025.
- **Unexpected questions:** Vrij et al. (2009) L&HB; Melis et al. (2024) Sci Rep + OSF r5z67;
  Monaro et al. (2020); Warmelink et al. (2019).
- **Follow-ups:** Cognitive Load Approach (Vrij 2008); SUE (Hartwig et al. 2007); SVA empathy
  probes (Steller & Köhnken 1989).
- **Lexical rules:** DePaulo (2003); Hauch meta-analysis (2015); CBCA overview Vrij (2022 PMC).
- **Voice:** Fatma et al. (2024); VSA near-chance reviews — coarse heuristics only here.
- **Face:** Gallardo-Antolín MDPI 2021; gaze aversion weak (DePaulo 2003) — no pupilometry.
- **Contradiction:** Vrij & Granhag (2012); Buller & Burgoon (1996) IDT.
- **AI overlay:** Pérez-Rosas Sci Rep 2023; Adkins Frontiers AI 2025.

---

## Honesty (never claim in code)

- No “X% accuracy”, “clinically validated”, “forensic certification”, “polygraph equivalent”
- Sidebar HR/RR/SC/biomarkers are **simulated visuals**, not LieScorer inputs
- Rule-based demonstration — accuracy not claimed

---

## Full NUKE PROMPT text

The complete directive (§SYSTEM IDENTITY through §WHEN IN DOUBT) is the message
titled **“POLYTRUTH v5.0 — MASTER CODING DIRECTIVE (NUKE PROMPT)”** in the project
owner’s specification. If this file and the codebase diverge, **scoring.py + the
NUKE PROMPT win**; update code to match.

For the expanded operational guide (modes, dataset, prior-work comparison, debug trace),
see **`documentation_and_working.txt`**.
