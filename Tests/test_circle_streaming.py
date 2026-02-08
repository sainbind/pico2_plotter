import math
import sys
import os
# Ensure Sources directory is on path for imports during tests
ROOT = os.path.dirname(os.path.dirname(__file__))
SOURCES = os.path.join(ROOT, 'Sources')
if SOURCES not in sys.path:
    sys.path.insert(0, SOURCES)

from gcode_machine import GCodeMachine
from point import Point


class DummyMachine(GCodeMachine):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.moves = []

    def penup(self):
        # no-op for test
        pass

    def pendown(self):
        # no-op for test
        pass

    def move(self, x=None, y=None):
        # simulate updating absolute position
        # treat inputs as absolute positions when provided as Points; otherwise numeric
        if isinstance(x, Point):
            self.absolute_x = x.x
            self.absolute_y = x.y
            self.moves.append((self.absolute_x, self.absolute_y))
            return
        if x is None and y is None:
            return
        # if call comes with relative coordinates we will add them
        self.absolute_x = x
        self.absolute_y = y
        self.moves.append((self.absolute_x, self.absolute_y))


def test_circle_streaming_runs_without_allocating_list():
    # Use low resolution for quick test
    m = DummyMachine(steps_per_mm=1, step_delay_us=0)
    # start at 0,0
    assert (m.absolute_x, m.absolute_y) == (0, 0)
    # draw a quarter circle to (10,0) with radius 10 (should sample a few points)
    m.circle(Point(10, 0), 10, is_clockwise=True)
    # ensure some moves were recorded
    assert len(m.moves) > 0
    # final position should be at or very near (10,0)
    fx, fy = m.moves[-1]
    assert abs(fx - 10) < 1e-6
    assert abs(fy - 0) < 1e-6
