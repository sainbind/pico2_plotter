import math
from point import Point
from logging_compat import get_logger, logging


class GCodeMachine:


    def __init__(self, steps_per_mm = 10, step_delay_us = 100, rounding_precision=0, line_increment=0.25):
        self.absolute_x = 0
        self.absolute_y = 0
        self.is_pendown = False
        self.relative_mode = False
        self.banner_sent = False
        self.steps_per_mm = steps_per_mm
        self.step_delay_us = step_delay_us
        # rounding precision of 0 for large rounding, 1 for  better precision
        self.rounding_precision = rounding_precision
        # line increment of 1 is very coarse, 0.25 is very fine
        self.line_increment = line_increment
        logging.basicConfig(level=logging.INFO)
        self.logger = get_logger("gcode_machine")



    def line(self, end_point):
        start_point = self.current_point()
        ending_point = end_point.add(start_point) if self.relative_mode else end_point
        self.logger.debug("Line start: %s, end: %s, point: %s", start_point, ending_point, end_point)
        points = start_point.bresenham_line(ending_point, self.line_increment)
        for point in points:
            next_point = point.subtract(self.current_point()) if self.relative_mode else end_point
            self.move(next_point.x, next_point.y)

    def circle(self, end_point, radius, is_clockwise=True):
        """
        Draw a circle arc from the current point to end_point with given radius.
        Uses is_clockwise to choose sweep direction and is robust to zero-length arcs.
        """
        start_point = self.current_point()
        ending_point = start_point.add(end_point) if self.relative_mode else end_point
        center_point = start_point.circle_center(ending_point, radius, is_clockwise)
        mid_point = start_point.midpoint(ending_point)
        start_angle = start_point.angle(center_point)
        end_angle = ending_point.angle(center_point)
        start_point_vector = start_point.vector(center_point)
        end_point_vector = ending_point.vector(center_point)

        self.logger.debug(f"mid: {mid_point}")
        self.logger.debug(f"center: {center_point}")
        self.logger.debug(f"start_angle: {start_angle:.2f}, end_angle: {end_angle:.2f}")
        self.logger.debug(f"start_degrees: {start_angle * 180 / math.pi:.2f}, end_degrees: {end_angle * 180 / math.pi:.2f}")
        self.logger.debug(f"v1: {start_point_vector}, v2: {end_point_vector}")
        self.logger.debug(f"center to mid distance: {center_point.distance(mid_point):.2f}")

        # normalize delta to (-pi, pi]
        delta = end_angle - start_angle
        delta = (delta + math.pi) % (2.0 * math.pi) - math.pi

        # pick sweep direction according to is_clockwise
        if is_clockwise:
            sweep = delta - (2.0 * math.pi) if delta > 0 else delta
        else:
            sweep = delta + (2.0 * math.pi) if delta < 0 else delta

        arc_length = abs(sweep) * abs(radius)
        # if arc is effectively zero, just move to the endpoint
        if arc_length < 1e-9:
            next_point = self.current_point().subtract(ending_point) if self.relative_mode else ending_point
            next_point.round(self.rounding_precision)
            self.move(next_point.x, next_point.y)
            return

        steps = int(math.floor(arc_length * self.steps_per_mm))
        if steps <= 0:
            # ensure at least one sampling step if arc length small
            steps = 1

        # Streamed generation to avoid allocating a list of Point objects
        # First pass: find the first emitted (rounded) sample and remember whether
        # a final endpoint needs to be appended.

        first_x = first_y = None
        last_emitted_x = last_emitted_y = None
        emitted_any = False

        for n in range(steps):
            t = n / float(steps)
            theta = start_angle + t * sweep
            x = center_point.x + abs(radius) * math.cos(theta)
            y = center_point.y + abs(radius) * math.sin(theta)
            # apply rounding precision semantics from original implementation
            rx = round(x, self.rounding_precision)
            ry = round(y, self.rounding_precision)

            if emitted_any and rx == last_emitted_x and ry == last_emitted_y:
                continue

            if not emitted_any:
                first_x, first_y = rx, ry

            last_emitted_x, last_emitted_y = rx, ry
            emitted_any = True

        # ensure final endpoint is considered
        final_rx = round(ending_point.x, self.rounding_precision)
        final_ry = round(ending_point.y, self.rounding_precision)
        final_needed = not emitted_any or (final_rx != last_emitted_x or final_ry != last_emitted_y)

        if not emitted_any and not final_needed:
            # nothing to draw
            return

        # Move to start of arc
        self.penup()
        if emitted_any:
            # compute move to first sample
            if self.relative_mode:
                dx = first_x - self.absolute_x
                dy = first_y - self.absolute_y
                self.move(dx, dy)
            else:
                self.move(first_x, first_y)
        else:
            # No sampled points, just move to final endpoint
            if self.relative_mode:
                dx = final_rx - self.absolute_x
                dy = final_ry - self.absolute_y
                self.move(dx, dy)
            else:
                self.move(final_rx, final_ry)

        # draw remaining points
        self.pendown()

        # Second pass: recompute and emit moves (skip the first emitted sample)
        emitted_count = 0
        last_emitted_during_draw_x = None
        last_emitted_during_draw_y = None

        for n in range(steps):
            t = n / float(steps)
            theta = start_angle + t * sweep
            x = center_point.x + abs(radius) * math.cos(theta)
            y = center_point.y + abs(radius) * math.sin(theta)
            rx = round(x, self.rounding_precision)
            ry = round(y, self.rounding_precision)

            if emitted_count > 0 and rx == last_emitted_during_draw_x and ry == last_emitted_during_draw_y:
                continue

            # this is an emitted sample
            if emitted_count == 0:
                # skip the first because we already moved to it (penup->move)
                emitted_count += 1
                last_emitted_during_draw_x, last_emitted_during_draw_y = rx, ry
                continue

            # compute relative delta if needed at moment of move so current position is accounted
            if self.relative_mode:
                dx = rx - self.absolute_x
                dy = ry - self.absolute_y
                self.move(dx, dy)
            else:
                self.move(rx, ry)

            last_emitted_during_draw_x, last_emitted_during_draw_y = rx, ry
            emitted_count += 1

        # finally, ensure final endpoint is reached
        if final_needed:
            if self.relative_mode:
                dx = final_rx - self.absolute_x
                dy = final_ry - self.absolute_y
                self.move(dx, dy)
            else:
                self.move(final_rx, final_ry)


    def dot(self, point):
        pass

    def move(self, x = None, y = None):
        pass

    def end(self):
        self.penup()

    def home(self):
        pass


    def penup(self):
        pass

    def pendown(self):
        pass


    def current_point(self):
        return Point(self.absolute_x, self.absolute_y)



def relative_draw(machine):
    # using relative positions to test out drawing
    machine.home()
    machine.relative_mode = True

    # box
    machine.penup()
    machine.move(50, 80)
    machine.pendown()
    machine.line(Point(40, 0))
    machine.line(Point(0, -40))
    machine.line(Point(-40, 0))
    machine.line(Point(0, 40))

    # circle in the box
    machine.penup()
    machine.move(20, -50)
    machine.pendown()
    machine.circle(Point(.1, 0), 30, True)

    # 2 diagonal lines
    machine.penup()
    machine.move(0, 10)
    machine.pendown()
    machine.line(Point(-20, 40))
    machine.penup()
    machine.line(Point(20, -40))
    machine.pendown()
    machine.line(Point(20, 40))

    machine.home()
    machine.end()



