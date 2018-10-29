# -*- coding: utf-8 -*-

import math

from .theme import theme


def normalise_angle(a):
    """
        Make angle in 0 < x < 360
    """
    return a % 360


class Point(object):

    @classmethod
    def from_point(cls, point):
        assert isinstance(point, Point)
        return cls(x=point.x, y=point.y)

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def distance_to(self, other):
        """
            The distance to other points
        """
        from robogame_engine import GameObject
        if isinstance(other, GameObject):
            other = other.coord
        assert isinstance(other, Point)
        return math.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)

    def to_screen(self):
        """
            Convert coordinates to display
        """
        return int(self.x), theme.FIELD_HEIGHT - int(self.y)

    def __add__(self, vector):
        assert isinstance(vector, Vector)
        return Point(self.x + vector.x, self.y + vector.y)

    __radd__ = __add__

    def __iadd__(self, vector):
        assert isinstance(vector, Vector)
        self.x += vector.x
        self.y += vector.y
        return self

    def __sub__(self, vector):
        assert isinstance(vector, Vector)
        return Point(self.x - vector.x, self.y - vector.y)

    __rsub__ = __sub__

    def __isub__(self, vector):
        assert isinstance(vector, Vector)
        self.x -= vector.x
        self.y -= vector.y
        return self

    def __str__(self):
        return 'p({:.1f},{:.1f})'.format(self.x, self.y)

    __repr__ = __str__

    def copy(self):
        return self.__class__(self.x, self.y)


class Vector(object):

    def __init__(self, x, y):
        self.x = x
        self.y = y

    @classmethod
    def from_points(cls, point1, point2, module=None):
        assert isinstance(point1, Point)
        assert isinstance(point2, Point)
        x = float(point2.x - point1.x)
        y = float(point2.y - point1.y)
        if module:
            current_module = cls.calc_module(x, y)
            if current_module:
                x *= module / current_module
                y *= module / current_module
        return cls(x, y)

    @classmethod
    def from_direction(cls, direction, module):
        rads = cls.to_radian(direction)
        x = math.cos(rads) * module
        y = math.sin(rads) * module
        return cls(x, y)

    @staticmethod
    def to_radian(degrees):
        return (degrees * math.pi) / 180

    @property
    def direction(self):
        try:
            return self._direction
        except AttributeError:
            self._direction = self._get_direction()
            return self._direction

    @property
    def module(self):
        try:
            return self._module
        except AttributeError:
            self._module = self._get_module()
            return self._module

    def _get_direction(self):
        if self.x == 0:
            if self.y >= 0:
                direction = 90
            else:
                direction = 270
        else:
            direction = math.atan(self.y / self.x) * (180 / math.pi)
            if self.x < 0:
                direction += 180
        return normalise_angle(direction)

    def _get_module(self):
        return self.calc_module(self.x, self.y)

    @staticmethod
    def calc_module(x, y):
        return math.sqrt(x ** 2 + y ** 2)

    def rotate(self, delta):
        rad = self.to_radian(self.direction + delta)
        self.x = math.cos(rad) * self.module
        self.y = math.sin(rad) * self.module
        delattr(self, '_direction')

    def __str__(self):
        return 'v({:.1f},{:.1f})'.format(self.direction, self.module)

    __repr__ = __str__

    def __nonzero__(self):
        return self.x + self.y < 0

    def __neg__(self):
        return Vector(-self.x, -self.y)

    def __mul__(self, other):
        assert isinstance(other, int)
        return Vector(self.x * other, self.y * other)

    def copy(self):
        return self.__class__(self.x, self.y)


def get_arctan(dy, dx):
    """
        Determine the angle in degrees for the twins
    """
    out = math.atan2(dy, dx) / math.pi * 180
    # Unlike atan(y/x), the signs of both x and y are considered.
    return normalise_angle(out)

# def get_tangens(angle):
#     """
#         Determine the tangent of the angle in degrees
#     """
#     return math.tan(angle / 180.0 * math.pi)


