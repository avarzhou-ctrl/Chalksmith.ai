from manim import *
import numpy as np

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
        # 1. Title & Introduction
        self.intro_scene()
        
        # 2. Build the Pyramid
        self.build_pyramid()
        
        # 3. Explain the 10% Rule & Heat Loss
        self.explain_10_percent_rule()
        
        # 4. Summary & Takeaways
        self.summary_scene()

    def intro_scene(self):
        title = Text("The Trophic Energy Pyramid", font_size=40, color=BLUE)
        subtitle = Text("Energy Flow in Ecosystems", font_size=24, color=GRAY)
        
        VGroup(title, subtitle).arrange(DOWN, buff=0.4)
        
        self.play(Write(title))
        self.play(FadeIn(subtitle, shift=UP * 0.3))
        self.wait(2)
        
        intro_text = Paragraph(
            "Ecosystems rely on a continuous flow of energy.",
            "As energy moves up the food chain, most of it is lost.",
            alignment="center",
            font_size=18,
            color=WHITE
        ).next_to(subtitle, DOWN, buff=0.8)
        
        self.play(Write(intro_text))
        self.wait(3)
        
        # Transition out intro text, keep title but move it up
        self.play(
            FadeOut(intro_text),
            FadeOut(subtitle),
            title.animate.scale(0.7).to_edge(UP, buff=0.4)
        )
        self.wait(1)
        self.title = title  # Keep reference to title

    def build_pyramid(self):
        # Define Y-levels for each trophic tier
        self.y_coords = [-1.65, -0.65, 0.35, 1.35]
        
        # Define the 4 levels of the pyramid using custom coordinates
        self.p4 = Polygon([-3.0, -2.1, 0], [3.0, -2.1, 0], [2.1, -1.2, 0], [-2.1, -1.2, 0], 
                          stroke_color=WHITE, fill_color=GREEN, fill_opacity=0.6)
        
        self.p3 = Polygon([-2.1, -1.1, 0], [2.1, -1.1, 0], [1.3, -0.2, 0], [-1.3, -0.2, 0], 
                          stroke_color=WHITE, fill_color=YELLOW, fill_opacity=0.6)
        
        self.p2 = Polygon([-1.3, -0.1, 0], [1.3, -0.1, 0], [0.6, 0.8, 0], [-0.6, 0.8, 0], 
                          stroke_color=WHITE, fill_color=ORANGE, fill_opacity=0.6)
        
        self.p1 = Polygon([-0.6, 0.9, 0], [0.6, 0.9, 0], [0.0, 1.8, 0], 
                          stroke_color=WHITE, fill_color=RED, fill_opacity=0.6)
        
        self.pyramid_layers = VGroup(self.p4, self.p3, self.p2, self.p1)
        
        # Define Labels (Left = Trophic Role, Right = Energy Capacity)
        self.left_labels = VGroup(
            Text("Producers\n(Plants, Algae)", font_size=16, color=GREEN),
            Text("Primary Consumers\n(Herbivores)", font_size=16, color=YELLOW),
            Text("Secondary Consumers\n(Carnivores)", font_size=16, color=ORANGE),
            Text("Tertiary Consumers\n(Apex Predators)", font_size=16, color=RED)
        )
        
        self.right_labels = VGroup(
            Text("100% Energy\n(10,000 J)", font_size=16, color=WHITE),
            Text("10% Energy\n(1,000 J)", font_size=16, color=WHITE),
            Text("1% Energy\n(100 J)", font_size=16, color=WHITE),
            Text("0.1% Energy\n(10 J)", font_size=16, color=WHITE)
        )
        
        # Position the labels perfectly on the sides of each pyramid block
        for i in range(4):
            self.left_labels[i].next_to(np.array([-3.4, self.y_coords[i], 0]), LEFT, buff=0)
            self.right_labels[i].next_to(np.array([3.4, self.y_coords[i], 0]), RIGHT, buff=0)
            
        # Draw the pyramid from the bottom up (mimicking natural energy flow)
        for i in range(4):
            self.play(
                Create(self.pyramid_layers[i]),
                Write(self.left_labels[i]),
                Write(self.right_labels[i]),
                run_time=1.2
            )
            self.wait(0.5)
            
        self.wait(1.5)

    def explain_10_percent_rule(self):
        # Explanation text at the bottom
        explanation = Paragraph(
            "The 10% Rule: Only about 10% of the energy stored as biomass",
            "at one trophic level is passed on to the next level.",
            alignment="center",
            font_size=18,
            color=WHITE
        ).to_edge(DOWN, buff=0.4)
        
        self.play(Write(explanation))
        self.wait(2)
        
        # Let's demonstrate the loss from Level 4 to Level 3 visually
        # Flow arrow going up
        up_arrow = Arrow(
            start=[0.0, -1.65, 0], 
            end=[0.0, -0.65, 0], 
            color=BLUE, 
            stroke_width=6, 
            max_tip_length_to_length_ratio=0.3
        )
        up_arrow_label = Text("10% Transferred", font_size=14, color=BLUE).next_to(up_arrow, RIGHT, buff=0.15)
        
        # Heat loss arrow going out
        heat_arrow = Arrow(
            start=[2.3, -1.4, 0], 
            end=[3.8, -1.9, 0], 
            color=RED, 
            stroke_width=4
        )
        heat_label = Text("90% Lost\n(Heat & Waste)", font_size=14, color=RED).next_to(heat_arrow.get_end(), DOWN, buff=0.1)
        
        # Step 1: Highlight bottom tier (Producers)
        self.play(
            Indicate(self.p4, color=GREEN),
            self.right_labels[0].animate.scale(1.15).set_color(GREEN)
        )
        self.wait(1)
        
        # Step 2: Show energy loss
        self.play(
            Create(heat_arrow),
            Write(heat_label)
        )
        self.wait(1.5)
        
        # Step 3: Show transfer to level 3
        self.play(
            Create(up_arrow),
            Write(up_arrow_label)
        )
        self.play(
            Indicate(self.p3, color=YELLOW),
            self.right_labels[1].animate.scale(1.15).set_color(YELLOW)
        )
        self.wait(2.5)
        
        # Clean up temporary annotations for the final transition
        self.play(
            FadeOut(up_arrow),
            FadeOut(up_arrow_label),
            FadeOut(heat_arrow),
            FadeOut(heat_label),
            FadeOut(explanation),
            self.right_labels[0].animate.scale(1/1.15).set_color(WHITE),
            self.right_labels[1].animate.scale(1/1.15).set_color(WHITE)
        )
        self.wait(1)

    def summary_scene(self):
        # Fade out pyramid and labels
        self.play(
            FadeOut(self.pyramid_layers),
            FadeOut(self.left_labels),
            FadeOut(self.right_labels),
            FadeOut(self.title)
        )
        self.wait(0.5)
        
        # Show final summary slide
        summary_title = Text("Key Takeaways", font_size=32, color=BLUE).to_edge(UP, buff=0.8)
        
        bullet1 = Paragraph(
            "1. Energy Decreases Progressively",
            "   Each level has only 10% of the energy of the level below it.",
            font_size=18,
            color=WHITE
        )
        bullet2 = Paragraph(
            "2. Biomass Limits",
            "   Because energy is lost, higher levels support far fewer organisms.",
            font_size=18,
            color=WHITE
        )
        bullet3 = Paragraph(
            "3. Heat Loss",
            "   90% of energy is lost via cellular respiration, movement, and heat.",
            font_size=18,
            color=WHITE
        )
        
        bullets = VGroup(bullet1, bullet2, bullet3).arrange(DOWN, buff=0.5, aligned_edge=LEFT)
        bullets.next_to(summary_title, DOWN, buff=0.8)
        
        self.play(Write(summary_title))
        self.wait(0.5)
        
        for bullet in bullets:
            self.play(FadeIn(bullet, shift=RIGHT * 0.4))
            self.wait(2)
            
        self.wait(3)
        
        # Clean up scene entirely
        self.play(FadeOut(summary_title), FadeOut(bullets))
        self.wait(1)