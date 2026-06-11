from manim import *

# Compatibility layer for potential missing constants or legacy methods
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

# Legacy Compatibility for common migration needs
TextMobject = Text
TexMobject = Tex
ShowCreation = Create

class MainScene(Scene):
    def construct(self):
        self.intro_section()
        self.error_explanation()
        self.solution_demonstration()
        self.animation_best_practices()
        self.final_summary()

    def intro_section(self):
        title = Text("Manim Syntax Mastery", color=BLUE).scale(1.2)
        subtitle = Text("Fixing NameErrors & TypeErrors", color=GRAY).scale(0.8)
        subtitle.next_to(title, DOWN)
        
        self.play(Write(title))
        self.play(FadeIn(subtitle, shift=UP))
        self.wait(2)
        self.play(FadeOut(title), FadeOut(subtitle))

    def error_explanation(self):
        error_msg = Text("The Error:", color=RED).to_edge(UP)
        
        # We display the broken code as text to explain why it failed
        code_wrong = Paragraph(
            '# This fails in Manim Community:',
            'line = Line(LEFT, RIGHT)',
            'line.set_stroke(style=DASHED) # NameError',
            'dashed = DashedLine(radius=1) # TypeError',
            alignment="left",
            font_size=24
        ).set_color(WHITE).shift(UP * 0.5)
        
        explanation = Text(
            "DASHED is not a constant, and Lines don't have a radius.",
            font_size=24,
            color=YELLOW
        ).next_to(code_wrong, DOWN, buff=1)

        self.play(Write(error_msg))
        self.play(FadeIn(code_wrong))
        self.wait(1)
        self.play(Write(explanation))
        self.wait(3)
        
        self.play(FadeOut(error_msg), FadeOut(code_wrong), FadeOut(explanation))

    def solution_demonstration(self):
        solution_title = Text("The Solution: Specialized Classes", color=GREEN).to_edge(UP)
        
        code_right = Paragraph(
            '# Use DashedLine for linear segments',
            'line = DashedLine(LEFT, RIGHT)',
            '# Use DashedVMobject for other shapes',
            'circle = DashedVMobject(Circle(radius=1))',
            alignment="left",
            font_size=24
        ).shift(UP * 1.5)

        # Visual example
        start_point = LEFT * 3
        end_point = RIGHT * 3
        
        standard_line = Line(start_point + UP, end_point + UP, color=GRAY)
        label_std = Text("Standard Line", font_size=20).next_to(standard_line, LEFT)
        
        dashed_line = DashedLine(start_point + DOWN, end_point + DOWN, color=BLUE)
        label_dash = Text("Dashed Line", font_size=20).next_to(dashed_line, LEFT)

        self.play(Write(solution_title))
        self.play(FadeIn(code_right))
        self.wait(1)
        
        self.play(Create(standard_line), Write(label_std))
        self.play(Create(dashed_line), Write(label_dash))
        self.wait(2)
        
        self.play(Indicate(dashed_line))
        self.wait(1)
        
        self.play(
            FadeOut(solution_title), 
            FadeOut(code_right), 
            FadeOut(standard_line), 
            FadeOut(label_std),
            FadeOut(dashed_line),
            FadeOut(label_dash)
        )

    def animation_best_practices(self):
        header = Text("Dashed Shapes & .animate", color=GOLD).to_edge(UP)
        
        circle = Circle(radius=1, color=PURPLE).shift(LEFT * 2)
        square = Square(side_length=2, color=ORANGE).shift(RIGHT * 2)
        
        label_circle = Text("Circle", font_size=24).next_to(circle, DOWN)
        label_square = Text("Square", font_size=24).next_to(square, DOWN)

        self.play(Write(header))
        self.play(Create(circle), Create(square), Write(label_circle), Write(label_square))
        self.wait(1)

        # Demonstrating .animate syntax
        self.play(
            circle.animate.shift(UP).set_fill(PURPLE, opacity=0.5),
            square.animate.rotate(PI/4).scale(0.5),
            run_time=2
        )
        self.wait(1)
        
        # Creating a dashed version of a complex shape
        dashed_circle_mobject = DashedVMobject(Circle(radius=1.5, color=TEAL), num_dashes=30)
        
        self.play(
            ReplacementTransform(circle, dashed_circle_mobject),
            square.animate.shift(DOWN).set_color(RED),
            FadeOut(label_circle),
            FadeOut(label_square)
        )
        self.wait(2)

        # Clean cleanup
        self.play(*[FadeOut(mob) for mob in self.mobjects])

    def final_summary(self):
        summary_title = Text("Key Takeaways", color=BLUE).scale(1.2)
        self.play(Write(summary_title))
        self.wait(1)
        self.play(summary_title.animate.to_edge(UP))

        points = BulletList(
            "Use 'DashedLine' instead of 'DASHED' constant.",
            "Use 'DashedVMobject' to dash complex shapes.",
            "Check parameter names (e.g., Line has no 'radius').",
            "Prefer '.animate' for property changes.",
            font_size=28
        ).shift(DOWN * 0.5)

        for point in points:
            self.play(FadeIn(point, shift=RIGHT))
            self.wait(0.5)

        self.wait(3)
        self.play(FadeOut(VGroup(*self.mobjects)))