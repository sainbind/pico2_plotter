# Main file for running drawing gcode using Turtle Graphic
# Use the .venv_turtle virtualenv to run this file, which will install the turtle module
# Scott Ainbinder
# 07-Feb-2026

from mplot_gcode_machine import MplotGCodeMachine
from gcode_interpreter import GcodeInterpreter
from gcode_machine import relative_draw



mplot_machine = MplotGCodeMachine(5, 0, 10, 10, 1)

# Attach the gcode interpreter to the turtle machine
interpreter = GcodeInterpreter(mplot_machine)

# either manually type in gcode commands or read from standard input
# absolute.gcode uses absolute positioning, relative.gcode uses relative positioning
#
# cd Sources
# ../.venv_turtle/bin/python mlot_main.py < absolute.gcode
#
interpreter.interpret()

# similar results can be achieved by directly calling the drawing functions
# without going through the gcode interpreter
#relative_draw(mplot_machine)
