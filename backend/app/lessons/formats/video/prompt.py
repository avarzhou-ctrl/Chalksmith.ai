VIDEO_RULES = """
Return a complete Python Manim Community scene. Define exactly one Scene subclass named
GeneratedScene and import Manim with `from manim import *`. Organize the animation into a brief
opening, two or three logically connected explanations, and a recap. Prefer native geometric
primitives, graphs, arrows, and short Text labels. Keep all objects inside a 16:9 frame and avoid
simultaneous clutter. Use Text and Unicode symbols instead of Tex, MathTex, Code, images, or SVG
assets. Do not access the network, filesystem, environment, subprocesses, runtime internals, or
user input.
"""
