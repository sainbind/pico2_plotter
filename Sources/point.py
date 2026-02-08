import math


class Point:
    def __init__(self, *args):
        """ Initialize point using 2 integer or up to 2 strings starting with either x or y
            Examples:
                10, 20 will set x=10, y=20
                "x10", "y20" will set x=10, y=20
        """

        self.x = 0
        self.y = 0

        if len(args) == 2 and not isinstance(args[0], str) and not isinstance(args[1], str):
            self.x = args[0]
            self.y = args[1]
        else:
            params =  args[0] if isinstance(args[0],list) and len(args) == 1 else args
            for arg in params:
                arg = arg.lower()
                if arg.startswith("x"):
                    self.x = int(arg[1:])
                elif arg.startswith("y"):
                    self.y = int(arg[1:])

    def __str__(self):
        return f"[({self.x:.2f}, {self.y:.2f})]"

    def distance(self, other_point):
        """
        Distance between this point to another point
        :param other_point:
        :return: distance between this point and another point
        """
        return math.sqrt((other_point.x - self.x ) ** 2 + ( other_point.y - self.y) ** 2)

    def midpoint(self, other_point):
        """
        Midpoint between this point and another points
        :param other_point:
        :return: midpoint between this point and another points
        """
        mx = (self.x + other_point.x) / 2
        my = (self.y + other_point.y) / 2
        return Point(mx, my)

    def angle(self, center_point):
        """
        Returns the angle between this point and center point of a circle
        :param center_point:
        :return: angle between this point and center point of a circle
        """
        result = math.atan2(self.y - center_point.y, self.x - center_point.x)
        result =  result % (2 * math.pi)
        if result < 0:
            result += (2 * math.pi)
        return result

    def line(self, other_point):
        """Return slope and intercept of a line"""
        rise = other_point.y -self.y
        run = other_point.x - self.x
        slope = None if run == 0 else rise / run
        intercept = None if run == 0 else  self.y - self.x * slope
        return slope, intercept

    def add(self, other_point):
        """ Add this point to another point"""
        return Point(self.x + other_point.x, self.y + other_point.y)

    def subtract(self, other_point):
        """ Subtract other point from this point"""
        return Point( self.x - other_point.x,  self.y - other_point.y)

    def vector(self, center_point):
        return Point(self.x - center_point.x, self.y - center_point.y)

    def round(self,decimals=0):
        self.x = round(self.x,decimals)
        self.y = round(self.y,decimals)
        return self

    def circle_center(self, other_point, radius, clockwise = True):
        """
        Returns the center point of a circle between this point and another point
        :param point2:
        :param radius:
        :param clockwise:
        :return: center point of a circle between this point and another point
        """
        d = self.distance(other_point)

        if d > (abs(radius) * 2):
            raise ValueError("No Arc with this radius can connect the 2 points")
        factor = 1 if radius > 0 else -1
        h = math.sqrt( (radius ** 2.0) - ((d/2.0) ** 2.0) ) * factor
        mid_point = self.midpoint(other_point)

        # vector from point1 to point2
        vx  = (other_point.x -self.x) / d
        vy = (other_point.y -self.y) / d

        # perpendicular unit vectors
        px = -vy
        py = vx

        #print(f"d: {d:.2f}  vx: {vx:.2f}, vy: {vy:.2f}, px: {px:.2f}, py: {py:.2f}")

        if clockwise:
            return Point(mid_point.x + h * px, mid_point.y + h *  py)
        else:
            return Point(mid_point.x - h * px, mid_point.y - h * py)


    def is_equal(self, other_point):
        return other_point.x == self.x and other_point.y == self.y


    def bresenham_line(self, point, increment = 1):
        """
        Generates the coordinates for a line using the Bresenham algorithm.
        """
        x0 = self.x
        y0 = self.y
        x1 = point.x
        y1 = point.y

        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        # Determine the direction of movement along axes
        sx = increment if x0 < x1 else -1 * increment
        sy = increment if y0 < y1 else -1 * increment
        err = dx - dy

        while True:
            yield Point(x0, y0)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy



