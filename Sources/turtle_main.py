# Main file for running drawing gcode using Turtle Graphic
# Use the .venv_turtle virtualenv to run this file, which will install the turtle module
# Scott Ainbinder
# 07-Feb-2026
import serial
from turtle_gcode_machine import TurtleGCodeMachine
from gcode_interpreter import GcodeInterpreter, FileIO, UARTIO
from gcode_machine import relative_draw

class PySerialAdapter:
    def __init__(self, device, baud=115200, timeout=0.1):
        self.s = serial.Serial(device, baud, timeout=timeout)

    def any(self):
        # pyserial provides in_waiting
        try:
            return self.s.in_waiting > 0
        except Exception:
            return False

    def readline(self):
        # return bytes like MicroPython uart.readline()
        return self.s.readline()  # bytes

    def write(self, b):
        if isinstance(b, str):
            b = b.encode()
        return self.s.write(b)

# 50 Scale seems to give each box about 1 cm square and 5 stes per mm
turtle_machine = TurtleGCodeMachine(5,0,1000,1000, 50)
# Slow it down so it is easier to see the movements
turtle_machine.trace_mode(True)


# Start serial ports using socat and Univeral Gcode Sender (UGS) to send gcode commands from UGS to this script
# socat -v -x  PTY,link=/tmp/ttyV0,raw,echo=0 PTY,link=/tmp/ttyV1,raw,echo=0 2>&1 | tee serial_log.txt
#

isSerial = True
if isSerial:
    ser = PySerialAdapter('/tmp/ttyV0', 115200)
    io = UARTIO(ser)          # your UARTIO accepts an object with .any, .readline, .write
    # io = FileIO("./absolute.gcode")
    interpreter = GcodeInterpreter(turtle_machine, io, use_polling=True)
else:
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
