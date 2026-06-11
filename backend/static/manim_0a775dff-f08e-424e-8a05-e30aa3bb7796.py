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
ReplacementTransform = Transform

# Monkey-patch Line to prevent crashes on hallucinated .bend() method
Line.bend = lambda self, *args, **kwargs: self
Mobject.set_color_by_gradient = lambda self, *args, **kwargs: self



class MainScene(Scene):
    def construct(self):
        self.show_intro()
        self.compare_area_volume()
        self.construct_prism()
        self.final_formula()

    def show_intro(self):
        # Title and definition
        title = Text("Investigating Volume", color=BLUE).scale(1.2)
        definition = Text(
            "Volume is the amount of 3D space\nan object occupies.",
            font_size=32,
            t2c={"3D space": YELLOW}
        ).next_to(title, DOWN, buff=0.5)

        self.play(Write(title))
        self.wait(1)
        self.play(FadeIn(definition))
        self.wait(2)
        self.play(FadeOut(title), FadeOut(definition))

    def compare_area_volume(self):
        # 2D Area section
        area_text = Text("2D: Area", color=GREEN).to_edge(UP)
        square = Square(side_length=2).set_stroke(GREEN)
        square_label = MathTex(r"\text{Side} \times \text{Side}").next_to(square, DOWN)
        
        self.play(Write(area_text))
        self.play(Create(square))
        self.play(Write(square_label))
        self.wait(1)

        # Transition to 3D Volume
        volume_text = Text("3D: Volume", color=YELLOW).to_edge(UP)
        
        # Creating a pseudo-3D Cube using Polygons to represent volume
        f_face = Square(side_length=2).set_fill(BLUE, opacity=0.5).set_stroke(WHITE)
        # Isometric-style top and side faces
        t_face = Polygon(
            [-1, 1, 0], [-0.5, 1.5, 0], [1.5, 1.5, 0], [1, 1, 0],
            stroke_color=WHITE, fill_color=BLUE, fill_opacity=0.3
        )
        s_face = Polygon(
            [1, 1, 0], [1.5, 1.5, 0], [1.5, -0.5, 0], [1, -1, 0],
            stroke_color=WHITE, fill_color=BLUE, fill_opacity=0.4
        )
        cube_3d = VGroup(f_face, t_face, s_face).center()

        self.play(
            ReplacementTransform(area_text, volume_text),
            ReplacementTransform(square, cube_3d),
            FadeOut(square_label)
        )
        
        vol_label = MathTex(r"L \times W \times H").next_to(cube_3d, DOWN)
        self.play(Write(vol_label))
        self.wait(2)
        
        self.play(FadeOut(volume_text), FadeOut(cube_3d), FadeOut(vol_label))

    def construct_prism(self):
        # Helper for a single "3D" unit cube
        def get_unit_cube(color=ORANGE):
            s = 0.8 # size
            f = Square(side_length=s).set_fill(color, opacity=0.8).set_stroke(WHITE, width=1)
            # Top face
            t = Polygon(
                [-s/2, s/2, 0], [-s/2+0.2, s/2+0.2, 0], [s/2+0.2, s/2+0.2, 0], [s/2, s/2, 0],
                fill_color=color, fill_opacity=0.6, stroke_color=WHITE, stroke_width=1
            )
            # Side face
            side = Polygon(
                [s/2, s/2, 0], [s/2+0.2, s/2+0.2, 0], [s/2+0.2, -s/2+0.2, 0], [s/2, -s/2, 0],
                fill_color=color, fill_opacity=0.7, stroke_color=WHITE, stroke_width=1
            )
            return VGroup(f, t, side)

        prism_group = VGroup()
        
        # Build layer by layer: Length 3, Depth 2, Height 2
        # Loop order matters for pseudo-3D layering (back-to-front)
        for d in range(1, -1, -1): # Depth
            for h in range(2):      # Height
                for l in range(3):  # Length
                    unit = get_unit_cube()
                    # Offset for each dimension
                    unit.shift(RIGHT * l * 0.8 + UP * h * 0.8 + (RIGHT*0.2 + UP*0.2) * d)
                    prism_group.add(unit)

        prism_group.center()
        
        # Dimensions and Labels
        length_brace = Brace(prism_group, DOWN, color=WHITE)
        length_text = length_brace.get_text("Length = 3")
        
        height_brace = Brace(prism_group, LEFT, color=WHITE)
        height_text = height_brace.get_text("Height = 2")
        
        # Use an arrow to represent the depth/width
        w_start = prism_group.get_corner(DR) + LEFT*0.1
        w_end = w_start + (RIGHT*0.4 + UP*0.4)
        width_arrow = DoubleArrow(w_start, w_end, buff=0, color=YELLOW, tip_length=0.2)
        width_text = Text("Width = 2", font_size=24).next_to(width_arrow, RIGHT)

        self.play(FadeIn(prism_group, shift=UP))
        self.wait(1)
        self.play(Create(length_brace), Write(length_text))
        self.play(Create(height_brace), Write(height_text))
        self.play(Create(width_arrow), Write(width_text))
        self.wait(1)

        # Calculation display
        calc = MathTex("V = 3 \\times 2 \\times 2", color=YELLOW).to_edge(UP).shift(DOWN)
        result = MathTex("V = 12 \\text{ cubic units}", color=YELLOW).next_to(calc, DOWN)
        
        self.play(Write(calc))
        self.wait(0.5)
        self.play(Write(result))
        self.play(Indicate(result))
        self.wait(2)
        
        self.play(
            FadeOut(prism_group), FadeOut(length_brace), FadeOut(length_text),
            FadeOut(height_brace), FadeOut(height_text), FadeOut(width_arrow),
            FadeOut(width_text), FadeOut(calc), FadeOut(result)
        )

    def final_formula(self):
        summary_title = Text("Key Takeaway").scale(1.1).to_edge(UP)
        formula_box = Rectangle(width=8, height=2.5, color=GOLD)
        
        formula = MathTex(r"\text{Volume} = \text{Length} \times \text{Width} \times \text{Height}", color=WHITE)
        formula_short = MathTex(r"V = l \cdot w \cdot h", color=YELLOW).next_to(formula, DOWN, buff=0.4)
        
        v_group = VGroup(formula, formula_short).move_to(formula_box.get_center())
        
        units_info = Text(
            "Measured in cubic units (e.g., cm³, m³)",
            font_size=28,
            color=LIGHT_GRAY
        ).next_to(formula_box, DOWN, buff=1)

        self.play(Write(summary_title))
        self.play(Create(formula_box), Write(formula))
        self.wait(1)
        self.play(Write(formula_short))
        self.wait(1)
        self.play(FadeIn(units_info))
        self.wait(3)
        
        self.play(*[FadeOut(m) for m in self.mobjects])