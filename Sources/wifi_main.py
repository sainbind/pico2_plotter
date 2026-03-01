import sys
import io
import asyncio
from stepper_gcode_machine import StepperGCodeMachine
from gcode_interpreter import GcodeInterpreter, IOBase
from microdot import Microdot

import network


class RestIO(IOBase):

    def __init__(self, text_buffer: io.BytesIO):
        # text_buffer is an in-memory bytes buffer (io.BytesIO)
        self.text_buffer = text_buffer

    def read_line(self, blocking=False):
        """Read a single line from the underlying BytesIO and return a decoded
        string (without trailing CR/LF). For non-blocking calls, return None if
        no complete line is available. For blocking calls, wait until a line
        becomes available.
        """
        buf = self.text_buffer
        try:
            if not blocking:
                print("Not blocking, Checking for available data in buffer...")
                # If no data available beyond current position, return None
                pos = buf.tell()
                buf.seek(0, 2)  # SEEK_END
                end = buf.tell()
                buf.seek(pos)
                if end <= pos:
                    return None
                # There is data; attempt to read a line
                raw = buf.readline()
            else:
                # Blocking: wait until a newline-terminated line is available
                print("blocking, Waiting for available data in buffer...")
                raw = buf.readline()
                if not raw or raw.endswith(b"\n") is False:
                    # If readline returned empty bytes (no data yet) or returned
                    # a partial line (shouldn't happen for BytesIO), loop/wait
                    import time
                    while True:
                        pos = buf.tell()
                        buf.seek(0, 2)
                        end = buf.tell()
                        buf.seek(pos)
                        if end > pos:
                            raw = buf.readline()
                            if raw:
                                break
                        time.sleep(0.01)
        except Exception as e:
            print("Error reading from buffer:", e)
            return None

        if not raw:
            return None

        # Decode bytes to text and strip trailing newlines
        try:
            line = raw.decode('utf-8').rstrip('\r\n')
        except Exception:
            line = raw.decode('utf-8', errors='ignore').rstrip('\r\n')

        return line

    def write(self, s: str  ):
        try:
            sys.stdout.write(s)
        except Exception:
            pass

    def any(self) -> bool:
        try:
            buf = self.text_buffer
            pos = buf.tell()
            buf.seek(0, 2) # 2 is SEEK_END
            end = buf.tell()
            buf.seek(pos)
            return end > pos
        except Exception:
            return False

class RestSerialServer:

    def __init__(self, text_buffer: io.BytesIO):
        # store the bytes buffer (do NOT shadow the io module name)
        self.text_buffer = text_buffer
        self.port = 5000
        self.app = Microdot()

    # Shared helper: append text (plain UTF-8) to the underlying bytes buffer.
    def _append_text(self, text: str) -> int:
        """Append lines from `text` to the bytes buffer as UTF-8 lines.
        Returns the number of bytes written.
        """
        if not text:
            return 0
        buf = self.text_buffer
        buf.seek(0, 2) # 2 is SEEK_END
        written = 0
        for line in text.split('\n'):
            if line:
                b = (line + '\n').encode('utf-8')
                buf.write(b)
                written += len(b)
        return written

    # Shared helper: read a single line from the buffer and decode to UTF-8
    def _readline_decoded(self):
        buf = self.text_buffer
        raw = buf.readline() or b""
        if not raw:
            return None
        try:
            return raw.decode('utf-8').rstrip('\r\n')
        except Exception:
            return raw.decode('utf-8', errors='ignore').rstrip('\r\n')

    def _register_routes(self):
        app = self.app
        server = self

        @app.route('/')
        async def index(request):
            return 'Ready to support /run or /run_all'

        @app.route("/run", methods=["GET"])
        async def readline_route(request):
            try:
                line = server._readline_decoded()
                if line is not None:
                    #return jsonify(result='OK', data=line), 200
                    return line, 200, {'Content-Type': 'text/plain'}
                else:
                    #return jsonify(result='OK', data=''), 200
                    return 'OK', 200, {'Content-Type': 'text/plain'}
            except Exception as e:
                #return jsonify(error=str(e)), 500
                return str(e), 500, {'Content-Type': 'text/plain'}


        @app.route("/run_all", methods=["POST"])
        async def readlines_route(request):
            try:
                # Request body is plain text with newlines embedded
                text = request.body.decode('utf-8') if isinstance(request.body, bytes) else str(request.body)
                print("request is\n"+text)
                written = server._append_text(text)
                print(f"Appended {written} bytes to buffer")
                #return jsonify(result='OK', written=written), 200
                return "OK", 200, {'Content-Type': 'text/plain'}
            except Exception as e:
                #return jsonify(error=str(e)), 500
                return str(e), 500, {'Content-Type': 'text/plain'}

    def run(self, debug=False):
        # Ensure routes are registered before running
        try:
            self._register_routes()
        except Exception:
            pass

        if self.app is None:
            raise RuntimeError("Microdot is not installed. Install it with: pip install microdot")

        self.app.run(debug=debug, port=self.port)


def create_rest_server(text_buffer: io.BytesIO = None, use_polling=True):

    if text_buffer is None:
        text_buffer = io.BytesIO(b"?\r\n")
    stepper_machine = StepperGCodeMachine(11, 1500)
    interpreter = GcodeInterpreter(stepper_machine, RestIO(text_buffer),use_polling=use_polling)
    rest_server = RestSerialServer(text_buffer)
    #rest_server.run()
    return rest_server, interpreter, text_buffer


if __name__ == "__main__":
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect('Scott Stamford', 'charmatt')
    status = wlan.ifconfig()
    print("IP: " + status[0])

    text_buffer = io.BytesIO(b"?\r\n")
    rest_server, interpreter, text_buffer = create_rest_server(text_buffer=text_buffer, use_polling=True)
    loop = asyncio.get_event_loop()

    if loop is not None:
        loop.create_task(interpreter.interpret())
        print("Starting REST server in async mode...")
        rest_server.run(debug=True)
    else:
        print("Starting rest server...")
        rest_server.run()
        print("Starting G-code interpreter...")
        interpreter.interpret()
    print("Ending REST server with G-code interpreter...")
    print("Text Buffer content:\n" + text_buffer.getvalue().decode('utf-8'))
