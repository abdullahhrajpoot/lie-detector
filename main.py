try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import sys
import time
from rich.console import Console

console = Console()

def _boot_sequence():
    console.print("INITIALIZING POLYTRUTH KERNEL v5.0...")
    time.sleep(0.15)
    console.print()
    console.print("LOADING SUBSYSTEMS:")
    time.sleep(0.3)
    
    active_count = 0
    total = 6
    
    # Check 1: KEYSTROKE PSI SENSOR......... (always OK)
    console.print("  KEYSTROKE PSI SENSOR......... [bold bright_green][  OK  ][/]")
    active_count += 1
    time.sleep(0.1)

    # Check 2: LEXICAL TRAP ENGINE.......... (always OK)
    console.print("  LEXICAL TRAP ENGINE.......... [bold bright_green][  OK  ][/]")
    active_count += 1
    time.sleep(0.1)
    
    # Check 3: ANTHROPIC NEURAL CORE.........
    console.print("  GEMINI NEURAL CORE...........", end="")
    try:
        from ai_analyst import AI_AVAILABLE
        if AI_AVAILABLE:
            console.print(" [bold bright_green][  OK  ][/]")
            active_count += 1
        else:
            console.print(" [bold red][ FAIL ][/]")
    except Exception:
        console.print(" [bold red][ FAIL ][/]")
    time.sleep(0.1)

    # Check 4: ACOUSTIC STRESS SENSOR.......
    console.print("  ACOUSTIC STRESS SENSOR.......", end="")
    try:
        from voice_analyzer import VOICE_AVAILABLE
        if VOICE_AVAILABLE:
            console.print(" [bold bright_green][  OK  ][/]")
            active_count += 1
        else:
            console.print(" [bold red][ FAIL ][/]")
    except Exception:
        console.print(" [bold red][ FAIL ][/]")
    time.sleep(0.1)
    
    # Check 5: BIOMETRIC VISUAL FEED.........
    console.print("  BIOMETRIC VISUAL FEED........", end="")
    try:
        from face_tracker import FACE_AVAILABLE
        if FACE_AVAILABLE:
            console.print(" [bold bright_green][  OK  ][/]")
            active_count += 1
        else:
            console.print(" [bold red][ FAIL ][/]")
    except Exception:
        console.print(" [bold red][ FAIL ][/]")
    time.sleep(0.1)

    # Check 6: CONTRADICTION ENGINE..........
    console.print("  CONTRADICTION ENGINE......... [bold bright_green][  OK  ][/]")
    active_count += 1
    time.sleep(0.1)

    console.print()
    console.print(f"  [bold bright_green]ACTIVE SENSORS: {active_count}/{total}[/]")
    console.print("  [dim cyan]Degraded sensors fall back to simulation mode.[/]")
    
    try:
        from ai_analyst import AI_AVAILABLE
        if not AI_AVAILABLE:
            console.print("  [yellow]  \u25ba Set GEMINI_API_KEY env var (or run python setup_key.py) for AI analysis[/]")
    except Exception:
        pass
        
    console.print()
    console.print("  [bold red][WARNING] BEHAVIORAL DATA IS BEING RETAINED FOR ANALYSIS[/]")
    time.sleep(0.5)
    console.print("  [bold red][WARNING] SUBJECT HAS IMPLICITLY CONSENTED TO INTERROGATION[/]")
    time.sleep(0.8)
    console.print()

def main():
    _boot_sequence()
    from menu import run_menu
    run_menu()

if __name__ == "__main__":
    main()
