# Main file for running drawing on a Pico using a stepper motor and gcode commands
# Download this to Pico to run
# Scott Ainbinder
# 07-Feb-2026


import sys
import machine
import os

from stepper_gcode_machine import StepperGCodeMachine
from gcode_interpreter import GcodeInterpreter, FileIO, UARTIO


def get_gcode_interpreter(uart=None):
    stepper_machine = StepperGCodeMachine(11, 1500)
    try:
        if (uart):
            print("Using UART for input")
            return GcodeInterpreter(stepper_machine, UARTIO(uart), use_polling=True)
        elif len(sys.argv) > 1:
            print("Using file provided in sys.argv: "+sys.argv[1])
            return GcodeInterpreter(stepper_machine,FileIO(sys.argv[1]), use_polling=True)
        else:
            print("Using default file: absolute.gcode")
            return GcodeInterpreter(stepper_machine, FileIO("absolute.gcode"), use_polling=True)

    except OSError as e:
        print("Error loading file for input: "+str(e))
        return None


uart = None
#uart = machine.UART(0, baudrate=115200, tx=17, rx=16)
#os.dupterm(uart)  # keep REPL / prints duplicated to the UART
interpreter = get_gcode_interpreter(uart)
interpreter.interpret()

# similar results can be achieved by directly calling the drawing functions
# without going through the gcode interpreter
#relative_draw(stepper_machine)