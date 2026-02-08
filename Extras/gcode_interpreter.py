# Refactoring from Kevin McAleer
# Pico Plotter Project
#
# 28 June 2025

import sys, select

from time_compat import tick_millis, ticks_diffs, sleep_secs
from enum import StrEnum
from point import Point
from turtle_gcode_machine import TurtleGCodeMachine

class GcodeInterpreter:


    IDLE_RESET_MS = 8000  # if no '?' for this long, treat as new session
    REQ_INTERVAL_MS = 1500  # max gap between two '?' for banner trigger
    STATUS_INTERVAL_MS = 2000  # send idle status every 2s after banner

    class GCodeCommands(StrEnum):
        G0 = "g0"
        G00 = "g00"
        G1 = "g1"
        G01 = "g01"
        G02 = "g02"
        G2 = "g2"
        G03 = "g03"
        G3 = "g3"
        G28 = "g28"
        G90 = "g90"
        G91 = "g91"
        M30 = "m30"
        JOG = "j="
        UNLOCK = "$x"
        SETTINGS = "$$"
        HOME = "$h"
        HELP = "$"
        INFO = "$i"
        STATUS = "?"
        FILE_BOUNDARY = "%"

    commands = (

        ("g00 [x?] [y?]", "Rapid move, no printing"),
        ("g01 [x?] [y?]", "Slow move straight line with printing"),
        # ("g02 X10 Y7 I0 J-5", "Clockwise circle with x,y using center point I, Y as offset from starting point x, y"),
        ("g02 x10 y7 r5", "Clockwise circle to x,y from starting point using radius R"),
        ("g03", "Counter-clockwise, same params as g02"),
        ("g28", "Return home"),
        ("g90", "Switch to absolute mode"),
        ("g91", "Switch to incremental mode"),
        ("m30", "End of program"),
        ("g0 [x?] [y?]", "GRBL rapid move, no printing"),
        ("g1 [x?] [y?]", "GRBL Line to x,y. Same as g01"),
        ("g3", "GRBL Counter-clockwise, same params as g02"),
        ("g2", "GRBL Clockwise, same params as g02"),
        ("$h", "GRBL return home"),
        ("$x", "GRBL unlock"),
        ("$j", "GRBL jog, same x y params as g0"),
        ("$i", "GRBL info"),
        ("$$", "GRBL Settings"),
        ("?", "GRBL status report"),
        ("$", "Help"),
        ("%", "Begin and end of file")
    )

    def __init__(self, machine, use_polling=False):
        self.machine = machine
        self.banner_sent = False
        self.question_counter = 0
        self.last_question_time = 0
        self.last_status_time = tick_millis()
        self.now = tick_millis()
        self.use_polling = use_polling

        if use_polling:
            sleep_secs(1)
            self.poller = select.poll()
            self.poller.register(sys.stdin, select.POLLIN)
        else:
            self.poller = None

    def _send_status(self):
        return "<Idle|MPos:{:.3f},{:.3f},{:.3f}|FS:0,0>\r\n".format(
                self.machine.absolute_x , self.machine.absolute_y, -1 if self.machine.is_pendown else 0
            )


    def _banner(self):

        # Send the banner plus three status reports and trailing ok.
        statuses = "".join(self._send_status() for _ in range(3))
        banner = "Grbl 1.1f ['$' for help]\r\n<Idle|MPos:0.000,0.000,0.000|FS:0,0>\r\nMSG: '$X' to unlock]\r\n"
        sys.stdout.write(banner + statuses + "ok\r\n")
        self.banner_sent = True
        self.last_status_time = tick_millis()

    def _soft_reset(self):
        self.banner_sent = False

    @staticmethod
    def _unlock():
        """Unlock response on $X"""
        sys.stdout.write("[MSG:Caution: Unlocked]\r\nok\r\n")

    @staticmethod
    def _settings():
        """response to a $$ command"""
        grbl_settings = (
            (0, 10, "Step pulse, usec"),
            (1, 25, "Step idle delay, msec"),
            (2, 0, "Step port invert mask"),
            (3, 0, "Dir port invert mask"),
            (4, 0, "Step enable invert, bool"),
            (5, 0, "Limit pins invert, bool"),
            (6, 0, "Probe pin invert, bool"),
            (10, 3, "Status report mask"),
            (11, 0.010, "Junction deviation, mm"),
            (12, 0.002, "Arc tolerance, mm"),
            (13, 0, "Report in inches, bool"),
            (20, 0, "Soft limits enable, bool"),
            (21, 0, "Hard limits enable, bool"),
            (22, 0, "Homing cycle enable, bool"),
            (23, 0, "Homing dir invert mask"),
            (24, 25.0, "Homing feed, mm/min"),
            (25, 500.0, "Homing seek, mm/min"),
            (26, 250, "Homing debounce, msec"),
            (27, 1.000, "Homing pull-off, mm"),
            (30, 1000, "Max spindle speed, RPM"),
            (31, 0, "Min spindle speed, RPM"),
            (32, 1, "Laser-mode enable, bool"),
        )
        sys.stdout.write("".join(f"${key}={val} ({desc})\r\n" for (key, val, desc) in grbl_settings) + "ok\r\n")

    @staticmethod
    def _help():
        sys.stdout.write( "".join(f"{key}: {value}\r\n" for (key, value) in GcodeInterpreter.commands))

    @staticmethod
    def _info():
        sys.stdout.write("[VER:MicroPythonGRBL:1.1]\r\n")
        sys.stdout.write("[OPT:MPY,USB,3AXIS]\r\n")
        sys.stdout.write("ok\r\n")

    def _status(self):
        # Determine if this '?' arrived within the quick-request window
        since_last_question = ticks_diffs(self.now, self.last_question_time)
        quick_request = since_last_question < GcodeInterpreter.REQ_INTERVAL_MS

        if quick_request:
            self.question_counter += 1
        else:
            self.question_counter = 1

        # Record when this question arrived
        self.last_question_time = self.now

        # On the second quick `?`, fire the banner if needed
        if not self.banner_sent and self.question_counter >= 2:
            self._banner()
            self.question_counter = 0
            return

        # After banner has been shown, throttle status replies by STATUS_INTERVAL_MS
        if self.banner_sent and ticks_diffs(self.now, self.last_status_time) > GcodeInterpreter.STATUS_INTERVAL_MS:
            sys.stdout.write(self._send_status())
            self.last_status_time = self.now


    def interpret(self):

        try:
            while True:
                self.now = tick_millis()

                # If no '?' for a while, assume UGS reconnected → reset banner logic
                if self.banner_sent and ticks_diffs(self.now, self.last_question_time) > GcodeInterpreter.IDLE_RESET_MS:
                    self.banner_sent  = False
                    self.question_counter = 0

                line = None
                # Non-blocking mode: check for input, otherwise allow periodic tasks
                if self.use_polling:
                    events = self.poller.poll(0)
                    if not events:
                        # Optionally emit periodic idle status after banner
                        if self.banner_sent and ticks_diffs(self.now,
                                                            self.last_status_time) > GcodeInterpreter.STATUS_INTERVAL_MS:
                            sys.stdout.write(self._send_status())
                            self.last_status_time = self.now
                        sleep_secs(0.01)
                        continue
                    # Read a single line (poll indicated input available)
                    line = sys.stdin.readline()
                    if line == "":
                        # EOF on stdin
                        break
                    line = line.rstrip("\r\n")
                else:
                    # Blocking read; will wait for a line from the host
                    try:
                        line = input("")
                    except EOFError:
                        break

                # Update last_question_time if this looks like a status request
                stripped = (line or "").strip()
                if stripped.startswith("?"):
                    self.last_question_time = self.now

                # Dispatch the line to the gcode handler
                try:
                    if stripped:
                        self.gcode(stripped)
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    sys.stdout.write("error: {}\r\n".format(e))

        except KeyboardInterrupt:
            # clean exit on Ctrl-C
            pass

        finally:
            # Ensure machine is properly shut down
            try:
                self.machine.end()
            except Exception:
                pass

    def _parse_command_params(self, sub_commands):

        x = y = z = r = None
        for sub_command in sub_commands:
            if sub_command.startswith("x"):
                x = float(sub_command[1:])
            elif sub_command.startswith("y"):
                y = float(sub_command[1:])
            elif sub_command.startswith("z"):
                z = float(sub_command[1:])
            elif sub_command.startswith("r"):
                r = float(sub_command[1:])

        if self.machine.relative_mode:
            x = 0 if x is None else x
            y = 0 if y is None else y
        else:
            x = self.machine.absolute_x if x is None else x
            y = self.machine.absolute_y if y is None else y

        return {'x': x, 'y': y, 'z': z, 'r': r}

    def gcode(self, command):

        command = (command or "").split(';', 1)[0].rstrip().lower()  # Remove comments and trailing whitespace
        if not command: return
        sub_commands = command.split()

        try:
            sub_command = GcodeInterpreter.GCodeCommands(sub_commands[0])
        except ValueError:
            sys.stdout.write(f"Unknown G-code command: {command}\r\n")
            return

        match sub_command:
            case GcodeInterpreter.GCodeCommands.G00 | GcodeInterpreter.GCodeCommands.G0 | GcodeInterpreter.GCodeCommands.JOG:
                params = self._parse_command_params(sub_commands[1:])
                self.machine.penup()
                self.machine.move(params['x'], params['y'])
                sys.stdout.write("ok\r\n")
            case GcodeInterpreter.GCodeCommands.G01 | GcodeInterpreter.GCodeCommands.G1:
                params = self._parse_command_params(sub_commands[1:])
                self.machine.pendown()
                self.machine.move(params['x'], params['y'])
                sys.stdout.write("ok\r\n")
            case GcodeInterpreter.GCodeCommands.G02 | GcodeInterpreter.GCodeCommands.G2:
                params = self._parse_command_params(sub_commands[1:])
                self.machine.circle(Point(params['x'], params['y']), params['r'], is_clockwise=True)
                sys.stdout.write("ok\r\n")
            case GcodeInterpreter.GCodeCommands.G03 | GcodeInterpreter.GCodeCommands.G3:
                params = self._parse_command_params(sub_commands[1:])
                self.machine.circle(Point(params['x'], params['y']), params['r'], is_clockwise=False)
                sys.stdout.write("ok\r\n")
            case GcodeInterpreter.GCodeCommands.G28 | GcodeInterpreter.GCodeCommands.HOME:
                self.machine.home()
                sys.stdout.write("ok\r\n")
            case GcodeInterpreter.GCodeCommands.G90:
                self.machine.relative_mode = False
                sys.stdout.write("ok\r\n")
            case GcodeInterpreter.GCodeCommands.G91:
                self.machine.relative_mode = True
                sys.stdout.write("ok\r\n")
            case GcodeInterpreter.GCodeCommands.M30:
                raise KeyboardInterrupt
            case GcodeInterpreter.GCodeCommands.STATUS:
                self._status()
            case GcodeInterpreter.GCodeCommands.SETTINGS:
                GcodeInterpreter._settings()
            case GcodeInterpreter.GCodeCommands.INFO:
                GcodeInterpreter._info()
            case GcodeInterpreter.GCodeCommands.HELP:
                GcodeInterpreter._help()
            case GcodeInterpreter.GCodeCommands.UNLOCK:
                GcodeInterpreter._unlock()
            case _:
                sys.stdout.write(f"Unknown G-code command: {command}")

# 50 Scale seems to give each box about 1 cm square and 5 stes per mm
turtle_machine = TurtleGCodeMachine(5,0,1000,1000, 50)
turtle_machine.trace_mode(True)
interpreter = GcodeInterpreter(turtle_machine)
interpreter.interpret()
