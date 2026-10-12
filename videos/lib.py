"""Shared toolkit for lesson videos. Every video builds on LessonScene so they
share one look, one set of element colors and one (quiet) sound palette.
See videos/README.md.
"""
import re
import tomllib
import wave
from pathlib import Path

import numpy as np
from manim import (
    BOLD, DOWN, LEFT, UP, WHITE, BLACK,
    Circle, FadeIn, FadeOut, LaggedStart, Line, MarkupText, Scene, Text, VGroup,
)

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "videos" / ".cache"

# Colors come from the same files the site uses, so a video can never drift
# from the pages around it.
_css = (ROOT / "src" / "styles" / "site.css").read_text().split("@media")[0]
TOKENS = dict(re.findall(r"--([\w-]+):\s*(#[0-9a-fA-F]{6})", _css))
ELEMENT_COLORS = tomllib.loads((ROOT / "conventions" / "elements.toml").read_text())["color"]

BG, TEXT, MUTED = TOKENS["bg"], TOKENS["text"], TOKENS["muted"]
ACCENT, CORRECT, WRONG = TOKENS["accent"], TOKENS["correct"], TOKENS["wrong"]
FONT = "Palatino"
UI_FONT = "Helvetica Neue"


# --- Chemistry drawing -------------------------------------------------------

def color_of(symbol):
    return ELEMENT_COLORS.get(symbol, ELEMENT_COLORS["default"])


def atom(symbol, radius=0.34):
    """An atom as a labelled circle in its element's color."""
    circle = Circle(radius=radius, color=TEXT, stroke_width=1.5, fill_color=color_of(symbol), fill_opacity=1)
    label = Text(symbol, font=UI_FONT, weight=BOLD, color=WHITE, font_size=radius * 70)
    label.set_stroke(BLACK, width=2.5, opacity=0.5, background=True)
    return VGroup(circle, label)


# Where each atom sits, in units of one atom radius. Add a molecule here to use it.
LAYOUTS = {
    "H2": [("H", (-0.8, 0)), ("H", (0.8, 0))],
    "O2": [("O", (-0.85, 0)), ("O", (0.85, 0))],
    "N2": [("N", (-0.85, 0)), ("N", (0.85, 0))],
    "H2O": [("H", (-1.25, -0.8)), ("H", (1.25, -0.8)), ("O", (0, 0.15))],
    "CO2": [("O", (-1.7, 0)), ("O", (1.7, 0)), ("C", (0, 0))],
    "NH3": [("H", (-1.3, -0.8)), ("H", (1.3, -0.8)), ("H", (0, -1.4)), ("N", (0, 0.1))],
    "CH4": [("H", (-1.3, 0.8)), ("H", (1.3, 0.8)), ("H", (-1.3, -0.8)), ("H", (1.3, -0.8)), ("C", (0, 0))],
}


def molecule(formula, radius=0.34):
    """A space-filling drawing of a molecule listed in LAYOUTS."""
    parts = VGroup()
    for symbol, (x, y) in LAYOUTS[formula]:
        parts.add(atom(symbol, radius).move_to([x * radius, y * radius, 0]))
    return parts


def chem(text):
    """Pango markup for a formula: digits after a symbol become subscripts."""
    # Pango's own <sub> is too small to read on video, so size and drop it by hand.
    return re.sub(r"(?<=[A-Za-z)])(\d+)", r'<span font_size="62%" baseline_shift="subscript">\1</span>', text)


def equation(reactants, products, font_size=64):
    """A typeset equation from [(coefficient, formula), ...] for each side.
    Coefficients above 1 are shown in the accent color."""
    def term(coefficient, formula):
        lead = f'<span fgcolor="{ACCENT}">{coefficient}</span> ' if coefficient > 1 else ""
        return lead + chem(formula)

    sides = [" + ".join(term(*t) for t in side) for side in (reactants, products)]
    return MarkupText(" → ".join(sides), font=FONT, color=TEXT, font_size=font_size)


def tally(title, counts, other):
    """Atom counts for one side of an equation. A count is green when it
    matches the other side and red when it does not."""
    rows = VGroup(Text(title.upper(), font=UI_FONT, color=MUTED, font_size=20))
    for symbol, n in counts.items():
        color = CORRECT if other.get(symbol) == n else WRONG
        count = Text(f"{symbol}   {n}", font=UI_FONT, weight=BOLD, color=color, font_size=34)
        rows.add(VGroup(atom(symbol, 0.17), count).arrange(buff=0.25))
    return rows.arrange(DOWN, buff=0.22)


# --- Sound -------------------------------------------------------------------
# All audio is synthesized here, so there is nothing to download or license.
# Keep it quiet: these levels are deliberately low.

RATE = 44100


def _save(name, samples):
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / f"{name}.wav"
    with wave.open(str(path), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(RATE)
        f.writeframes((np.clip(samples, -1, 1) * 32767).astype(np.int16).tobytes())
    return str(path)


def swoosh(seconds=0.45, level=0.06):
    """Soft filtered noise that rises and falls, for things entering."""
    n = int(RATE * seconds)
    noise = np.random.default_rng(1).standard_normal(n)
    position = np.linspace(0, 1, n)
    cutoff = 300 + 2600 * np.sin(np.pi * position)  # Hz, sweeping up then down
    alpha = 1 - np.exp(-2 * np.pi * cutoff / RATE)
    out = np.zeros(n)
    value = 0.0
    for i in range(n):  # one-pole low-pass with a moving cutoff
        value += alpha[i] * (noise[i] - value)
        out[i] = value
    return _save("swoosh", level * out / np.abs(out).max() * np.sin(np.pi * position) ** 2)


def chime(seconds=1.2, level=0.08):
    """Two soft sine tones a fifth apart, for a result."""
    t = np.arange(int(RATE * seconds)) / RATE
    tone = np.sin(2 * np.pi * 784 * t) + 0.6 * np.sin(2 * np.pi * 1175 * t)
    attack = np.minimum(t / 0.01, 1)
    return _save("chime", level * tone / 1.6 * attack * np.exp(-4 * t))


def pad(seconds, level=0.022):
    """A barely-there sustained chord under the whole video."""
    t = np.arange(int(RATE * seconds)) / RATE
    notes = [196.00, 293.66, 392.00, 493.88]  # G, D, G, B
    chord = sum(np.sin(2 * np.pi * f * t) * (0.75 + 0.25 * np.sin(2 * np.pi * (0.07 + 0.03 * i) * t)) for i, f in enumerate(notes))
    fade = np.minimum(t / 2, 1) * np.minimum((seconds - t) / 2.5, 1)
    return _save("pad", level * chord / len(notes) * fade)


# --- Scene -------------------------------------------------------------------

class LessonScene(Scene):
    """Base class for lesson videos: title card, captions, entrances, sound."""

    def setup(self):
        self.camera.background_color = BG
        self._caption = None

    def title_card(self, title, hold=2.2):
        # Shown from the very first frame, so the video's preview is the title.
        heading = Text(title, font=FONT, weight=BOLD, color=TEXT, font_size=54)
        rule = Line(heading.get_left(), heading.get_right(), color=TEXT, stroke_width=3).next_to(heading, DOWN, buff=0.3)
        kicker = Text("OPEN CHEMISTRY GRAPH", font=UI_FONT, color=MUTED, font_size=20).next_to(heading, UP, buff=0.5)
        card = VGroup(kicker, heading, rule)
        self.add(card)
        self.wait(hold)
        self.play(FadeOut(card, shift=UP * 0.3), run_time=0.6)

    def enter(self, *mobjects, shift=UP * 0.25, run_time=0.7):
        """Bring things on screen with a soft swoosh."""
        self.swoosh()
        self.play(LaggedStart(*[FadeIn(m, shift=shift) for m in mobjects], lag_ratio=0.2), run_time=run_time)

    def caption(self, text):
        """Replace the line of narration at the bottom of the frame."""
        new = MarkupText(text, font=FONT, color=TEXT, font_size=32).move_to(DOWN * 3.15)
        animations = [FadeIn(new, shift=UP * 0.15)]
        if self._caption:
            animations.append(FadeOut(self._caption, shift=UP * 0.15))
        self.play(*animations, run_time=0.5)
        self._caption = new

    def swoosh(self):
        self.add_sound(swoosh())

    def chime(self):
        self.add_sound(chime())

    def finish(self, hold=2.5):
        """Hold the last frame, fade out, and lay the pad under everything."""
        self.wait(hold)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.8)
        self.add_sound(pad(self.renderer.time), time_offset=-self.renderer.time)
