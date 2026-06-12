from manim import *

# Compatibility layer for LLM-hallucinated colors and classes
BROWN = "#8B4513"
SANDY_BROWN = "#F4A460"
MAGENTA = "#FF00FF"
CYAN = "#00FFFF"
DARK_GRAY = "#A9A9A9"
LIGHT_GRAY = "#D3D3D3"
PINK = "#FFC0CB"
LIME = "#00FF00"
MAROON = "#800000"
NAVY = "#000080"
OLIVE = "#808000"

class BulletList(VGroup):
    def __init__(self, *items, **kwargs):
        line_spacing = kwargs.pop('line_spacing', 0.5)
        dot = '• '
        mobjects = [Text(f'{dot}{item}', **kwargs) for item in items]
        super().__init__(*mobjects)
        self.arrange(DOWN, aligned_edge=LEFT, buff=line_spacing)

def Capsule(**kwargs):
    width = kwargs.pop('width', 2)
    height = kwargs.pop('height', 1)
    return RoundedRectangle(corner_radius=min(width, height)/2, width=width, height=height, **kwargs)

# Legacy Compatibility for common LLM hallucinations
TextMobject = Text
TexMobject = Tex
ShowCreation = Create
ApplyMethod = lambda m, *args, **kwargs: m.animate.method(*args, **kwargs) if hasattr(m, 'animate') else m

# Monkey-patch Line to prevent crashes on hallucinated .bend() method
Line.bend = lambda self, *args, **kwargs: self
Mobject.set_color_by_gradient = lambda self, *args, **kwargs: self


class MainScene(Scene):
    def construct(self):
        self.show_intro()
        self.show_fraction()
        self.show_decimal()
        self.show_percentage()
        self.show_summary_table()

    def show_intro(self):
        title = Text("Fractions, Decimals, & Percentages", font_size=40)
        subtitle = Text("Three ways to show the same value", font_size=28, color=GRAY)
        intro_group = VGroup(title, subtitle).arrange(DOWN, buff=0.5)
        
        self.play(Write(title))
        self.play(FadeIn(subtitle, shift=DOWN))
        self.wait(2)
        self.play(FadeOut(intro_group))

    def show_fraction(self):
        # Title
        sec_title = Text("1. Fractions (Parts of a Whole)", font_size=32, color=BLUE).to_edge(UP)
        self.play(Write(sec_title))
        
        # Create 4 boxes side-by-side
        boxes = VGroup(*[Square(side_length=1.5, stroke_color=WHITE) for _ in range(4)]).arrange(RIGHT, buff=0)
        boxes.move_to(ORIGIN).shift(UP * 0.5)
        self.play(Create(boxes))
        self.wait(0.5)
        
        # Highlight 3 boxes
        highlighted = VGroup(*[Square(side_length=1.5, fill_color=BLUE, fill_opacity=0.6, stroke_color=WHITE) for _ in range(3)]).arrange(RIGHT, buff=0)
        highlighted.move_to(boxes.get_left(), aligned_edge=LEFT)
        self.play(FadeIn(highlighted))
        self.wait(1)
        
        # Label the fraction
        fraction_tex = MathTex(r"\frac{3}{4}", font_size=60).next_to(boxes, DOWN, buff=0.8)
        
        # Label descriptions
        frac_explanation = VGroup(
            Text("Numerator (parts we have): 3", font_size=24, color=BLUE),
            Text("Denominator (total parts): 4", font_size=24, color=WHITE)
        ).arrange(DOWN, aligned_edge=LEFT).next_to(fraction_tex, RIGHT, buff=1.5)
        
        self.play(Write(fraction_tex))
        self.play(FadeIn(frac_explanation, shift=RIGHT))
        self.wait(2.5)
        
        # Transition out of elements but keep/move the fraction
        self.play(
            FadeOut(sec_title),
            FadeOut(boxes),
            FadeOut(highlighted),
            FadeOut(frac_explanation),
            fraction_tex.animate.to_edge(LEFT, buff=1.5).shift(UP * 1.5)
        )
        self.current_fraction = fraction_tex

    def show_decimal(self):
        sec_title = Text("2. Decimals (Base-10 Representation)", font_size=32, color=GREEN).to_edge(UP)
        self.play(Write(sec_title))
        
        # Setup target aligned layout to avoid nested VGroup animation bugs
        division_tex = MathTex(r"= 3 \div 4", font_size=60)
        decimal_tex = MathTex(r"= 0.75", font_size=60, color=GREEN)
        
        eq_group = VGroup(self.current_fraction, division_tex, decimal_tex).arrange(RIGHT, buff=0.5).move_to(UP * 1.5)
        
        self.play(
            self.current_fraction.animate.move_to(eq_group[0].get_center()),
            Write(division_tex)
        )
        self.wait(1)
        
        self.play(Write(decimal_tex))
        self.wait(1)
        
        # Place value explanation
        explanation = VGroup(
            MathTex(r"0.75 = \frac{7}{10} + \frac{5}{100}", font_size=36),
            Text("0.75 represents 75 hundredths", font_size=24, color=GREEN)
        ).arrange(DOWN, buff=0.4).shift(DOWN * 1.5)
        
        self.play(FadeIn(explanation, shift=UP))
        self.wait(2.5)
        
        # Transition to consolidate representations
        combo_tex = MathTex(r"\frac{3}{4} = 0.75", font_size=60).move_to(UP * 1.5)
        self.play(
            FadeOut(sec_title),
            FadeOut(division_tex),
            FadeOut(explanation),
            ReplacementTransform(VGroup(self.current_fraction, decimal_tex), combo_tex)
        )
        self.combo_tex = combo_tex
        self.wait(1)

    def show_percentage(self):
        sec_title = Text("3. Percentages (Out of 100)", font_size=32, color=ORANGE).to_edge(UP)
        self.play(Write(sec_title))
        
        # Calculation demonstration
        calc_tex = MathTex(r"0.75 \times 100\%", font_size=54).next_to(self.combo_tex, DOWN, buff=1.0)
        self.play(Write(calc_tex))
        self.wait(1)
        
        percent_tex = MathTex(r"= 75\%", font_size=60, color=ORANGE).next_to(calc_tex, RIGHT, buff=0.5)
        self.play(Write(percent_tex))
        self.wait(1.5)
        
        explanation = Text('"Percent" literally means "per 100"', font_size=24, color=GRAY).next_to(percent_tex, DOWN, buff=0.8).align_to(calc_tex, LEFT)
        self.play(FadeIn(explanation))
        self.wait(2.5)
        
        # Clear everything for final summary
        self.play(
            FadeOut(sec_title),
            FadeOut(self.combo_tex),
            FadeOut(calc_tex),
            FadeOut(percent_tex),
            FadeOut(explanation)
        )

    def show_summary_table(self):
        sec_title = Text("Equivalence Chart", font_size=32, color=YELLOW).to_edge(UP)
        self.play(Write(sec_title))
        
        # Construct header columns
        headers = VGroup(
            Text("Fraction", font_size=28, color=BLUE),
            Text("Decimal", font_size=28, color=GREEN),
            Text("Percentage", font_size=28, color=ORANGE)
        ).arrange(RIGHT, buff=1.5).shift(UP * 1.2)
        
        # Horizontal divider
        line = Line(start=[-5, 0.8, 0], end=[5, 0.8, 0], stroke_width=2, color=WHITE)
        
        self.play(Write(headers), Create(line))
        self.wait(0.5)
        
        # Rows containing equivalences
        rows = [
            (r"\frac{1}{2}", "0.5", "50\%"),
            (r"\frac{1}{4}", "0.25", "25\%"),
            (r"\frac{3}{4}", "0.75", "75\%"),
            (r"\frac{1}{10}", "0.1", "10\%"),
        ]
        
        row_groups = []
        for i, (frac, dec, perc) in enumerate(rows):
            f_m = MathTex(frac, font_size=32, color=BLUE)
            d_m = MathTex(dec, font_size=32, color=GREEN)
            p_m = MathTex(perc, font_size=32, color=ORANGE)
            
            # Position manually relative to headers
            f_m.move_to([headers[0].get_x(), 0.2 - i * 0.8, 0])
            d_m.move_to([headers[1].get_x(), 0.2 - i * 0.8, 0])
            p_m.move_to([headers[2].get_x(), 0.2 - i * 0.8, 0])
            
            row_groups.append(VGroup(f_m, d_m, p_m))
        
        for row in row_groups:
            self.play(FadeIn(row, shift=UP * 0.1), run_time=0.5)
            self.wait(0.2)
            
        self.wait(3.5)
        
        # Final cleanup using list comprehension instead of VGroup packaging to safely handle all mobjects
        self.play(*[FadeOut(m) for m in self.mobjects])