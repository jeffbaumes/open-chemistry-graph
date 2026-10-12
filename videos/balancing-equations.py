"""Balancing H2 + O2 -> H2O by adding coefficients and counting atoms."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from manim import DOWN, LEFT, RIGHT, UP, Arrow, FadeIn, FadeOut, Indicate, Text  # noqa: E402

from lib import FONT, MUTED, TEXT, WRONG, LessonScene, equation, molecule, tally  # noqa: E402

ROW = UP * 0.55      # where the molecules sit
COUNTS = DOWN * 1.45  # where the atom tallies sit


class Lesson(LessonScene):
    def construct(self):
        self.title_card("Balancing chemical equations")

        eq = equation([(1, "H2"), (1, "O2")], [(1, "H2O")]).move_to(UP * 2.75)
        self.play(FadeIn(eq, shift=DOWN * 0.2), run_time=0.6)

        h2 = molecule("H2").move_to(LEFT * 4.7 + ROW)
        plus = Text("+", font=FONT, color=MUTED, font_size=44).move_to(LEFT * 3.35 + ROW)
        o2 = molecule("O2").move_to(LEFT * 2.0 + ROW)
        arrow = Arrow(LEFT * 0.7, RIGHT * 0.7, color=MUTED, buff=0, stroke_width=5).move_to(ROW)
        water = molecule("H2O").move_to(RIGHT * 3.35 + ROW)
        self.enter(h2, plus, o2, arrow, water)

        self.caption("Count the atoms on each side.")
        left_counts = {"H": 2, "O": 2}
        right_counts = {"H": 2, "O": 1}
        left = tally("Reactants", left_counts, right_counts).move_to(LEFT * 3.35 + COUNTS)
        right = tally("Products", right_counts, left_counts).move_to(RIGHT * 3.35 + COUNTS)
        self.enter(left, right)
        self.wait(1.6)

        self.caption("Oxygen does not match: 2 on the left, 1 on the right.")
        self.play(Indicate(left[2], color=WRONG), Indicate(right[2], color=WRONG))
        self.wait(2.3)

        self.caption("Never change a subscript. Add a coefficient instead.")
        self.wait(3)

        # A second water molecule fixes oxygen.
        water2 = molecule("H2O").move_to(RIGHT * 3.35 + ROW + DOWN * 0.6)
        eq2 = equation([(1, "H2"), (1, "O2")], [(2, "H2O")]).move_to(eq)
        right_counts = {"H": 4, "O": 2}
        left2 = tally("Reactants", left_counts, right_counts).move_to(left)
        right2 = tally("Products", right_counts, left_counts).move_to(right)
        self.swoosh()
        self.play(
            water.animate.shift(UP * 0.6), FadeIn(water2, shift=LEFT * 0.4),
            FadeOut(eq), FadeIn(eq2), FadeOut(left), FadeIn(left2), FadeOut(right), FadeIn(right2),
            run_time=0.9,
        )
        self.caption("Two water molecules. Oxygen balances, but now hydrogen is 2 and 4.")
        self.play(Indicate(left2[1], color=WRONG), Indicate(right2[1], color=WRONG))
        self.wait(2.3)

        # A second hydrogen molecule fixes hydrogen.
        h2b = molecule("H2").move_to(LEFT * 4.7 + ROW + DOWN * 0.45)
        eq3 = equation([(2, "H2"), (1, "O2")], [(2, "H2O")]).move_to(eq)
        left_counts = {"H": 4, "O": 2}
        left3 = tally("Reactants", left_counts, right_counts).move_to(left)
        right3 = tally("Products", right_counts, left_counts).move_to(right)
        self.swoosh()
        self.play(
            h2.animate.shift(UP * 0.45), FadeIn(h2b, shift=RIGHT * 0.4),
            FadeOut(eq2), FadeIn(eq3), FadeOut(left2), FadeIn(left3), FadeOut(right2), FadeIn(right3),
            run_time=0.9,
        )
        self.chime()
        self.caption("Balanced: 4 hydrogen atoms and 2 oxygen atoms on each side.")
        self.play(Indicate(eq3, color=TEXT, scale_factor=1.08))
        self.finish(hold=3.5)
