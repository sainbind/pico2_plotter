# python
# File: `Source/time_compat.py`
# Compatibility wrapper: time, fall back to MicroPython's utime.
try:
    import utime as timing
except ImportError:
    import time as timing  # MicroPython

# Provide a fallback ticks_ms() when the imported timing module doesn't have it.
if not hasattr(timing, "ticks_ms"):
    def _ticks_ms():
        # use time.time() -> seconds to compute milliseconds
        return int(timing.time() * 1000)
    timing.ticks_ms = _ticks_ms

if not hasattr(timing, "ticks_diff"):
    def _ticks_diff(end, start):
        return int(end) - int(start)
    timing.ticks_diff = _ticks_diff

if not hasattr(timing, "sleep_us"):
    def _sleep_us(microseconds):
        timing.sleep(microseconds / 1000000)
    timing.sleep_us = _sleep_us

def tick_millis():
    """Return the current time in milliseconds."""
    return timing.ticks_ms()

def ticks_diff(end, start):
   return timing.ticks_diff(end, start)

def sleep_secs(seconds):
    timing.sleep(seconds)

def sleep_micros(microseconds):
    timing.sleep_us(microseconds)