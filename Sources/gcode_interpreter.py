# Refactoring from Kevin McAleer
# Pico Plotter Project
# 28 June 2025

import sys, select
from gcode_machine import GCodeMachine
from time_compat import tick_millis, ticks_diff, sleep_secs
#from enum import StrEnum
from point import Point
from logging_compat import get_logger, logging



# IO abstraction layer -----------------------------------------------------
class IOBase:
    """Abstract IO handler. Provide read_line(blocking=True), write(s), any(),
    and optionally get_fileno() for integration with select.poll().
    """
    def read_line(self, blocking=True):
        raise NotImplementedError

    def write(self, s: str):
        raise NotImplementedError

    def any(self) -> bool:
        """Return True if there's data available to read without blocking.
        If not implementable, return True to let caller attempt a read.
        """
        return True

    def get_fileno(self):
        """Return a file descriptor integer usable with select.poll(), or None.
        """
        return None


class StdioIO(IOBase):
    """Standard input/output handler using sys.stdin/sys.stdout.
    Works with both blocking and (with select) non-blocking modes.
    """
    def __init__(self):
        # cached poll object (if poll is available and registration succeeds)
        self._poll = None

    def read_line(self, blocking=True):
        if blocking:
            try:
                return input("")
            except EOFError:
                return None
        else:
            # Non-blocking read; caller should check any() or poll first.
            try:
                line = sys.stdin.readline()
            except Exception:
                return None
            if line == "":
                return None
            return line.rstrip('\n')

    def write(self, s: str):
        try:
            sys.stdout.write(s)
        except Exception:
            # Best-effort: ignore write errors
            pass

    def any(self) -> bool:
        # Prefer a poll-based check when possible (more efficient / scalable).
        try:
            fileno = self.get_fileno()
        except Exception:
            fileno = None

        # Use select.poll where available and we have a fileno
        try:
            if fileno is not None and hasattr(select, 'poll'):
                # Cache a poll object on this StdioIO instance to avoid recreating it each call
                if self._poll is None:
                    try:
                        self._poll = select.poll()
                        self._poll.register(fileno, select.POLLIN)
                    except Exception:
                        # If poll/register fails, clear _poll and fall back
                        self._poll = None
                if self._poll is not None:
                    events = self._poll.poll(0)
                    return bool(events)
        except Exception:
            # Fall through to select.select fallback
            pass

        # Fallback: if poll isn't available or failed, be conservative and assume data may be available
        # (This avoids platform-specific select.select unpacking warnings in static analyzers.)
        return True

    def get_fileno(self):
        try:
            fd = sys.stdin.fileno()
            # sanitize: ensure we got an int
            if isinstance(fd, int) and fd >= 0:
                return fd
            return None
        except Exception:
            return None


class FileIO(IOBase):
    """Read lines from a file path. Writes still go to stdout by default.
    """
    def __init__(self, path, write_to_stdout=True):
        self._lines = []
        self._pos = 0
        self.write_to_stdout = write_to_stdout
        try:
            with open(path, 'r') as f:
                self._lines = [ln.rstrip('\n') for ln in f.readlines()]
        except Exception:
            self._lines = []

    def read_line(self, blocking=True):
        if self._pos >= len(self._lines):
            return None
        val = self._lines[self._pos]
        self._pos += 1
        return val

    def any(self) -> bool:
        return self._pos < len(self._lines)

    def write(self, s: str):
        if self.write_to_stdout:
            try:
                sys.stdout.write(s)
            except Exception:
                pass


class UARTIO(IOBase):
    """Wrap a UART-like object that provides any(), readline(), and write().
    The uart.readline() is expected to return bytes (MicroPython style) or a
    string (pyserial style)."""
    def __init__(self, uart):
        self.uart = uart

    def read_line(self, blocking=True):
        # On typical uart objects, readline() will block until a line is available
        try:
            raw = self.uart.readline()
        except Exception:
            return None
        if raw is None:
            return None
        if isinstance(raw, bytes):
            try:
                return raw.decode().rstrip('\r\n')
            except Exception:
                return raw.decode(errors='ignore').rstrip('\r\n')
        return str(raw).rstrip('\r\n')

    def any(self) -> bool:
        try:
            return bool(self.uart.any())
        except Exception:
            # If underlying UART doesn't expose any(), assume data may be present
            return True

    def write(self, s: str):
        try:
            if hasattr(self.uart, 'write'):
                if isinstance(s, str):
                    b = s.encode()
                else:
                    b = s
                self.uart.write(b)
        except Exception:
            pass




# ...existing code...
class GcodeInterpreter:


    IDLE_RESET_MS = 8000  # if no '?' for this long, treat as new session
    REQ_INTERVAL_MS = 1500  # max gap between two '?' for banner trigger
    STATUS_INTERVAL_MS = 2000  # send idle status every 2s after banner

    ## this class was originally intended to be an Enum, but Python's Enum doesn't support the way I want to look up by string value, so I switched to a regular class with a dict for lookup instead.
    # The StrEnum base is just to get some of the nice features of Enums like immutability and auto string values.
    class GCodeCommands:

        G0 = "g0"
        G00 = "g00"
        G1 = "g1"
        G01 = "g01"
        G02 = "g2"
        G2 = "g2"
        G03 = "g3"
        G3 = "g3"
        G21 = "g21"
        G28 = "g28"
        G90 = "g90"
        G91 = "g91"
        M30 = "m30"
        JOG = "$j="
        UNLOCK = "$x"
        SETTINGS = "$$"
        HOME = "$h"
        HELP = "$"
        INFO = "$i"
        STATE = "$g"
        CHECK = "$c"
        STATUS = "?"
        FILE_BOUNDARY = "%"

        codes = {
        "g0": G0,
        "g00": G00,
        "g1": G1,
        "g01": G01,
        "g02": G02,
        "g2": G2,
        "g03": G03,
        "g3": G3,
        "g21": G21,
        "g28": G28,
        "g90": G90,
        "g91": G91,
        "m30": M30,
        "$j=": JOG,
        "$x": UNLOCK,
        "$$": SETTINGS,
        "$h": HOME,
        "$": HELP,
        "$i": INFO,
        "$g": STATE,
        "$c": CHECK,
        "?": STATUS,
        "%": FILE_BOUNDARY
        }

        def get_command(command_str):
            try:
                return GcodeInterpreter.GCodeCommands.codes[command_str]
            except:
                raise ValueError(f"Unknown G-code command: {command_str}")

    commands = (

        ("g00 [x?] [y?]", "Rapid move, no printing"),
        ("g01 [x?] [y?]", "Slow move straight line with printing"),
        # ("g02 X10 Y7 I0 J-5", "Clockwise circle with x,y using center point I, Y as offset from starting point x, y"),
        ("g02 x10 y7 r5", "Clockwise circle to x,y from starting point using radius R"),
        ("g03", "Counter-clockwise, same params as g02"),
        ("g21", "Set units to millimeters"),
        ("g28", "Return home"),
        ("g90", "Switch to absolute mode"),
        ("g91", "Switch to incremental mode"),
        ("m30", "End of program"),
        ("g0 [x?] [y?]", "GRBL rapid move, no printing"),
        ("g1 [x?] [y?]", "GRBL Line to x,y. Same as g01"),
        ("g3", "GRBL Counter-clockwise, same params as g02"),
        ("g2", "GRBL Clockwise, same params as g02"),
        ("$h", "GRBL return home"),
        ("$g", "GRBL parser state request"),
        ("$x", "GRBL unlock"),
        ("$j", "GRBL jog, same x y params as g0"),
        ("$i", "GRBL info"),
        ("$$", "GRBL Settings"),
        ("?", "GRBL status report"),
        ("$c", "GRBL check mode toggle"),
        ("$", "Help"),
        ("%", "Begin and end of file")
    )

    logging.basicConfig(level=logging.DEBUG)
    logger = get_logger("gcode_interpreter")


    def __init__(self, machine: GCodeMachine, io_handler: IOBase = None, use_polling=False):
        self.machine = machine
        self.banner_sent = False
        self.question_counter = 0
        self.last_question_time = 0
        self.last_status_time = tick_millis()
        self.now = tick_millis()
        self.use_polling = use_polling

        # IO handler: default to standard input/output
        self.io = io_handler if io_handler is not None else StdioIO()

        logging.info(f"G-code interpreter initialized, polling={'enabled' if use_polling else 'disabled'}, io_handler={type(self.io).__name__}")

        # Prepare polling support if requested and supported by the IO handler
        if use_polling:
            # If the io handler exposes a fileno usable with select.poll(), register it
            fileno = None
            try:
                fileno = self.io.get_fileno()
            except Exception:
                fileno = None

            if fileno is not None:
                sleep_secs(1)
                self.poller = select.poll()
                try:
                    self.poller.register(fileno, select.POLLIN)
                except Exception:
                    # If register fails, fall back to no poller and rely on io.any()
                    self.poller = None
            else:
                # No fileno available; we'll rely on io.any() for non-blocking checks
                self.poller = None
        else:
            self.poller = None

    def _send_status(self):
        return "<Idle|MPos:{:.3f},{:.3f},{:.3f}|FS:0,0>\r\n".format(
                self.machine.absolute_x , self.machine.absolute_y, -1 if self.machine.is_pendown else 0
            )

    def _send_state(self):
        distance_mode = "G91" if self.machine.relative_mode else "G90"
        return "[GC:G1 G54 G17 G2 {} G94 M5 M9 T0 S0.0 F500.0]\r\nok\r\n".format(distance_mode)

    def _banner(self):

        # Send the banner plus three status reports and trailing ok.
        statuses = "".join(self._send_status() for _ in range(3))
        banner = "Grbl 1.1f ['$' for help]\r\n<Idle|MPos:0.000,0.000,0.000|FS:0,0>\r\nMSG: '$X' to unlock]\r\n"
        result= banner + statuses + "ok\r\n"
        self.banner_sent = True
        self.last_status_time = tick_millis()
        return result

    def _soft_reset(self):
        self.banner_sent = False

    def _unlock(self):
            return "[MSG:Caution: Unlocked]\r\nok\r\n"


    def _settings(self):
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

        return "".join(f"${key}={val} ({desc})\r\n" for (key, val, desc) in grbl_settings) + "ok\r\n"



    def _help(self):

        return "".join(f"{key}: {value}\r\n" for (key, value) in GcodeInterpreter.commands)


    def _info(self):

        result = "[VER:MicroPythonGRBL:1.1]\r\n"
        result += "[OPT:MPY,USB,3AXIS]\r\n"
        result += "ok\r\n"
        return result

    def _status(self):
        # Determine if this '?' arrived within the quick-request window
        since_last_question = ticks_diff(self.now, self.last_question_time)
        quick_request = since_last_question < GcodeInterpreter.REQ_INTERVAL_MS

        if quick_request:
            self.question_counter += 1
        else:
            self.question_counter = 1

        # Record when this question arrived
        self.last_question_time = self.now

        # On the second quick `?`, fire the banner if needed
        if not self.banner_sent and self.question_counter >= 2:
            result = self._banner()
            self.question_counter = 0
            return result

        # After banner has been shown, throttle status replies by STATUS_INTERVAL_MS
        if self.banner_sent and ticks_diff(self.now, self.last_status_time) > GcodeInterpreter.STATUS_INTERVAL_MS:
            result = self._send_status()
            self.last_status_time = self.now
            return result


    def interpret(self):
        self.logger.info("Interpreting G-code...")
        try:
            while True:
                self.now = tick_millis()

                # If no '?' for a while, assume UGS reconnected → reset banner logic
                if self.banner_sent and ticks_diff(self.now, self.last_question_time) > GcodeInterpreter.IDLE_RESET_MS:
                    self.banner_sent  = False
                    self.question_counter = 0

                # Non-blocking mode: check for input, otherwise allow periodic tasks
                if self.use_polling and self.poller is not None:
                    #self.logger.info("Polling with self poller")
                    events = self.poller.poll(0)
                    if not events:
                        # Optionally emit periodic idle status after banner
                        if self.banner_sent and ticks_diff(self.now,
                                                            self.last_status_time) > GcodeInterpreter.STATUS_INTERVAL_MS:
                            self.io.write(self._send_status())
                            self.last_status_time = self.now
                        sleep_secs(0.01)
                        continue
                    # Read a single line (poll indicated input available)
                    line = self.io.read_line(blocking=False)
                    if line is None:
                        # EOF on stdin or no data
                        self.logger.info("EOF on input polling, exiting interpreter")
                        break
                else:
                    # If we have a non-poller IO, use its any() to check availability

                    if self.use_polling and self.poller is None:
                        #self.logger.info("Polling without self poller")
                        if not self.io.any():
                            # Optionally emit periodic idle status after banner
                            if self.banner_sent and ticks_diff(self.now, self.last_status_time) > GcodeInterpreter.STATUS_INTERVAL_MS:
                                self.io.write(self._send_status())
                                self.last_status_time = self.now
                            sleep_secs(0.01)
                            continue
                        #self.logger.info("About to read line in polling mode without poller...")
                        line = self.io.read_line(blocking=False)
                        sleep_secs(0.01)
                        if line is None:
                            self.logger.info("EOF on input non polling, exiting interpreter")
                            break

                    else:
                        # Blocking read; will wait for a line from the host
                        sleep_secs(0.01)
                        #self.logger.info("Blocking read for line input...")
                        line = self.io.read_line(blocking=True)
                        if line is None:
                            break

                # Update last_question_time if this looks like a status request
                stripped = (line or "").strip()
                if stripped.startswith("?"):
                    self.last_question_time = self.now

                # Dispatch the line to the gcode handler
                try:
                    if stripped:
                        result = self.gcode(stripped)
                        self.io.write(result)
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    self.io.write("error: {}\r\n".format(e))

        except KeyboardInterrupt:
            # clean exit on Ctrl-C
            pass

        finally:
            # Ensure machine is properly shut down
            try:
                self.io.write("ended interpreter\r\n")
                self.machine.end()
            except Exception:
                pass

    def _parse_command_params(self, sub_commands):

        x = y = z = r = abs_mode = None
        for sub_command in sub_commands:
            if sub_command.startswith("x"):
                x = float(sub_command[1:])
            elif sub_command.startswith("y"):
                y = float(sub_command[1:])
            elif sub_command.startswith("z"):
                z = float(sub_command[1:])
            elif sub_command.startswith("r"):
                r = float(sub_command[1:])
            elif sub_command.startswith("g90"):
                abs_mode = True
            elif sub_command.startswith("g91"):
                abs_mode = False

        if self.machine.relative_mode:
            if abs_mode == True:
                # Jog command can use a temp absolute mode when we are normally in relative mode.
                x = self.machine.absolute_x if x is None else x - self.machine.absolute_x
                y = self.machine.absolute_y if y is None else y - self.machine.absolute_y
            else:
                x = 0 if x is None else x
                y = 0 if y is None else y
        else:
            if abs_mode == False:
                # Jog command can use a temp relatvie mode when we are normally in absolute mode.
                x = self.machine.absolute_x + 0 if x is None else x
                y = self.machine.absolute_y + 0 if y is None else y
            else:
                x = self.machine.absolute_x if x is None else x
                y = self.machine.absolute_y if y is None else y

        return {'x': x, 'y': y, 'z': z, 'r': r}

    def split_and_separate_with_spaces(self, command):
        replacements = {"g": " g", "x": " x", "y": " y", "z": " z", "r": " r", "f": " f", "=": "= "}
        # translation_table = str.maketrans(replacements)
        result =  (command or "").split(';', 1)[0].rstrip().lower()  # Remove comments and trailing whitespace
        if len(command) > 2:
            ## translation_table = str.maketrans(replacements)
            ## result = result[0:2] + result[2:].translate(translation_table)  # Ensure spaces before command letters for splitting
            for key, value in replacements.items():
                result = result.replace(key, value)
        return result

    def gcode(self, command):

        command = self.split_and_separate_with_spaces(command)
        if not command: return
        sub_commands = command.split()
        result = ""

        try:
            sub_command = GcodeInterpreter.GCodeCommands.get_command(sub_commands[0])
        except ValueError:
             return f"Unknown G-code command: {command}\r\n"


        ## Originally I used enumStr matching for this, but it's not supported with MicroPython
        #     match sub_command:
        #        case GcodeInterpreter.GCodeCommands.G00 | GcodeInterpreter.GCodeCommands.G0 | GcodeInterpreter.GCodeCommands.JOG:
        #  So I switched to a dict lookup in the GCodeCommands class.
        #  The get_command method will raise a ValueError if the command is not found,

        if sub_command in (GcodeInterpreter.GCodeCommands.G00,
                           GcodeInterpreter.GCodeCommands.G0,
                           GcodeInterpreter.GCodeCommands.JOG):
            params = self._parse_command_params(sub_commands[1:])
            self.machine.penup()
            self.machine.move(params['x'], params['y'])
            #support fine tunning on the pen
            if GcodeInterpreter.GCodeCommands.JOG and params['z'] is not None:
                if params['z'] > 0:
                    self.machine.motor_z.move(40, 1)
                else:
                    self.machine.motor_z.move(abs(params['z']), -1)
            result = "ok\r\n"

        elif sub_command in (GcodeInterpreter.GCodeCommands.G01,
                             GcodeInterpreter.GCodeCommands.G1):
            params = self._parse_command_params(sub_commands[1:])
            self.machine.pendown()
            self.machine.move(params['x'], params['y'])
            result = "ok\r\n"

        elif sub_command in (GcodeInterpreter.GCodeCommands.G02,
                             GcodeInterpreter.GCodeCommands.G2):
            params = self._parse_command_params(sub_commands[1:])
            self.machine.circle(Point(params['x'], params['y']), params['r'], is_clockwise=True)
            result = "ok\r\n"

        elif sub_command in (GcodeInterpreter.GCodeCommands.G03,
                             GcodeInterpreter.GCodeCommands.G3):
            params = self._parse_command_params(sub_commands[1:])
            self.machine.circle(Point(params['x'], params['y']), params['r'], is_clockwise=False)
            result = "ok\r\n"

        elif sub_command == GcodeInterpreter.GCodeCommands.G21:
            result = "ok\r\n"

        elif sub_command in (GcodeInterpreter.GCodeCommands.G28,
                             GcodeInterpreter.GCodeCommands.HOME):
            self.machine.home()
            result = "ok\r\n"

        elif sub_command == GcodeInterpreter.GCodeCommands.G90:
            self.machine.relative_mode = False
            result = "ok\r\n"

        elif sub_command == GcodeInterpreter.GCodeCommands.G91:
            self.machine.relative_mode = True
            result = "ok\r\n"

        elif sub_command == GcodeInterpreter.GCodeCommands.M30:
            raise KeyboardInterrupt

        elif sub_command == GcodeInterpreter.GCodeCommands.STATUS:
           sult = self._status()

        elif sub_command == GcodeInterpreter.GCodeCommands.CHECK:
            result = "ok\r\n"

        elif sub_command == GcodeInterpreter.GCodeCommands.SETTINGS:
            # Call instance method so it uses the configured io handler
            result =self._settings()

        elif sub_command == GcodeInterpreter.GCodeCommands.INFO:
            result = self._info()

        elif sub_command == GcodeInterpreter.GCodeCommands.HELP:
            result = self._help()

        elif sub_command == GcodeInterpreter.GCodeCommands.UNLOCK:
            result = self._unlock()

        elif sub_command == GcodeInterpreter.GCodeCommands.STATE:
            result = "ok\r\n"

        else:
            result =  f"Unknown G-code command: {command}"

        return result
