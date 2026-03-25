"""
menu.py — POLYTRUTH v5.0
Main menu routing and shutdown sequence.
"""

import sys
import time

from rich.console import Console
from rich.panel import Panel
from rich.text import Text

import ui
from session import Session

console = Console()

# ─────────────────────────────────────────────────────────────
# ASCII Title Art
# ─────────────────────────────────────────────────────────────
_TITLE = r"""
  ██████╗  ██████╗ ██╗  ██╗   ██╗████████╗██████╗ ██╗   ██╗████████╗██╗  ██╗
  ██╔══██╗██╔═══██╗██║  ╚██╗ ██╔╝╚══██╔══╝██╔══██╗██║   ██║╚══██╔══╝██║  ██║
  ██████╔╝██║   ██║██║   ╚████╔╝    ██║   ██████╔╝██║   ██║   ██║   ███████║
  ██╔═══╝ ██║   ██║██║    ╚██╔╝     ██║   ██╔══██╗██║   ██║   ██║   ██╔══██║
  ██║     ╚██████╔╝███████╗██║      ██║   ██║  ██║╚██████╔╝   ██║   ██║  ██║
  ╚═╝      ╚═════╝ ╚══════╝╚═╝      ╚═╝   ╚═╝  ╚═╝ ╚═════╝    ╚═╝   ╚═╝  ╚═╝
"""

_SUBTITLE = "v5.0 // BEHAVIORAL INTERROGATION SYSTEM // CLASSIFIED"

_MENU_OPTIONS = """
  ┌─────────────────────────────────────────────────────────────────┐
  │                    SELECT OPERATING MODE                        │
  ├───────────┬─────────────────────────────────────────────────────┤
  │    [1]    │  HONESTY TEST         — Full profiling (6 questions)│
  │    [2]    │  INTERROGATION MODE   — Adaptive follow-up branching│
  │    [3]    │  FRIEND TEST          — 2-player custom question     │
  │    [4]    │  SINGLE QUESTION      — Rapid baseline verification  │
  ├───────────┼─────────────────────────────────────────────────────┤
  │    [0]    │  DISMOUNT & EXIT      — Terminate connection         │
  └───────────┴─────────────────────────────────────────────────────┘
"""


def _show_menu_overlay():
    """Print the title art and menu over the stopped dashboard."""
    console.clear()
    console.print(Text(_TITLE, style="bold bright_green"))
    console.print(Text(f"  {_SUBTITLE}\n", style="dim cyan"))
    console.print(
        Panel(
            Text(_MENU_OPTIONS, style="bright_green"),
            border_style="green",
            expand=True,
        )
    )
    console.print()


def _shutdown_sequence():
    console.print()
    _steps = [
        ("DISMOUNTING DRIVES...", 0.4),
        ("PURGING SESSION CACHE...", 0.35),
        ("SEVERING BIOMETRIC LINKS...", 0.4),
        ("ZEROING KEYSTROKE BUFFER...", 0.3),
        ("SANITIZING MEMORY...", 0.35),
        ("CONNECTION TERMINATED.", 0.5),
    ]
    for msg, delay in _steps:
        console.print(f"  [bold red]{msg}[/]")
        time.sleep(delay)
    console.print()
    console.print("[bold bright_green]  POLYTRUTH SESSION ENDED.[/]")
    console.print()
    sys.exit(0)


def run_menu():
    """Main menu loop. Starts dashboard, shows menu, routes to sessions."""
    # Initial state for dashboard
    initial_state = {
        "mode": 0,
        "questions_asked": 0,
        "avg_lie_prob": 0.0,
        "deceptive_count": 0,
        "truthful_count": 0,
        "status": "AWAITING SUBJECT",
        "scores": [],
    }

    while True:
        # Start dashboard (or restart it after a session)
        ui.start_dashboard(initial_state)
        time.sleep(0.8)

        # Stop dashboard to show menu
        ui.stop_dashboard()
        _show_menu_overlay()

        try:
            choice = input("  ENTER SELECTION >>> ").strip()
        except (KeyboardInterrupt, EOFError):
            ui.stop_dashboard()
            _shutdown_sequence()

        if choice == "0":
            _shutdown_sequence()
        elif choice in ("1", "2", "3", "4"):
            mode = int(choice)
            # Reset session sub-state
            initial_state = {
                "mode": mode,
                "questions_asked": 0,
                "avg_lie_prob": 0.0,
                "deceptive_count": 0,
                "truthful_count": 0,
                "status": "SESSION ACTIVE",
                "scores": [],
            }
            # Start dashboard for the session
            ui.start_dashboard(initial_state)
            try:
                sess = Session(mode)
                sess.run()
            except Exception as exc:
                ui.stop_dashboard()
                console.print(f"\n[red]Session error: {exc}[/]")
                time.sleep(2)
            # Reset state for next menu display
            initial_state = {
                "mode": 0,
                "questions_asked": 0,
                "avg_lie_prob": 0.0,
                "deceptive_count": 0,
                "truthful_count": 0,
                "status": "AWAITING SUBJECT",
                "scores": [],
            }
        else:
            ui.stop_dashboard()
            console.print("  [yellow]Invalid selection. Try 0-4.[/]")
            time.sleep(1)
