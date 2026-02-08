
from point import Point
from machine import Pin
from gcode_machine import GCodeMachine
from time_compat import sleep_micros

class Motor:

    full_sequence = [
        (1, 1, 0, 0),
        (0, 1, 1, 0),
        (0, 0, 1, 1),
        (1, 0, 0, 1)
    ]
    half_sequence = [
        (1, 0, 0, 0),
        (1, 1, 0, 0),
        (0, 1, 0, 0),
        (0, 1, 1, 0),
        (0, 0, 1, 0),
        (0, 0, 1, 1),
        (0, 0, 0, 1),
        (1, 0, 0, 1)
    ]

    def __init__(self, name, delay_us, mode='full', endstop_direction = None, max_steps = 1200):
        self.name = name
        self.endstop_direction = endstop_direction
        self.max_steps = max_steps
        self.current_step = 0
        self.delay_us = delay_us
        self.sequence = self.full_sequence if mode == 'full' else self.half_sequence


    def move(self, steps, direction = 1):
        count = 0

        while count < steps:
            if self.endstop_direction == direction and self.is_endstop_triggered():
                self.current_step = 0
                print(f"End stop reached for: {self.name}")
                break
            if self.max_steps and self.current_step >= self.max_steps and direction != self.endstop_direction:
                print(f"Max steps reached for: {self.name}")
                break


            for step in self.sequence if direction > 0 else self.sequence[::-1]:
                try:
                    self.set_step(step)
                    self.sleep_delay()
                except Exception as e:
                    print(f"Error during sleep: {e}")

            count += 1
            self.current_step += direction

        self.stop()
        return count * direction



    def stop(self):
        return

    def sleep_delay(self):
        return

    def set_step(self, steps):
        return

    def is_endstop_triggered(self):
        if self.endstop_direction is None:
            return False
        return self.current_step == 0

    def home(self):
        if self.endstop_direction:
            self.current_step = self.max_steps
            self.move(self.current_step, self.endstop_direction)
        self.current_step = 0


class StepperMotor(Motor):

    def __init__(self, name, in1, in2, in3, in4, delay_us=1500, mode='full', endstop_pin=None, endstop_direction=1,
                 max_steps=1100):
        super().__init__(name, delay_us, mode, endstop_direction, max_steps)
        self.coils = [Pin(in1, Pin.OUT), Pin(in2, Pin.OUT), Pin(in3, Pin.OUT), Pin(in4, Pin.OUT)]
        self.endstop = Pin(endstop_pin, Pin.IN, Pin.PULL_UP) if endstop_pin is not None else None

    def stop(self):
        self.set_step((0, 0, 0, 0))

    def set_step(self, step):
        for i, coil in enumerate(self.coils):
            coil.value(step[i])

    def is_endstop_triggered(self):
        return not self.endstop.value() if self.endstop else False

    def sleep_delay(self):
        sleep_micros(self.delay_us)

class StepperGCodeMachine(GCodeMachine):

    dot_size = 2

    def __init__(self, steps_per_mm, step_delay_us):
        super().__init__(steps_per_mm, step_delay_us)
        self.motor_y = StepperMotor("Y", 0, 1, 2, 3, delay_us=1500, mode='half', endstop_pin=15, endstop_direction=1)
        self.motor_x = StepperMotor("X", 4, 5, 6, 7, delay_us=1500, mode='half', endstop_pin=14, endstop_direction=-1)
        self.motor_z = StepperMotor("Z", 8, 9, 10, 11)
        self.is_pendown = False
        self.home()
        # may need to adjust as 0
        self.rounding_precision = 0
        self.line_increment = .25



    def dot(self, point):
        """draw a dot at point"""
        self.penup()
        self.move(point.x, point.y)
        self.pendown()
        self.penup()

    def move(self, x = None, y = None):
        current_point = Point(self.absolute_x, self.absolute_y)
        if self.relative_mode:
            relative_point = Point(0 if x is None else x, 0 if y is None else y)
            next_point =  relative_point.add(current_point)
        else:
            next_point = Point(self.absolute_x if x is None else x, self.absolute_y if y is None else y)
            relative_point = next_point.subtract(current_point)

        x_steps = abs(relative_point.x)
        x_direction = self.motor_x.endstop_direction if  relative_point.x < 0 else self.motor_x.endstop_direction * -1
        y_steps = abs(relative_point.y)
        y_direction = self.motor_y.endstop_direction if relative_point.y < 0 else self.motor_y.endstop_direction * -1
        self.motor_x.move(x_steps * self.steps_per_mm , x_direction)
        self.motor_y.move(y_steps * self.steps_per_mm, y_direction)

        self.absolute_x = next_point.x
        self.absolute_y = next_point.y



    def home(self):
        self.penup()
        self.motor_x.home()
        self.motor_y.home()
        self.absolute_x = 0
        self.absolute_y = 0


    def penup(self):
        if self.is_pendown:
            self.is_pendown = False
            self.motor_z.move(40, -1)

    def pendown(self):
        if not self.is_pendown:
            self.is_pendown = True
            self.motor_z.move(40, 1)


