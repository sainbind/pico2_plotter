import sys
import io

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
