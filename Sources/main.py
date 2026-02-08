# Main file for running drawing gcode using Turtle Graphic
# Use the .venv_turtle virtualenv to run this file, which will install the turtle module
# Scott Ainbinder
# 07-Feb-2026
#
# Original implementation but uses enumStr and matches instead of if/else statements to parse gcode commands.
# This is more efficient and easier to maintain as more gcode commands are added.

from stepper_gcode_machine import StepperGCodeMachine
from gcode_interpreter import GcodeInterpreter
from gcode_machine import relative_draw



stepper_machine = StepperGCodeMachine(11, 1500)

# Attach the gcode interpreter to the turtle machine
interpreter = GcodeInterpreter(stepper_machine, use_polling=True)

# either manually type in gcode commands or read from standard input
# absolute.gcode uses absolute positioning, relative.gcode uses relative positioning
#
# cd Sources
# ../.venv_turtle/bin/python main.py < relative.gcode
#
interpreter.interpret()

# similar results can be achieved by directly calling the drawing functions
# without going through the gcode interpreter
#relative_draw(stepper_machine)