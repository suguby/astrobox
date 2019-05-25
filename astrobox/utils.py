# -*- coding: utf-8 -*-

import math

from robogame_engine.geometry import Vector, normalise_angle


def nearest_angle_distance(left, right):
    lv = Vector.from_direction(left, module=10)
    rv = Vector.from_direction(right, module=10)
    return normalise_angle(math.atan2(rv.y - lv.y, rv.x - lv.x) * 180 / math.pi)


