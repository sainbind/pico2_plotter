# Lightweight mock of MicroPython 'machine' module for host-side testing

class Pin:
    IN = 0
    OUT = 1
    PULL_UP = 2

    def __init__(self, pin_id, mode=OUT, pull=None):
        self.pin_id = pin_id
        self.mode = mode
        self.pull = pull
        # default value: high for inputs with pull-up, else low
        if self.mode == Pin.IN and self.pull == Pin.PULL_UP:
            self._value = 1
        else:
            self._value = 0

    def value(self, val=None):
        """Get or set the pin value. If val is None, return current value.
        Accepts 0/1 or False/True.
        """
        if val is None:
            return self._value
        # setter
        self._value = 1 if val else 0


class WDT:
    def __init__(self, timeout=5000):
        self.timeout = timeout

    def feed(self):
        # no-op for host
        pass

# Provide a minimal hardware RTC/Timer if some code expects it
class Timer:
    def __init__(self, id=None):
        self.id = id

    def init(self, *args, **kwargs):
        pass

    def deinit(self):
        pass
