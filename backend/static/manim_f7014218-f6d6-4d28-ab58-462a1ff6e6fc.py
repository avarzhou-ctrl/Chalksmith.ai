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
        self.intro_section()
        self.greenhouse_effect_section()
        self.correlation_section()
        self.consequences_section()
        self.outro_section()

    def intro_section(self):
        title = Text("Understanding Global Warming", font_size=40, color=RED)
        subtitle = Text("The science of our changing climate", font_size=24, color=GRAY)
        VGroup(title, subtitle).arrange(DOWN, buff=0.4)

        self.play(FadeIn(title), Write(subtitle))
        self.wait(2)
        self.play(FadeOut(title), FadeOut(subtitle))
        self.wait(0.5)

    def greenhouse_effect_section(self):
        # Header
        title_gh = Text("The Greenhouse Effect", font_size=24, color=YELLOW).to_edge(UP, buff=0.5)
        self.play(Write(title_gh))

        # Earth & Atmosphere setup on the Left
        earth_center = LEFT * 3.5 + DOWN * 1
        earth = Circle(radius=1.1, color=BLUE, fill_opacity=0.8).move_to(earth_center)
        land1 = Circle(radius=0.4, color=GREEN, fill_opacity=0.8).move_to(earth_center + UP * 0.3 + LEFT * 0.3)
        land2 = Circle(radius=0.3, color=GREEN, fill_opacity=0.8).move_to(earth_center + DOWN * 0.2 + RIGHT * 0.4)
        earth_system = VGroup(earth, land1, land2)

        atmosphere = Circle(radius=1.8, color=TEAL, stroke_opacity=0.6).move_to(earth_center)
        atmosphere_label = Text("Atmosphere (GHGs)", font_size=14, color=TEAL).next_to(atmosphere, UP, buff=0.1)

        # Sun setup
        sun_center = np.array([-6.0, 2.5, 0.0])
        sun = Circle(radius=0.5, color=YELLOW, fill_opacity=0.9).move_to(sun_center)
        sun_label = Text("Sun", font_size=14, color=YELLOW).next_to(sun, DOWN, buff=0.1)

        self.play(
            FadeIn(earth_system),
            Create(atmosphere),
            FadeIn(atmosphere_label),
            FadeIn(sun),
            FadeIn(sun_label)
        )
        self.wait(1)

        # Right-side explanatory text
        bullet1 = Text("1. Solar rays warm Earth's surface.", font_size=16).to_edge(RIGHT, buff=0.5).shift(UP * 1.5)
        bullet2 = Text("2. Earth radiates thermal heat back.", font_size=16).next_to(bullet1, DOWN, buff=0.4, aligned_edge=LEFT)
        bullet3 = Text("3. GHGs trap heat in the atmosphere.", font_size=16).next_to(bullet2, DOWN, buff=0.4, aligned_edge=LEFT)
        bullet4 = Text("4. Excess GHGs raise global temperatures.", font_size=16).next_to(bullet3, DOWN, buff=0.4, aligned_edge=LEFT)

        # Step 1: Incoming Solar Ray
        ray_in = Arrow(start=sun_center, end=earth_center, color=YELLOW, buff=0.2, stroke_width=4)
        self.play(Write(bullet1))
        self.play(Create(ray_in))
        self.wait(1)

        # Step 2: Outgoing Heat
        ray_out = Arrow(start=earth_center, end=[-1.5, 0.5, 0], color=ORANGE, buff=0.2, stroke_width=4)
        self.play(Write(bullet2))
        self.play(Create(ray_out))
        self.wait(1)

        # Step 3: Trapped Heat bouncing back
        bounce_pt = np.array([-2.3, 0.2, 0])
        ray_trap1 = Line(start=earth_center, end=bounce_pt, color=RED, stroke_width=4)
        ray_trap2 = Arrow(start=bounce_pt, end=earth_center + RIGHT * 0.5 + UP * 0.2, color=RED, buff=0.1, stroke_width=4)
        self.play(Write(bullet3))
        self.play(Create(ray_trap1))
        self.play(Create(ray_trap2))
        self.wait(1)

        # Step 4: Temperature rise
        self.play(Write(bullet4))
        self.play(
            earth.animate.set_color(RED),
            land1.animate.set_color(ORANGE),
            land2.animate.set_color(ORANGE)
        )
        self.wait(3)

        # Clean up section safely
        self.play(*[FadeOut(mob) for mob in self.mobjects])
        self.wait(0.5)

    def correlation_section(self):
        title = Text("The Correlation: CO2 vs. Temperature", font_size=24, color=WHITE).to_edge(UP, buff=0.5)
        self.play(Write(title))

        # Set up graph axes
        axes = Axes(
            x_range=[1960, 2020, 10],
            y_range=[0, 100, 20],
            x_length=6,
            y_length=3.5,
            axis_config={"include_numbers": True, "color": GRAY},
            tips=False
        ).to_edge(LEFT, buff=0.8).shift(DOWN * 0.5)

        axis_labels = axes.get_axis_labels(
            x_label=Text("Year", font_size=14, color=WHITE),
            y_label=Text("Normalized Increase (%)", font_size=14, color=WHITE)
        )

        legend_co2 = Text("— CO2 Concentration", font_size=14, color=GREEN)
        legend_temp = Text("— Global Temperature", font_size=14, color=RED)
        legend = VGroup(legend_co2, legend_temp).arrange(RIGHT, buff=0.5).next_to(axes, UP, buff=0.3)

        self.play(Create(axes), FadeIn(axis_labels), FadeIn(legend))
        self.wait(1)

        # Curve plots
        co2_curve = axes.plot(
            lambda t: 10 + 90 * ((t - 1960) / 60) ** 1.3,
            color=GREEN,
            x_range=[1960, 2020]
        )

        temp_curve = axes.plot(
            lambda t: 5 + 85 * ((t - 1960) / 60) ** 1.7 + 6 * np.sin(0.5 * (t - 1960)),
            color=RED,
            x_range=[1960, 2020]
        )

        # Text explanation on the right (fixed alignment to aligned_edge)
        explanation = VGroup(
            Text("Scientific evidence", font_size=16, color=YELLOW),
            Text("shows that atmospheric CO2", font_size=16),
            Text("and global average temperatures", font_size=16),
            Text("have risen in tight correlation", font_size=16, color=RED),
            Text("over the last several decades.", font_size=16)
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.25).to_edge(RIGHT, buff=0.8).shift(DOWN * 0.5)

        self.play(Create(co2_curve), run_time=3)
        self.play(Create(temp_curve), run_time=3)
        self.play(FadeIn(explanation))
        self.wait(3)

        # Clean up section safely
        self.play(*[FadeOut(mob) for mob in self.mobjects])
        self.wait(0.5)

    def consequences_section(self):
        title = Text("Consequences of Climate Change", font_size=24, color=WHITE).to_edge(UP, buff=0.5)
        self.play(Write(title))

        # Column 1: Glacier Melt (Left)
        label_melt = Text("Glacier Melt", font_size=18, color=WHITE).shift(LEFT * 3.5 + UP * 1.5)
        
        # Draw glacier shapes
        ice_cap = Polygon(
            [-4.8, -1.5, 0], [-2.2, -1.5, 0], [-2.8, 0.3, 0], [-4.2, 0.3, 0],
            color=WHITE, stroke_color=GRAY, fill_opacity=0.9
        )
        water = Rectangle(width=3.2, height=0.5, color=BLUE, fill_opacity=0.7).move_to([-3.5, -1.8, 0])
        glacier_group = VGroup(ice_cap, water)

        # Column 2: Rising Temperatures (Right)
        label_temp = Text("Extreme Heatwaves", font_size=18, color=WHITE).shift(RIGHT * 3.5 + UP * 1.5)

        # Draw a thermometer
        thermo_stem = RoundedRectangle(corner_radius=0.15, height=2.0, width=0.4, color=GRAY, stroke_width=3).shift(RIGHT * 3.5 + DOWN * 0.3)
        thermo_bulb = Circle(radius=0.4, color=GRAY, fill_opacity=1, stroke_width=3).move_to(thermo_stem.get_bottom() + DOWN * 0.1)
        thermo_shell = VGroup(thermo_stem, thermo_bulb)

        liquid_bulb = Circle(radius=0.32, color=RED, fill_opacity=1).move_to(thermo_bulb.get_center())
        liquid_stem = Rectangle(width=0.18, height=0.2, color=RED, fill_opacity=1).next_to(liquid_bulb, UP, buff=-0.05)
        liquid_group = VGroup(liquid_bulb, liquid_stem)

        self.play(
            FadeIn(label_melt),
            FadeIn(glacier_group),
            FadeIn(label_temp),
            FadeIn(thermo_shell),
            FadeIn(liquid_group)
        )
        self.wait(1.5)

        # Action 1: Ice Melts & Sea Level Rises
        melted_ice = Polygon(
            [-4.8, -1.5, 0], [-2.2, -1.5, 0], [-3.4, -1.1, 0], [-3.6, -1.1, 0],
            color=WHITE, stroke_color=GRAY, fill_opacity=0.4
        )
        risen_water = Rectangle(width=3.2, height=1.1, color=BLUE, fill_opacity=0.7).move_to([-3.5, -1.5, 0])

        # Action 2: Temperature Rises
        liquid_stem_hot = Rectangle(width=0.18, height=1.5, color=RED, fill_opacity=1).next_to(liquid_bulb, UP, buff=-0.05)

        self.play(
            Transform(ice_cap, melted_ice),
            Transform(water, risen_water),
            Transform(liquid_stem, liquid_stem_hot),
            run_time=3
        )
        self.wait(3)

        # Clean up section safely
        self.play(*[FadeOut(mob) for mob in self.mobjects])
        self.wait(0.5)

    def outro_section(self):
        title = Text("Combatting Global Warming", font_size=28, color=YELLOW).to_edge(UP, buff=1)
        
        # Fixed alignment to aligned_edge
        points = VGroup(
            Text("- Transition to 100% renewable energy", font_size=18),
            Text("- Conserve ecosystems and restore forests", font_size=18),
            Text("- Implement clean technologies & reduce waste", font_size=18),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.5).next_to(title, DOWN, buff=1)

        closing = Text("The choice is in our hands.", font_size=20, color=RED).next_to(points, DOWN, buff=1.2)

        self.play(Write(title))
        self.play(FadeIn(points))
        self.wait(2)
        self.play(Write(closing))
        self.wait(3)

        # Final clean up safely
        self.play(*[FadeOut(mob) for mob in self.mobjects])
        self.wait(1)