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
        self.intro_section()
        self.prism_construction()
        self.formula_derivation()
        self.summary_section()

    def intro_section(self):
        title = Text("Volume of a Rectangular Prism", color=BLUE).scale(1.2)
        definition = Paragraph(
            "Volume is the measure of 3D space",
            "enclosed by a boundary.",
            alignment="center"
        ).scale(0.8).next_to(title, DOWN)

        self.play(Write(title))
        self.wait(1)
        self.play(FadeIn(definition))
        self.wait(2)
        self.play(FadeOut(title), FadeOut(definition))

    def prism_construction(self):
        # Create a visual 3D-style prism using Polygons in a 2D Scene
        # Base rectangle (front face)
        front_face = Rectangle(width=4, height=2, color=BLUE, fill_opacity=0.3)
        
        # Oblique projection offset
        offset = np.array([0.8, 0.8, 0])
        
        # Calculate vertices for the top and side faces
        p_ul = front_face.get_corner(UL)
        p_ur = front_face.get_corner(UR)
        p_dl = front_face.get_corner(DL)
        p_dr = front_face.get_corner(DR)
        
        top_face = Polygon(
            p_ul, p_ul + offset, p_ur + offset, p_ur,
            color=BLUE, fill_opacity=0.2, stroke_color=BLUE
        )
        side_face = Polygon(
            p_ur, p_ur + offset, p_dr + offset, p_dr,
            color=BLUE, fill_opacity=0.4, stroke_color=BLUE
        )
        
        prism = VGroup(front_face, top_face, side_face).center()
        
        # Labels for the dimensions
        l_label = MathTex("L", color=YELLOW).next_to(front_face, DOWN)
        # Width label placed on the receding edge
        w_label = MathTex("W", color=YELLOW).move_to(side_face.get_edge_center(UR) + RIGHT*0.3)
        h_label = MathTex("H", color=YELLOW).next_to(front_face, LEFT)

        self.play(Create(front_face))
        self.wait(0.5)
        self.play(Create(top_face), Create(side_face))
        self.wait(1)
        
        self.play(
            Write(l_label),
            Write(w_label),
            Write(h_label)
        )
        self.wait(2)
        
        self.prism_group = VGroup(prism, l_label, w_label, h_label)
        self.labels = VGroup(l_label, w_label, h_label)

    def formula_derivation(self):
        # Move prism to the left to make room for text
        self.play(
            self.prism_group.animate.shift(LEFT * 3)
        )

        step1 = Text("1. Find the Area of the Base", font_size=28).to_edge(RIGHT, buff=1).shift(UP * 2)
        area_base = MathTex(r"\text{Area}_{\text{base}} = L \times W", color=GREEN).next_to(step1, DOWN)
        
        step2 = Text("2. Multiply by the Height", font_size=28).next_to(area_base, DOWN, buff=1)
        vol_formula = MathTex(r"\text{Volume} = (L \times W) \times H", color=ORANGE).next_to(step2, DOWN)

        # Highlight L and W
        self.play(Write(step1))
        self.play(Indicate(self.labels[0]), Indicate(self.labels[1]))
        self.play(Write(area_base))
        self.wait(1.5)

        # Highlight H
        self.play(Write(step2))
        self.play(Indicate(self.labels[2]))
        self.play(Write(vol_formula))
        self.wait(1)

        # Final Formula Box
        final_box = SurroundingRectangle(vol_formula, color=YELLOW, buff=0.2)
        self.play(Create(final_box))
        self.wait(2)
        
        self.play(
            FadeOut(step1), 
            FadeOut(area_base), 
            FadeOut(step2), 
            FadeOut(final_box),
            vol_formula.animate.scale(1.2).move_to(RIGHT * 3.5)
        )
        self.final_vol = vol_formula

    def summary_section(self):
        summary_title = Text("Summary", color=BLUE).scale(0.8).to_edge(UL)
        
        summary_points = Paragraph(
            "• Identify Length (L)",
            "• Identify Width (W)",
            "• Identify Height (H)",
            "• V = L × W × H",
            line_spacing=0.8
        ).scale(0.7).next_to(summary_title, DOWN, aligned_edge=LEFT)

        self.play(Write(summary_title))
        self.play(FadeIn(summary_points))
        
        conclusion = Text("Units are always cubic (e.g., cm³)", color=RED, font_size=32).to_edge(DOWN, buff=1.5)
        
        self.play(FadeIn(conclusion))
        self.play(Wiggle(conclusion))
        self.wait(3)

        # Cleanup: use *self.mobjects to unpack list into FadeOut arguments
        # This avoids TypeError by not creating a VGroup of potentially incompatible types
        self.play(*[FadeOut(mob) for mob in self.mobjects])
        self.wait(1)