# Main file for running drawing gcode using Turtle Graphic
# Use the .venv_turtle virtualenv to run this file, which will install the turtle module
# Scott Ainbinder
# 07-Feb-2026

from turtle_gcode_machine import TurtleGCodeMachine
from gcode_interpreter import GcodeInterpreter
from gcode_machine import relative_draw


# 50 Scale seems to give each box about 1 cm square and 5 stes per mm
turtle_machine = TurtleGCodeMachine(5,0,1000,1000, 50)
# Slow it down so it is easier to see the movements
turtle_machine.trace_mode(True)
# Attach the gcode interpreter to the turtle machine
interpreter = GcodeInterpreter(turtle_machine)

# either manually type in gcode commands or read from standard input
# absolute.gcode uses absolute positioning, relative.gcode uses relative positioning
#
# cd Sources
# ../.venv_turtle/bin/python turtle_main.py < absolute.gcode
#
interpreter.interpret()

# similar results can be achieved by directly calling the drawing functions
# without going through the gcode interpreter
#relative_draw(turtle_machine)
