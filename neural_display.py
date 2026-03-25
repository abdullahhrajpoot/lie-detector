import random
import math
from rich.text import Text
from rich.style import Style

class NeuralDisplay:
    def __init__(self):
        pass

    def render(self, lie_score: int, frame: int, width: int, height: int) -> Text:
        # Base colors
        dim_color = "dark_green"
        active_color = "bright_red" if lie_score > 60 else "yellow" if lie_score > 35 else "green"
        
        # Calculate base activation probability based on lie_score (0.0 to 1.0)
        activation_prob = lie_score / 100.0
        
        # Modulate with a sine wave over the frame counter to make it "pulse"
        pulse = (math.sin(frame * 0.5) + 1) / 2 # 0.0 to 1.0
        current_threshold = 1.0 - (activation_prob * pulse)

        def get_node():
            if random.random() > current_threshold:
                return f"[{active_color}]●[/]"
            else:
                return f"[{dim_color}]○[/]"

        def get_conn():
            if random.random() > current_threshold:
                return f"[{active_color}]\u2500\u2500\u2500[/]"
            else:
                return f"[{dim_color}]\u2500\u2500\u2500[/]"

        # Build the exact visual requested
        t = Text()
        
        # Line 1
        t.append_text(Text.from_markup(f"  KSTROKE {get_conn()} {get_node()} {get_conn()} {get_node()} {get_conn()}\n"))
        # Line 2
        t.append_text(Text.from_markup(f"  VOICE   {get_conn()} {get_node()} {get_conn()} {get_node()} {get_conn()}  {get_node()} DECEPTION\n"))
        # Line 3
        t.append_text(Text.from_markup(f"  VISION  {get_conn()} {get_node()} {get_conn()} {get_node()} {get_conn()}    INDEX: {lie_score}%\n"))
        # Line 4
        t.append_text(Text.from_markup(f"  LEXICAL {get_conn()} {get_node()} {get_conn()} {get_node()} {get_conn()}\n"))
        
        return t
