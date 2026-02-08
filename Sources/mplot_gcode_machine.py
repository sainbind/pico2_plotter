import matplotlib.pyplot as plt
import numpy as np

from point import Point
from gcode_machine import GCodeMachine



class MplotGCodeMachine(GCodeMachine):

    dot_size = 2

    def __init__(self, steps_per_mm, step_delay_us, width, height, scale):
        super().__init__(steps_per_mm, step_delay_us,1, .25)
        self.width = width
        self.height = height
        self.scale = scale
        self.plt = plt
        self.plt.figure(figsize=(width,height))

        # Ensure equal scaling on both axes so 1 unit in X == 1 unit in Y
        self.ax = self.plt.gca()
        self.ax.set_aspect('equal', adjustable='box')


        # Set linear ticks every 20 units

        # self.ax.set_xticks(np.arange(0, self.width + tick_step, tick_step))
        self.ax.set_xticks(np.arange(0,  150, 10))
        self.ax.set_yticks(np.arange(0, 150, 10))
        self.ax.grid(True, which='both', linestyle='--',  alpha=0.4)
        #self.ax.grid(True, which='both', linestyle='--', linewidth=0.5)

        # How the CNC coordinate system works
        self.home()





    def dot(self, point):
        """draw a dot at point"""
        self.penup()
        self.move(point.x, point.y)
        self.pendown()
        self.plt.plot(point.x, point.y, 'o', color='black', markersize=MplotGCodeMachine.dot_size)

    def move(self, x = None, y = None):
        current_point = Point(self.absolute_x, self.absolute_y)
        if self.relative_mode:
            next_point =  Point(0 if x is None else x, 0 if y is None else y).add(current_point)
        else:
            next_point = Point(self.absolute_x if x is None else x, self.absolute_y if y is None else y)
        color = 'black' if self.is_pendown else 'white'
        nx = np.array([self.absolute_x,next_point.x])
        ny = np.array([self.absolute_y,next_point.y])
        self.plt.plot(nx, ny, linestyle='-', linewidth=2, color=color)
        self.absolute_x = next_point.x
        self.absolute_y = next_point.y


    def end(self):
        self.plt.show()
        super().end()


    def home(self):
        self.penup()
        self.move(0, 0)


    def penup(self):
        self.is_pendown = False


    def pendown(self):
        self.is_pendown = True

