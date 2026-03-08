
import asyncio
from machine import Pin
from stepper_gcode_machine import StepperGCodeMachine
from gcode_interpreter import GcodeInterpreter, IOBase
from microdot import Microdot
import network

# We can use an LED to indicate when the server is running and ready to accept commands
led_pin = Pin(16, Pin.OUT)


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
                line = line.strip()
                if line:
                    s = line
                    print("\nProcessing command: "+s)
                    result = self.interpreter.gcode(s)
                    output = output + line + ":\n" +  (result or "") + "\n"
        except KeyboardInterrupt:
            led_pin.value(0)
            output = output + "\nEnding Server\n"

        return output


    def _register_routes(self):
        app = self.app
        server = self

        @app.route('/')
        async def index(request):
            return 'Ready to support / and  /run'


        @app.route("/run", methods=["POST"])
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
    print(f"Connect using\ncurl -X POST http://{wlan.ifconfig()[0]}:5000/run -d '$' \n")
    led_pin.value(1)
    #rest_io = RestIO()
    stepper_machine = StepperGCodeMachine(11, 1500)
    interpreter = GcodeInterpreter(stepper_machine, use_polling=True)
    rest_server = RestSerialServer(interpreter)

    rest_server.run(debug=True)


if __name__ == "__main__":
    asyncio.run(main())
else:
    asyncio.run(main())


