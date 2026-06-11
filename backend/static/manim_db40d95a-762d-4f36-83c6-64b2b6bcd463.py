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

# Legacy Compatibility 
TextMobject = Text
TexMobject = Tex
ShowCreation = Create
ApplyMethod = lambda m, *args, **kwargs: m.animate.method(*args, **kwargs) if hasattr(m, 'animate') else m
ReplacementTransform = Transform

# Monkey-patch to prevent crashes
Line.bend = lambda self, *args, **kwargs: self
Mobject.set_color_by_gradient = lambda self, *args, **kwargs: self

class MainScene(Scene):
    def construct(self):
        self.intro_section()
        self.explanation_section()
        self.demonstration_section()
        self.solution_section()

    def intro_section(self):
        title = Text("Fixing the VGroup TypeError", color=BLUE).scale(0.8)
        error_msg = Text(
            'TypeError: Only values of type VMobject can be added\nas submobjects of VGroup...',
            color=RED,
            line_spacing=0.8
        ).scale(0.5)
        
        self.play(Write(title))
        self.wait(1)
        self.play(title.animate.to_edge(UP))
        self.play(FadeIn(error_msg))
        self.wait(2)
        
        self.play(FadeOut(error_msg), FadeOut(title))

    def explanation_section(self):
        header = Text("The Hierarchy", color=YELLOW).to_edge(UP)
        self.play(Write(header))

        # Hierarchy Diagram using VGroups (as these are all VMobjects)
        mobject_box = Rectangle(height=1.5, width=4, color=WHITE)
        mobject_text = Text("Mobject").scale(0.7)
        m_group = VGroup(mobject_box, mobject_text)

        vmobject_box = Rectangle(height=1.5, width=3, color=BLUE)
        vmobject_text = Text("VMobject").scale(0.6)
        vm_group = VGroup(vmobject_box, vmobject_text)
        vm_group.next_to(m_group, DOWN, buff=1).shift(LEFT * 2)

        image_box = Rectangle(height=1.5, width=3, color=GREEN)
        image_text = Text("ImageMobject").scale(0.6)
        i_group = VGroup(image_box, image_text)
        i_group.next_to(m_group, DOWN, buff=1).shift(RIGHT * 2)

        arrow_vm = Arrow(m_group.get_bottom(), vm_group.get_top(), color=GRAY)
        arrow_im = Arrow(m_group.get_bottom(), i_group.get_top(), color=GRAY)

        self.play(FadeIn(m_group))
        self.wait(0.5)
        self.play(
            Create(arrow_vm),
            Create(arrow_im),
            FadeIn(vm_group),
            FadeIn(i_group)
        )
        self.wait(2)

        vm_label = Text("Shapes, Text, MathTex", color=BLUE).scale(0.4).next_to(vm_group, DOWN)
        im_label = Text("Bitmaps, Rasters", color=GREEN).scale(0.4).next_to(i_group, DOWN)
        
        self.play(Write(vm_label), Write(im_label))
        self.wait(2)

        self.play(FadeOut(VGroup(header, m_group, vm_group, i_group, arrow_vm, arrow_im, vm_label, im_label)))

    def demonstration_section(self):
        section_title = Text("The Problem: VGroup Constraint", color=RED).scale(0.7).to_edge(UP)
        self.play(Write(section_title))

        circle = Circle(color=BLUE).shift(LEFT * 2)
        circle_label = Text("Circle (VMobject)").scale(0.4).next_to(circle, DOWN)
        
        # Representing a non-VMobject (like an ImageMobject)
        # We use a Rectangle visually, but treat it as a generic Mobject conceptually
        rect = Rectangle(color=GREEN).shift(RIGHT * 2)
        rect_label = Text("ImageMobject (Non-VMobject)", color=GREEN).scale(0.4).next_to(rect, DOWN)

        self.play(
            Create(circle), Write(circle_label),
            FadeIn(rect), Write(rect_label)
        )
        self.wait(1)

        vgroup_fail = Text("VGroup(circle, image) --> CRASH", color=RED).scale(0.8).shift(UP * 0.5)
        reason = Text("VGroup requires ALL items to be VMobjects.", color=WHITE).scale(0.5).next_to(vgroup_fail, DOWN)

        self.play(Write(vgroup_fail))
        self.play(Indicate(vgroup_fail))
        self.play(Write(reason))
        self.wait(2)

        self.play(FadeOut(VGroup(section_title, circle, circle_label, rect, rect_label, vgroup_fail, reason)))

    def solution_section(self):
        header = Text("The Solution: Use Group", color=GREEN).to_edge(UP)
        self.play(Write(header))

        circle = Circle(color=BLUE)
        rect = Rectangle(color=GREEN) # Simulating a non-vectorized object
        
        # FIX: Use Group() instead of VGroup()
        # Group is the generic container for any Mobject subclass
        my_group = Group(circle, rect).arrange(RIGHT, buff=1)
        
        code_fix = Text("Group(circle, image_mobject)", font="Monospace", color=YELLOW).scale(0.6).shift(UP * 2)
        desc = Text("Group is the universal container for all Mobjects.", color=GRAY).scale(0.5).next_to(code_fix, DOWN)

        self.play(Write(code_fix))
        self.play(Write(desc))
        self.wait(1)
        
        # CRITICAL FIX: Use FadeIn instead of Create for general Groups 
        # to avoid NotImplementedError on non-vectorized children
        self.play(FadeIn(my_group))
        self.play(my_group.animate.scale(0.5).shift(DOWN * 1))
        
        highlight = Rectangle(color=YELLOW, height=2, width=6).surround(my_group)
        success_text = Text("Success! Compatible with all types.", color=YELLOW).scale(0.5).next_to(highlight, DOWN)
        
        self.play(Create(highlight))
        self.play(Write(success_text))
        self.wait(3)

        self.play(FadeOut(Group(*self.mobjects)))