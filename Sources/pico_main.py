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

stepper_machine = StepperGCodeMachine(11, 1500)

def main(action="serial"):
    """
    Main function for running drawing gcode using Turtle Graphics.
    Args:
        action: str - Type of input mode ('file', 'serial', or None for interactive)
    """

    if action == 'file':
        io = FileIO("./absolute.gcode")
        interpreter = GcodeInterpreter(stepper_machine, io, use_polling=False)
    elif action == 'serial':
        uart = machine.UART(0, baudrate=115200, tx=17, rx=16)
        os.dupterm(uart)            # keep REPL / prints duplicated to the UART
        io = UARTIO(uart)          # your UARTIO accepts an object with .any, .readline, .write
        interpreter = GcodeInterpreter(stepper_machine, io, use_polling=True)
    else:
        print("Running in interactive mode. Use 'file' or 'serial' as argument to specify input mode.")
        interpreter = GcodeInterpreter(stepper_machine)

    interpreter.interpret()

if __name__ == "__main__":
    # Get action from command-line argument or use default "file"
    action = sys.argv[1] if len(sys.argv) > 1 else "xfile"
    main(action)
else:
    main('xfile')