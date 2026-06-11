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
        self.intro_section()
        self.grid_section()
        self.formula_section()

    def intro_section(self):
        # Title of the lesson
        title = Text("What is Area?", font_size=44, color=BLUE)
        self.play(Write(title))
        self.wait(1.5)
        self.play(title.animate.to_edge(UP).scale(0.8))

        # Show 1D Line (Length)
        line = Line(start=LEFT * 2.5 + DOWN * 0.5, end=RIGHT * 2.5 + DOWN * 0.5, stroke_width=6, color=YELLOW)
        line_label = Text("1D: Length (1 dimension)", font_size=24).next_to(line, UP)

        self.play(Create(line), Write(line_label))
        self.wait(1.5)

        # Transition from 1D Line to 2D Area
        square = Square(side_length=3, stroke_color=WHITE).shift(DOWN * 0.5)
        square_fill = Square(side_length=3, stroke_width=0, fill_color=BLUE, fill_opacity=0.4).shift(DOWN * 0.5)
        square_label = Text("2D: Area (2 dimensions)", font_size=24).next_to(square, UP)

        self.play(
            ReplacementTransform(line, square),
            ReplacementTransform(line_label, square_label)
        )
        self.play(FadeIn(square_fill))
        self.wait(2)

        # Clear screen for next section
        self.play(FadeOut(square), FadeOut(square_fill), FadeOut(square_label), FadeOut(title))
        self.wait(0.5)

    def grid_section(self):
        # Section Title
        title_grid = Text("Measuring Area with Unit Squares", font_size=36, color=BLUE).to_edge(UP)
        self.play(Write(title_grid))

        # Create the grid manually for complete layout control
        grid_group = VGroup()
        grid_fill_group = VGroup()
        labels_group = VGroup()

        counter = 1
        for r in range(3):  # 3 rows
            for c in range(4):  # 4 columns
                # Calculate absolute coordinates to center the 4x3 grid
                x = c - 1.5
                y = r - 1.0 - 0.5  # Positioned slightly downwards
                
                # Grid outline
                sq = Square(side_length=1.0, stroke_color=WHITE, stroke_width=2)
                sq.move_to(np.array([x, y, 0]))
                
                # Fill layer to animate later
                sq_fill = Square(side_length=1.0, stroke_width=0, fill_color=GREEN, fill_opacity=0.0)
                sq_fill.move_to(np.array([x, y, 0]))
                
                # Unit count label
                lbl = Text(str(counter), font_size=20).move_to(sq.get_center())

                grid_group.add(sq)
                grid_fill_group.add(sq_fill)
                labels_group.add(lbl)
                counter += 1

        self.play(Create(grid_group))
        self.wait(1)

        # Conceptual explanation
        unit_desc = Text("We count how many 1x1 unit squares fit inside.", font_size=22, color=YELLOW).next_to(grid_group, DOWN, buff=0.5)
        self.play(Write(unit_desc))
        self.wait(1.5)

        # Animate the unit-by-unit grid filling and counting
        for i in range(12):
            self.play(
                grid_fill_group[i].animate.set_fill(GREEN, opacity=0.5),
                Write(labels_group[i]),
                run_time=0.2
            )

        # State the total visual area
        total_text = Text("Total Area = 12 Square Units", font_size=28, color=GREEN).next_to(unit_desc, DOWN, buff=0.3)
        self.play(Write(total_text))
        self.wait(2)

        # Clean transition
        self.play(
            FadeOut(grid_group),
            FadeOut(grid_fill_group),
            FadeOut(labels_group),
            FadeOut(unit_desc),
            FadeOut(total_text),
            FadeOut(title_grid)
        )
        self.wait(0.5)

    def formula_section(self):
        # Section Title
        title_formula = Text("The Area Formula", font_size=36, color=BLUE).to_edge(UP)
        self.play(Write(title_formula))

        # Define a geometric rectangle
        rect_width = 4.0
        rect_height = 3.0
        rect = Rectangle(width=rect_width, height=rect_height, stroke_color=WHITE, stroke_width=3).shift(DOWN * 0.5)
        rect_fill = Rectangle(width=rect_width, height=rect_height, stroke_width=0, fill_color=PURPLE, fill_opacity=0.3).shift(DOWN * 0.5)

        self.play(Create(rect), FadeIn(rect_fill))
        self.wait(1)

        # Width indicator arrow and label
        width_arrow = DoubleArrow(
            start=rect.get_corner(DL) + DOWN * 0.3,
            end=rect.get_corner(DR) + DOWN * 0.3,
            buff=0,
            stroke_width=3,
            color=YELLOW
        )
        width_label = Text("width = 4", font_size=24, color=YELLOW).next_to(width_arrow, DOWN, buff=0.1)

        # Height indicator arrow and label
        height_arrow = DoubleArrow(
            start=rect.get_corner(DR) + RIGHT * 0.3,
            end=rect.get_corner(UR) + RIGHT * 0.3,
            buff=0,
            stroke_width=3,
            color=ORANGE
        )
        height_label = Text("height = 3", font_size=24, color=ORANGE).next_to(height_arrow, RIGHT, buff=0.1)

        self.play(
            Create(width_arrow),
            Write(width_label),
            Create(height_arrow),
            Write(height_label)
        )
        self.wait(1.5)

        # Standard Area Formula
        formula_text = MathTex(
            r"\text{Area} = \text{width} \times \text{height}",
            font_size=36
        ).to_edge(DOWN, buff=0.6)

        self.play(Write(formula_text))
        self.wait(1.5)

        # Substitute dimensions into formula
        calc_text = MathTex(
            r"\text{Area} = 4 \times 3 = 12",
            font_size=36
        ).move_to(formula_text.get_center())

        self.play(ReplacementTransform(formula_text, calc_text))
        self.wait(1)

        # Circle the final mathematical result
        self.play(Circumscribe(calc_text, color=GREEN))
        self.wait(2.5)

        # Clean fade out of all remaining screen objects using Group to support all Mobject types safely
        self.play(FadeOut(Group(*self.mobjects)))
        self.wait(1)