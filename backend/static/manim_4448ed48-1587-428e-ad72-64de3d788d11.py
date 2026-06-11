import numpy as np
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
        # -------------------------------------------------------------
        # SECTION 1: Introduction & Concept Definition
        # -------------------------------------------------------------
        title = Text("Understanding Elapsed Time", font_size=36, color=YELLOW)
        title.to_edge(UP, buff=1.0)
        
        definition_line1 = Text("Elapsed time is the amount of time", font_size=24, color=WHITE)
        definition_line2 = Text("that passes from the start of an event to its end.", font_size=24, color=WHITE)
        definition = VGroup(definition_line1, definition_line2).arrange(DOWN, buff=0.3).next_to(title, DOWN, buff=1.0)
        
        self.play(Write(title))
        self.play(FadeIn(definition, shift=UP * 0.3))
        self.wait(2)
        
        # Introduce the example problem
        example_box = RoundedRectangle(corner_radius=0.1, color=BLUE, width=8, height=1.5).shift(DOWN * 1.5)
        example_text = Text("Example: How much time passes between\n8:15 AM and 10:45 AM?", font_size=22, color=WHITE)
        example_text.move_to(example_box.get_center())
        
        self.play(Create(example_box), Write(example_text))
        self.wait(3)
        
        # Clear the introduction screen to make space for the timeline
        self.play(
            FadeOut(definition),
            FadeOut(example_box),
            FadeOut(example_text),
            title.animate.scale(0.8).to_edge(UP, buff=0.4)
        )
        self.wait(0.5)

        # -------------------------------------------------------------
        # SECTION 2: Timeline Construction
        # -------------------------------------------------------------
        # Timeline lowered to y = -2.0 to prevent overlaps with calculation text above
        timeline_y = -2.0
        timeline = Line(start=LEFT * 5.0 + UP * timeline_y, end=RIGHT * 5.0 + UP * timeline_y, color=BLUE)
        
        ticks = VGroup()
        tick_labels = VGroup()
        
        # Hour mappings with wider spacing: x-coordinate = -4.5 + (hour - 8.0) * 3.0
        # 8:00 -> -4.5, 9:00 -> -1.5, 10:00 -> 1.5, 11:00 -> 4.5
        hours = [8, 9, 10, 11]
        for hour in hours:
            x_pos = -4.5 + (hour - 8.0) * 3.0
            tick = Line(
                start=np.array([x_pos, timeline_y + 0.15, 0]), 
                end=np.array([x_pos, timeline_y - 0.15, 0]), 
                color=BLUE
            )
            ticks.add(tick)
            
            label = Text(f"{hour}:00", font_size=14, color=WHITE)
            label.next_to(tick, DOWN, buff=0.15)
            tick_labels.add(label)
            
        self.play(Create(timeline), Create(ticks))
        self.play(FadeIn(tick_labels, shift=UP * 0.2))
        self.wait(1)

        # -------------------------------------------------------------
        # SECTION 3: Start and End Points
        # -------------------------------------------------------------
        # Start Time: 8:15 AM -> x = -4.5 + 0.25 * 3.0 = -3.75
        start_x = -3.75
        start_dot = Dot(point=np.array([start_x, timeline_y, 0]), color=YELLOW, radius=0.12)
        start_label = Text("8:15 AM\n(Start)", font_size=13, color=YELLOW).next_to(start_dot, DOWN, buff=0.7)
        
        # End Time: 10:45 AM -> x = 1.5 + 0.75 * 3.0 = 3.75
        end_x = 3.75
        end_dot = Dot(point=np.array([end_x, timeline_y, 0]), color=RED, radius=0.12)
        end_label = Text("10:45 AM\n(End)", font_size=13, color=RED).next_to(end_dot, DOWN, buff=0.7)
        
        self.play(
            GrowFromCenter(start_dot),
            FadeIn(start_label, shift=UP * 0.2)
        )
        self.play(
            GrowFromCenter(end_dot),
            FadeIn(end_label, shift=UP * 0.2)
        )
        self.wait(1.5)

        # -------------------------------------------------------------
        # SECTION 4: Step-by-Step Jumps
        # -------------------------------------------------------------
        step_instruction = Text("Let's break the timeline into easy steps!", font_size=20, color=WHITE).shift(UP * 2.2)
        self.play(Write(step_instruction))
        self.wait(1)

        # --- STEP 1: Jump to the next whole hour (8:15 -> 9:00) ---
        step1_desc = Text("Step 1: Jump to the next whole hour (8:15 to 9:00)", font_size=18, color=WHITE)
        step1_desc.shift(UP * 1.6)
        
        curve1, lbl1 = self.get_jump_bezier(start_x, -1.5, "+45 min", height=0.7, y_base=timeline_y)
        
        self.play(Transform(step_instruction, step1_desc))
        self.play(Create(curve1), FadeIn(lbl1, shift=UP * 0.1))
        self.wait(2)

        # --- STEP 2: Jump full hours (9:00 -> 10:00) ---
        step2_desc = Text("Step 2: Jump in full hour blocks (9:00 to 10:00)", font_size=18, color=WHITE)
        step2_desc.shift(UP * 1.6)
        
        curve2, lbl2 = self.get_jump_bezier(-1.5, 1.5, "+1 hr", height=0.9, y_base=timeline_y)
        
        self.play(Transform(step_instruction, step2_desc))
        self.play(Create(curve2), FadeIn(lbl2, shift=UP * 0.1))
        self.wait(2)

        # --- STEP 3: Jump remaining minutes (10:00 -> 10:45) ---
        step3_desc = Text("Step 3: Jump the remaining minutes (10:00 to 10:45)", font_size=18, color=WHITE)
        step3_desc.shift(UP * 1.6)
        
        curve3, lbl3 = self.get_jump_bezier(1.5, end_x, "+45 min", height=0.7, y_base=timeline_y)
        
        self.play(Transform(step_instruction, step3_desc))
        self.play(Create(curve3), FadeIn(lbl3, shift=UP * 0.1))
        self.wait(2.5)

        # -------------------------------------------------------------
        # SECTION 5: Addition & Final Calculation
        # -------------------------------------------------------------
        step4_desc = Text("Step 4: Add all the jump times together!", font_size=18, color=WHITE)
        step4_desc.shift(UP * 1.6)
        self.play(Transform(step_instruction, step4_desc))
        self.wait(1)

        # Positioned with breathing room above the jump curves and labels
        calc1 = MathTex(r"\text{Total Time} = 45\text{ min} + 1\text{ hr} + 45\text{ min}", font_size=22, color=WHITE)
        calc1.shift(UP * 0.8)
        
        calc2 = MathTex(r"= 1\text{ hr} + 90\text{ min}", font_size=22, color=WHITE)
        calc2.next_to(calc1, DOWN, buff=0.25)
        
        calc3 = MathTex(r"= 2\text{ hr } 30\text{ min}", font_size=24, color=YELLOW)
        calc3.next_to(calc2, DOWN, buff=0.25)

        self.play(Write(calc1))
        self.wait(1.5)
        self.play(Write(calc2))
        self.wait(1.5)
        self.play(Write(calc3))
        self.play(Circumscribe(calc3, color=YELLOW))
        self.wait(3)

        # -------------------------------------------------------------
        # SECTION 6: Outro & Summary
        # -------------------------------------------------------------
        # Fade out everything from the workspace safely
        self.play(
            FadeOut(timeline),
            FadeOut(ticks),
            FadeOut(tick_labels),
            FadeOut(start_dot),
            FadeOut(start_label),
            FadeOut(end_dot),
            FadeOut(end_label),
            FadeOut(curve1),
            FadeOut(lbl1),
            FadeOut(curve2),
            FadeOut(lbl2),
            FadeOut(curve3),
            FadeOut(lbl3),
            FadeOut(step_instruction),
            FadeOut(calc1),
            FadeOut(calc2),
            FadeOut(calc3),
            title.animate.scale(1.25).move_to(UP * 2.5)
        )
        self.wait(0.5)

        summary_title = Text("Key Strategy Summary:", font_size=24, color=GREEN).next_to(title, DOWN, buff=0.6)
        
        rule1 = Text("1. Go to the nearest whole hour to find initial minutes.", font_size=18, color=WHITE)
        rule2 = Text("2. Jump in easy hour-long blocks.", font_size=18, color=WHITE)
        rule3 = Text("3. Jump the leftover minutes to reach the final destination.", font_size=18, color=WHITE)
        rule4 = Text("4. Add the hours and minutes up to find the total!", font_size=18, color=WHITE)
        
        rules_group = VGroup(rule1, rule2, rule3, rule4).arrange(DOWN, aligned_edge=LEFT, buff=0.35).next_to(summary_title, DOWN, buff=0.5)
        
        self.play(Write(summary_title))
        for rule in rules_group:
            self.play(FadeIn(rule, shift=RIGHT * 0.3))
            self.wait(1)
            
        self.wait(3)
        
        # Clean up scene termination by fading out all remaining active mobjects
        self.play(*[FadeOut(mob) for mob in list(self.mobjects)])
        self.wait(1)

    def get_jump_bezier(self, start_x, end_x, label_text, height=0.6, y_base=-2.0):
        """Helper to construct a smooth custom jump curve on the timeline."""
        p0 = np.array([start_x, y_base, 0.0])
        p2 = np.array([end_x, y_base, 0.0])
        p1 = np.array([(start_x + end_x) / 2.0, y_base + height, 0.0])
        
        curve = VMobject(color=GREEN)
        curve.set_points_as_corners([p0, p1, p2])
        curve.make_smooth()
        
        # Position label slightly above the apex of the curve
        lbl = Text(label_text, font_size=14, color=GREEN).next_to(p1, UP, buff=0.08)
        return curve, lbl