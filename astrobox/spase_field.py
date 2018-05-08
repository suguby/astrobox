# -*- coding: utf-8 -*-
import math
import random

from astrobox.core import (MatherShip, Asteroid, Dron)
from robogame_engine import Scene
from robogame_engine.geometry import Point
from robogame_engine.theme import theme


class Rect(object):

    def __init__(self, x=0, y=0, w=10, h=10):
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def reduce(self, dw=0, dh=0):
        self.w -= dw
        self.h -= dh

    def shift(self, dx=0, dy=0):
        self.x += dx
        self.y += dy

    def __str__(self):
        return "{}x{} ({}, {})".format(self.w, self.h, self.x, self.y)


class StarField(Scene):
    check_collisions = False
    _CELL_JITTER = 0.7
    # _HONEY_SPEED_FACTOR = 0.02

    def __init__(self, *args, **kwargs):
        self.__matherships = []
        self.__asteroids = []
        if 'theme_mod_path' not in kwargs:
            kwargs['theme_mod_path'] = 'astrobox.themes.default'
        super(StarField, self).__init__(*args, **kwargs)

    def prepare(self, asteroids_count=5):
        self._fill_space(
            asteroids_count=asteroids_count,
        )
        self._objects_holder = self
        # TODO посмотреть зачем корректировалась скорость перекачки
        # honey_speed = int(theme.MAX_SPEED * self._HONEY_SPEED_FACTOR)
        # if honey_speed < 1:
        #     honey_speed = 1
        # CargoBox.__load_speed = honey_speed

    def _fill_space(self, asteroids_count):
        field = Rect(w=theme.FIELD_WIDTH, h=theme.FIELD_HEIGHT)
        field.reduce(dw=MatherShip.radius * 2, dh=MatherShip.radius * 2)
        if self.teams_count >= 2:
            field.reduce(dw=MatherShip.radius * 2)
        if self.teams_count >= 3:
            field.reduce(dh=MatherShip.radius * 2)
        if field.w < MatherShip.radius or field.h < MatherShip.radius:
            raise Exception("Too little field...")
        if theme.DEBUG:
            print("Initial field", field)

        cells_in_width = int(math.ceil(math.sqrt(float(field.w) / field.h * asteroids_count)))
        cells_in_height = int(math.ceil(float(asteroids_count) / cells_in_width))
        cells_count = cells_in_height * cells_in_width
        if theme.DEBUG:
            print("Cells count", cells_count, cells_in_width, cells_in_height)
        if cells_count < asteroids_count:
            print(u"Ну я не знаю...")

        cell = Rect(w=int(field.w / cells_in_width), h=int(field.h / cells_in_height))

        if theme.DEBUG:
            print("Adjusted cell", cell)

        cell_numbers = [i for i in range(cells_count)]

        jit_box = Rect(w=int(cell.w * self._CELL_JITTER), h=int(cell.h * self._CELL_JITTER))
        jit_box.shift(dx=(cell.w - jit_box.w) // 2, dy=(cell.h - jit_box.h) // 2)
        if theme.DEBUG:
            print("Jit box", jit_box)

        field.w = cells_in_width * cell.w + jit_box.w
        field.h = cells_in_height * cell.h + jit_box.h
        if theme.DEBUG:
            print("Adjusted field", field)

        field.x = MatherShip.radius * 2
        field.y = MatherShip.radius * 2
        if theme.DEBUG:
            print("Shifted field", field)

        max_elerium = 0
        i = 0
        while i < asteroids_count:
            cell_number = random.choice(cell_numbers)
            cell_numbers.remove(cell_number)
            cell.x = (cell_number % cells_in_width) * cell.w
            cell.y = (cell_number // cells_in_width) * cell.h
            dx = random.randint(0, jit_box.w)
            dy = random.randint(0, jit_box.h)
            pos = Point(field.x + cell.x + dx, field.y + cell.y + dy)
            asteroid = Asteroid(pos)
            self.__asteroids.append(asteroid)
            max_elerium += asteroid.payload
            i += 1
        max_elerium /= float(self.teams_count)
        max_elerium = int(round((max_elerium / 1000.0) * 1.3)) * 1000
        if max_elerium < 1000:
            max_elerium = 1000
        for team, cls in enumerate(self.teams):
            team += 1
            # TODO вычислять координаты от размера игрового поля и радиуса матки
            if team == 1:
                pos = Point(90, 75)
            elif team == 2:
                pos = Point(theme.FIELD_WIDTH - 90, 75)
            elif team == 3:
                pos = Point(90, theme.FIELD_HEIGHT - 75)
            else:
                pos = Point(theme.FIELD_WIDTH - 90, theme.FIELD_HEIGHT - 75)
            mathership = MatherShip(coord=pos, max_elerium=max_elerium, team=team)
            for dron in self.get_objects_by_type(cls):
                dron.coord = pos.copy()
                dron.set_team(team=team)
            self.__matherships.append(mathership)

    def get_mathership(self, team):
        return self.__matherships[team - 1]

    @property
    def drones(self):
        return self.get_objects_by_type(Dron)

    @property
    def asteroids(self):
        return self.get_objects_by_type(Asteroid)

    @property
    def matherships(self):
        return self.get_objects_by_type(MatherShip)
