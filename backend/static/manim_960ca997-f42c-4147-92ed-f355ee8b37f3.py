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
    def create_sun(self):
        """Creates a sun shape with radiating rays."""
        sun_circle = Circle(radius=0.25, color=YELLOW, fill_color=YELLOW, fill_opacity=1)
        rays = VGroup()
        for angle in np.linspace(0, 2 * np.pi, 8, endpoint=False):
            start = np.array([0.35 * np.cos(angle), 0.35 * np.sin(angle), 0])
            end = np.array([0.55 * np.cos(angle), 0.55 * np.sin(angle), 0])
            rays.add(Line(start, end, color=YELLOW, stroke_width=2.5))
        return VGroup(sun_circle, rays)

    def create_pot(self, position):
        """Creates a brown flower pot with dark grey soil."""
        pot = Rectangle(width=1.2, height=0.8, color=BROWN, fill_color=BROWN, fill_opacity=1)
        pot.move_to(position)
        soil = Rectangle(width=1.1, height=0.15, color=GRAY, fill_color=GRAY, fill_opacity=1)
        soil.next_to(pot.get_top(), DOWN, buff=0.05)
        return VGroup(pot, soil)

    def construct(self):
        # --- TITLE SECTION ---
        title = Text("3 Types of Scientific Variables", font_size=40, color=GOLD)
        subtitle = Text("The foundation of controlled experiments", font_size=24, color=WHITE).next_to(title, DOWN, buff=0.5)
        self.play(Write(title))
        self.play(FadeIn(subtitle))
        self.wait(2)
        self.play(FadeOut(title), FadeOut(subtitle))
        self.wait(0.5)

        # --- EXPERIMENT SETUP ---
        intro_text = Text("Let's set up an experiment:", font_size=28, color=WHITE).to_edge(UP, buff=0.5)
        scenario_text = Text("How does the amount of water affect plant growth?", font_size=24, color=BLUE).next_to(intro_text, DOWN, buff=0.2)
        
        self.play(Write(intro_text))
        self.play(FadeIn(scenario_text))
        self.wait(2)

        # Draw Ground
        ground = Line(start=[-6, -2.2, 0], end=[6, -2.2, 0], color=GRAY, stroke_width=4)
        self.play(Create(ground))

        # Draw 3 Pots
        pot1 = self.create_pot([-3.5, -1.8, 0])
        pot2 = self.create_pot([0, -1.8, 0])
        pot3 = self.create_pot([3.5, -1.8, 0])

        self.play(
            FadeIn(pot1),
            FadeIn(pot2),
            FadeIn(pot3)
        )
        self.wait(1.5)
        
        # Remove scenario text to clear up space
        self.play(FadeOut(intro_text), FadeOut(scenario_text))
        self.wait(0.5)

        # --- SECTION 1: INDEPENDENT VARIABLE ---
        sec1_title = Text("1. Independent Variable", font_size=32, color=BLUE).to_edge(UP, buff=0.4)
        sec1_desc = Text("The Cause: The factor you purposely change.", font_size=22, color=WHITE).next_to(sec1_title, DOWN, buff=0.1)
        
        self.play(Write(sec1_title), Write(sec1_desc))
        self.wait(1)

        # Create water drops for each pot
        drop1_1 = Circle(radius=0.1, color=BLUE, fill_color=BLUE, fill_opacity=0.8).next_to(pot1, UP, buff=0.3).shift(LEFT*0.3)
        
        drop2_1 = Circle(radius=0.1, color=BLUE, fill_color=BLUE, fill_opacity=0.8).next_to(pot2, UP, buff=0.3).shift(LEFT*0.3)
        drop2_2 = Circle(radius=0.1, color=BLUE, fill_color=BLUE, fill_opacity=0.8).next_to(drop2_1, RIGHT, buff=0.1)
        
        drop3_1 = Circle(radius=0.1, color=BLUE, fill_color=BLUE, fill_opacity=0.8).next_to(pot3, UP, buff=0.3).shift(LEFT*0.4)
        drop3_2 = Circle(radius=0.1, color=BLUE, fill_color=BLUE, fill_opacity=0.8).next_to(drop3_1, RIGHT, buff=0.1)
        drop3_3 = Circle(radius=0.1, color=BLUE, fill_color=BLUE, fill_opacity=0.8).next_to(drop3_2, RIGHT, buff=0.1)

        water1 = VGroup(drop1_1)
        water2 = VGroup(drop2_1, drop2_2)
        water3 = VGroup(drop3_1, drop3_2, drop3_3)

        # Standard labels constructed with separate lines to avoid multiline overlapping
        label1 = VGroup(
            Text("Low Water", font_size=16, color=BLUE),
            Text("(1 Unit)", font_size=14, color=GRAY)
        ).arrange(DOWN, buff=0.1).next_to(pot1, DOWN, buff=0.3)

        label2 = VGroup(
            Text("Medium Water", font_size=16, color=BLUE),
            Text("(2 Units)", font_size=14, color=GRAY)
        ).arrange(DOWN, buff=0.1).next_to(pot2, DOWN, buff=0.3)

        label3 = VGroup(
            Text("High Water", font_size=16, color=BLUE),
            Text("(3 Units)", font_size=14, color=GRAY)
        ).arrange(DOWN, buff=0.1).next_to(pot3, DOWN, buff=0.3)

        self.play(
            FadeIn(water1), FadeIn(label1),
            FadeIn(water2), FadeIn(label2),
            FadeIn(water3), FadeIn(label3)
        )
        self.wait(1)
        
        self.play(
            Indicate(water1, color=BLUE),
            Indicate(water2, color=BLUE),
            Indicate(water3, color=BLUE)
        )
        self.wait(2)

        # Clear section 1 text
        self.play(FadeOut(sec1_title), FadeOut(sec1_desc))
        self.wait(0.5)

        # --- SECTION 2: DEPENDENT VARIABLE ---
        sec2_title = Text("2. Dependent Variable", font_size=32, color=GREEN).to_edge(UP, buff=0.4)
        sec2_desc = Text("The Effect: What you measure or observe.", font_size=22, color=WHITE).next_to(sec2_title, DOWN, buff=0.1)
        
        self.play(Write(sec2_title), Write(sec2_desc))
        self.wait(1)

        # Stems grow from pot tops (y = -1.4)
        stem1 = Line(start=[-3.5, -1.4, 0], end=[-3.5, -0.8, 0], color=GREEN, stroke_width=6)
        stem2 = Line(start=[0, -1.4, 0], end=[0, 0.0, 0], color=GREEN, stroke_width=6)
        stem3 = Line(start=[3.5, -1.4, 0], end=[3.5, 0.8, 0], color=GREEN, stroke_width=6)

        # Leaves
        leaf1_1 = Ellipse(width=0.3, height=0.15, color=GREEN, fill_color=GREEN, fill_opacity=0.9).rotate(np.pi/6).move_to([-3.65, -0.9, 0])
        leaf1_2 = Ellipse(width=0.3, height=0.15, color=GREEN, fill_color=GREEN, fill_opacity=0.9).rotate(-np.pi/6).move_to([-3.35, -0.9, 0])
        leaves1 = VGroup(leaf1_1, leaf1_2)

        leaf2_1 = Ellipse(width=0.4, height=0.2, color=GREEN, fill_color=GREEN, fill_opacity=0.9).rotate(np.pi/6).move_to([-0.2, -0.1, 0])
        leaf2_2 = Ellipse(width=0.4, height=0.2, color=GREEN, fill_color=GREEN, fill_opacity=0.9).rotate(-np.pi/6).move_to([0.2, -0.1, 0])
        leaves2 = VGroup(leaf2_1, leaf2_2)

        leaf3_1 = Ellipse(width=0.45, height=0.22, color=GREEN, fill_color=GREEN, fill_opacity=0.9).rotate(np.pi/6).move_to([3.25, 0.7, 0])
        leaf3_2 = Ellipse(width=0.45, height=0.22, color=GREEN, fill_color=GREEN, fill_opacity=0.9).rotate(-np.pi/6).move_to([3.75, 0.7, 0])
        leaves3 = VGroup(leaf3_1, leaf3_2)

        self.play(
            Create(stem1),
            Create(stem2),
            Create(stem3),
            run_time=2
        )
        self.play(
            FadeIn(leaves1),
            FadeIn(leaves2),
            FadeIn(leaves3)
        )
        self.wait(1)

        # Growth labels
        g_label1 = VGroup(
            Text("Short Growth", font_size=16, color=GREEN),
            Text("(6 cm)", font_size=14, color=WHITE)
        ).arrange(DOWN, buff=0.1).next_to(stem1.get_top(), UP, buff=0.2)

        g_label2 = VGroup(
            Text("Medium Growth", font_size=16, color=GREEN),
            Text("(14 cm)", font_size=14, color=WHITE)
        ).arrange(DOWN, buff=0.1).next_to(stem2.get_top(), UP, buff=0.2)

        g_label3 = VGroup(
            Text("Tall Growth", font_size=16, color=GREEN),
            Text("(22 cm)", font_size=14, color=WHITE)
        ).arrange(DOWN, buff=0.1).next_to(stem3.get_top(), UP, buff=0.2)

        self.play(Write(g_label1), Write(g_label2), Write(g_label3))
        self.wait(2)

        # Clear section 2 text
        self.play(FadeOut(sec2_title), FadeOut(sec2_desc))
        self.wait(0.5)

        # --- SECTION 3: CONTROLLED VARIABLES ---
        sec3_title = Text("3. Controlled Variables", font_size=32, color=ORANGE).to_edge(UP, buff=0.4)
        sec3_desc = Text("The Constants: Kept strictly identical to ensure fairness.", font_size=22, color=WHITE).next_to(sec3_title, DOWN, buff=0.1)

        self.play(Write(sec3_title), Write(sec3_desc))
        self.wait(1)

        # Create 3 identical Suns
        sun1 = self.create_sun().move_to([-3.5, 2.0, 0])
        sun2 = self.create_sun().move_to([0, 2.0, 0])
        sun3 = self.create_sun().move_to([3.5, 2.0, 0])

        self.play(
            FadeIn(sun1),
            FadeIn(sun2),
            FadeIn(sun3)
        )
        self.wait(1)

        # Highlight Suns together
        self.play(
            Indicate(sun1, color=YELLOW),
            Indicate(sun2, color=YELLOW),
            Indicate(sun3, color=YELLOW)
        )
        # Highlight Pots together (representing soil/pot variables)
        self.play(
            Indicate(pot1, color=ORANGE),
            Indicate(pot2, color=ORANGE),
            Indicate(pot3, color=ORANGE)
        )
        self.wait(2.5)

        # Fade out everything to prepare for Summary Card Layout
        self.play(
            FadeOut(ground),
            FadeOut(pot1), FadeOut(pot2), FadeOut(pot3),
            FadeOut(water1), FadeOut(water2), FadeOut(water3),
            FadeOut(label1), FadeOut(label2), FadeOut(label3),
            FadeOut(stem1), FadeOut(stem2), FadeOut(stem3),
            FadeOut(leaves1), FadeOut(leaves2), FadeOut(leaves3),
            FadeOut(g_label1), FadeOut(g_label2), FadeOut(g_label3),
            FadeOut(sun1), FadeOut(sun2), FadeOut(sun3),
            FadeOut(sec3_title), FadeOut(sec3_desc)
        )
        self.wait(1)

        # --- SUMMARY SECTION ---
        sum_title = Text("Summary of Scientific Variables", font_size=34, color=GOLD).to_edge(UP, buff=0.6)
        self.play(Write(sum_title))
        self.wait(1)

        # Horizontal Box Container Settings
        box_width = 3.6
        box_height = 3.8
        
        box1 = RoundedRectangle(width=box_width, height=box_height, corner_radius=0.15, color=BLUE, stroke_width=3)
        box2 = RoundedRectangle(width=box_width, height=box_height, corner_radius=0.15, color=GREEN, stroke_width=3)
        box3 = RoundedRectangle(width=box_width, height=box_height, corner_radius=0.15, color=ORANGE, stroke_width=3)

        boxes = VGroup(box1, box2, box3).arrange(RIGHT, buff=0.4).shift(DOWN*0.5)

        # Box 1 content (Independent)
        b1_title = Text("Independent", font_size=22, color=BLUE)
        b1_desc1 = Text("What you CHANGE", font_size=16, color=WHITE)
        b1_desc2 = Text("(The Cause)", font_size=14, color=GRAY)
        b1_ex = VGroup(
            Text("Example:", font_size=14, color=WHITE),
            Text("Water Amount", font_size=16, color=BLUE)
        ).arrange(DOWN, buff=0.1)
        box1_content = VGroup(b1_title, b1_desc1, b1_desc2, b1_ex).arrange(DOWN, buff=0.3)
        box1_content.move_to(box1.get_center())

        # Box 2 content (Dependent)
        b2_title = Text("Dependent", font_size=22, color=GREEN)
        b2_desc1 = Text("What you MEASURE", font_size=16, color=WHITE)
        b2_desc2 = Text("(The Effect)", font_size=14, color=GRAY)
        b2_ex = VGroup(
            Text("Example:", font_size=14, color=WHITE),
            Text("Plant Growth", font_size=16, color=GREEN)
        ).arrange(DOWN, buff=0.1)
        box2_content = VGroup(b2_title, b2_desc1, b2_desc2, b2_ex).arrange(DOWN, buff=0.3)
        box2_content.move_to(box2.get_center())

        # Box 3 content (Controlled)
        b3_title = Text("Controlled", font_size=22, color=ORANGE)
        b3_desc1 = Text("What stays SAME", font_size=16, color=WHITE)
        b3_desc2 = Text("(The Constants)", font_size=14, color=GRAY)
        b3_ex = VGroup(
            Text("Example:", font_size=14, color=WHITE),
            Text("Soil, Pot, Sun", font_size=16, color=ORANGE)
        ).arrange(DOWN, buff=0.1)
        box3_content = VGroup(b3_title, b3_desc1, b3_desc2, b3_ex).arrange(DOWN, buff=0.3)
        box3_content.move_to(box3.get_center())

        # Sequential fade-in of card content
        self.play(FadeIn(box1), Write(box1_content))
        self.wait(1)
        self.play(FadeIn(box2), Write(box2_content))
        self.wait(1)
        self.play(FadeIn(box3), Write(box3_content))
        self.wait(3.5)

        # Clear everything out
        self.play(
            FadeOut(sum_title),
            FadeOut(box1), FadeOut(box1_content),
            FadeOut(box2), FadeOut(box2_content),
            FadeOut(box3), FadeOut(box3_content)
        )
        self.wait(1)