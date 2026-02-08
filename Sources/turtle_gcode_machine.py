import math
import turtle
from point import Point
from gcode_machine import GCodeMachine, relative_draw



class TurtleGCodeMachine(GCodeMachine):

    dot_size = 2

    def __init__(self, steps_per_mm, step_delay_us, width, height, scale):
        super().__init__(steps_per_mm, step_delay_us)
        self.width = width
        self.height = height
        self.scale = scale
        self.t = turtle.Turtle()
        self.screen = turtle.Screen()
        self.screen.title("Turtle GCode Machine: Values are Millimeters")
        self.screen.setup(width, height, startx=50, starty=50)
        self.screen.mode("world")
        #self.screen.setworldcoordinates(-scale, -scale, width - scale, height - scale)
        # How the CNC coordinate system works
        self.screen.setworldcoordinates(-scale, height - scale, width-scale, -scale )
        self.screen.colormode(255)
        self.screen.delay(step_delay_us)
        self.screen.tracer(0)
        self._init_graph()
        self.home()
        self.rounding_precision = 1 # 0 for large rounding, 1 for small
        self.line_increment = .25  # 1 for courser lines, .25 for finer lines


    def turtle(self):
        return self.t

    def trace_mode(self, turn_on = False):
        if turn_on:
            self.screen.tracer(1,10)
        else:
            self.screen.tracer(0, 10)


    def dot(self, point):
        """draw a dot at point"""
        self.penup()
        self.move(point.x, point.y)
        self.pendown()
        self.t.dot(TurtleGCodeMachine.dot_size)

    def move(self, x = None, y = None):
        current_point = Point(self.absolute_x, self.absolute_y)
        if self.relative_mode:
            next_point =  Point(0 if x is None else x, 0 if y is None else y).add(current_point)
        else:
            next_point = Point(self.absolute_x if x is None else x, self.absolute_y if y is None else y)


        self.t.setpos(next_point.x * self.steps_per_mm, next_point.y * self.steps_per_mm)
        self.absolute_x = next_point.x
        self.absolute_y = next_point.y


    def end(self):
        super().end()
        self.screen.mainloop()

    def home(self):
        self.penup()
        if self.relative_mode:
            self.move(self.absolute_x * -1, self.absolute_y * -1)
        else:
            self.move(0, 0)


    def penup(self):
        self.is_pendown = False
        if (self.t.isdown()):
            self.t.penup()

    def pendown(self):
        self.is_pendown = True
        if (not self.t.isdown()):
            self.t.pendown()



    def _init_graph(self):

        x = 0
        while x < self.width - self.scale:
            y = 0
            self.t.teleport(x, y)
            if x > 0:
                self.t.color('lightgray')

            while y < self.height - self.scale:
                self.t.setpos(x, y)
                self.t.dot(2)
                y += self.scale
                if x == 0 :
                    self.t.write( (math.floor(y / self.scale) -1) * 10 , align='right', font=('Arial', 12, 'bold'))

            x += self.scale

        self.t.teleport(0, 0)
        self.t.color('black')
        y = 0
        while y < self.height - self.scale:
            x = 0
            self.t.teleport(x, y)
            if y > 0:
                self.t.color('lightgray')

            while x < self.width - self.scale:
                self.t.setpos(x, y)
                self.t.dot(2)
                x += self.scale
                if y == 0 :
                    self.t.write( (math.floor(x / self.scale) -1) * 10 , align='right', font=('Arial', 12, 'bold'))

            y += self.scale

        self.t.teleport(0, 0)
        self.t.color('black')



#scale = 50  # Seems to give each box about 1 cm square and 5 stes per mm
#machine = TurtleGCodeMachine(5,0,1000,1000, scale)
#relative_draw(machine)

