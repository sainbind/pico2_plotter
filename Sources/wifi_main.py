import sys
import io
import asyncio
from stepper_gcode_machine import StepperGCodeMachine
from gcode_interpreter import GcodeInterpreter, IOBase
from microdot import Microdot

import network

## This class in no longer required,
class RestIO(IOBase):

    def __init__(self):
        self.text_buffer = io.StringIO()
        self._read_pos = 0

    def reset(self):
        self.text_buffer = io.StringIO()
        self._read_pos = 0

    # This method was designed to be called in the interpreter.interpret() loop.
    # It is now not used since the rest server calls interpreter.gcode() directly.
    def read_line(self, blocking=False):
        buf = self.text_buffer

        if not blocking:
            buf.seek(0, 2)
            end = buf.tell()
            if end <= self._read_pos:
                return None
            buf.seek(self._read_pos)
            raw = buf.readline()
            if not raw or not raw.endswith('\n'):  # no b prefix - it's a str now
                return None
            self._read_pos = buf.tell()
            return raw.rstrip('\r\n')
        else:
            import time
            while True:
                buf.seek(0, 2)
                end = buf.tell()
                if end > self._read_pos:
                    buf.seek(self._read_pos)
                    raw = buf.readline()
                    if raw and raw.endswith('\n'):
                        self._read_pos = buf.tell()
                        return raw.rstrip('\r\n')
                time.sleep(0.01)

    def any(self) -> bool:
        try:
            buf = self.text_buffer
            buf.seek(0, 2)
            end = buf.tell()
            return end > self._read_pos
        except Exception:
            return False

    def write(self, s: str):
        try:
            sys.stdout.write(s)
        except Exception:
            pass

class RestSerialServer:

    def __init__(self, interpreter: GcodeInterpreter):
        # store the bytes buffer (do NOT shadow the io module name)
        self.port = 5000
        self.interpreter = interpreter
        self.app = Microdot()

    async def start_server(self, debug=False):
        self._register_routes()
        await self.app.start_server(debug=debug, port=self.port)

    def _process_command(self, text: str) -> str:

        if not text:
            return ""

        output = ""
        text = text.replace('\\n', '\n')
        lines = text.split('\n')
        try:
            for line in lines:
                if line:
                    s = line
                    result = self.interpreter.gcode(s)
                    output = output + line + ":\n" +  result + "\n"
        except KeyboardInterrupt:
            output = output + "\nEnding Server\n"

        return output


    def _register_routes(self):
        app = self.app
        server = self

        @app.route('/')
        async def index(request):
            return 'Ready to support / and  /run_all'


        @app.route("/run_all", methods=["POST"])
        async def readlines_route(request):
            try:
                # Request body is plain text with newlines embedded
                text = request.body.decode('utf-8') if isinstance(request.body, bytes) else str(request.body)
                print("request is\n"+text)
                results = server._process_command(text)
                print(f"results: {results}")
                #return jsonify(result='OK', written=written), 200
                return results, 200, {'Content-Type': 'text/plain'}
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



async def main():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect('Scott Stamford', 'charmatt')
    # wait for connection...
    while not wlan.isconnected():
        await asyncio.sleep(0.5)
    print("\nIP:", wlan.ifconfig()[0])

    #rest_io = RestIO()
    stepper_machine = StepperGCodeMachine(11, 1500)
    interpreter = GcodeInterpreter(stepper_machine, use_polling=True)
    rest_server = RestSerialServer(interpreter)
    rest_server.run(debug=True)



asyncio.run(main())


