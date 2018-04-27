# -*- coding: utf-8 -*-
from __future__ import print_function

import math
import random

from robogame_engine import GameObject, Scene
from robogame_engine.constants import ROTATE_TURNING
from robogame_engine.geometry import Point
from robogame_engine.theme import theme
from .cargo_box import CargoBox


class Dron(GameObject, CargoBox):
    rotate_mode = ROTATE_TURNING
    radius = 44
    _part_of_team = True
    __my_mathership = None
    __asteroids = None
    _dead = False

    def __init__(self, pos=None):
        super(Dron, self).__init__(pos=self.my_mathership.coord if pos is None else pos)
        CargoBox.__init__(self, initial_cargo=0, maximum_cargo=theme.MAX_DRON_ELERIUM)
        self._objects_holder = self._scene
        self.__health = theme.MAX_HEALTH

    @property
    def sprite_filename(self):
        return 'dron_{}.png'.format(self.team)

    @property
    def my_mathership(self):
        if self.__my_mathership is None:
            try:
                self.__my_mathership = self._scene.get_mathership(team=self.team)
            except IndexError:
                raise Exception("No mathership for {} - check matherships_count!".format(self.__class__.__name__))
        return self.__my_mathership

    @property
    def asteroids(self):
        # TODO тут бы копию снимать?
        return self._scene.asteroids

    @property
    def meter_1(self):
        return self.fullness

    @property
    def meter_2(self):
        return float(self.__health) / theme.MAX_HEALTH

    @property
    def is_alive(self):
        return self.__health > 0

    def game_step(self):
        super(Dron, self).game_step()
        CargoBox.game_step(self)
        if self.is_alive and self.__health < theme.MAX_HEALTH:
            self.__health += theme.HEALTH_TOP_UP_SPEED

    def on_stop_at_target(self, target):
        for asteroid in self.asteroids:
            if asteroid.near(target):
                self.on_stop_at_asteroid(asteroid)
                return
        else:
            for ship in self._scene.matherships:
                if ship.near(target):
                    self.on_stop_at_mathership(ship)
                    return
        self.on_stop_at_point(target)

    def on_stop_at_point(self, target):
        pass

    def on_stop_at_asteroid(self, asteroid):
        pass

    def on_stop_at_mathership(self, mathership):
        pass

    # def sting(self, other):
    #     """
    #     Укусить другую пчелу
    #     """
    #     if self._dead:
    #         return
    #     if isinstance(other, Bee):
    #         other.stung(self, self.__reduce_health)
    #
    # def stung(self, other, kickback):
    #     """
    #     Принять укус, если кусающий близко.
    #     Здоровье кусающего тоже уменьшается через kickback
    #     """
    #     if self.distance_to(other) <= self.radius:
    #         try:
    #             kickback()
    #             self.__reduce_health()
    #         except TypeError:
    #             # flashback не может быть вызвана
    #             pass

    # def __reduce_health(self):
    #     if self.distance_to(self.my_beehive) > theme.BEEHIVE_SAFE_DISTANCE:
    #         self._health -= theme.STING_POWER
    #         if self._health < 0:
    #             self.__die()
    #
    # def __die(self):
    #     self.rotate_mode = ROTATE_FLIP_BOTH
    #     self.move_at(Point(x=self.x + random.randint(-20, 20), y=40 + random.randint(-10, 20)))
    #     self._dead = True

    def move_at(self, target, speed=None):
        if not self.is_alive:
            return
        super(Dron, self).move_at(target, speed)

    def turn_to(self, target, speed=None):
        if not self.is_alive:
            return
        super(Dron, self).turn_to(target, speed)


class Asteriod(GameObject, CargoBox):
    radius = 50
    selectable = False
    counter_attrs = dict(size=16, position=(43, 45), color=(128, 128, 128))

    def __init__(self, pos, max_elerium=None):
        super(Asteriod, self).__init__(pos=pos)
        if max_elerium is None:
            max_elerium = random.randint(theme.MIN_ASTEROID_ELERIUM, theme.MAX_ASTEROID_ELERIUM)
        CargoBox.__init__(self, initial_cargo=max_elerium, maximum_cargo=max_elerium)
        self._sprite_num = random.randint(1, 9)

    @property
    def sprite_filename(self):
        return 'asteroids/{}.png'.format(self._sprite_num)

    def update(self):
        pass

    @property
    def counter(self):
        return self.payload


class Mathership(GameObject, CargoBox):
    radius = 75
    selectable = False
    counter_attrs = dict(size=22, position=(60, 92), color=(255, 255, 0))

    def __init__(self, pos, max_elerium):
        super(Mathership, self).__init__(pos=pos)
        CargoBox.__init__(self, initial_cargo=0, maximum_cargo=max_elerium)

    @property
    def sprite_filename(self):
        # TODO тут надо допилить что бы матка была тоже в команде? иначе как спрайт рендерить?
        # return 'mathership_{}.png'.format(self.team)
        return 'mathership_1.png'

    @property
    def counter(self):
        return self.payload


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
        super(StarField, self).__init__(*args, **kwargs)

    def prepare(self, asteroids_count=5, matherships_count=1):
        self._fill_space(
            asteroids_count=asteroids_count,
            matherships_count=matherships_count,
        )
        self._objects_holder = self
        # TODO посмотреть зачем корректировалась скорость перекачки
        # honey_speed = int(theme.MAX_SPEED * self._HONEY_SPEED_FACTOR)
        # if honey_speed < 1:
        #     honey_speed = 1
        # CargoBox.__load_speed = honey_speed

    def _fill_space(self, asteroids_count, matherships_count):
        if matherships_count > theme.TEAMS_COUNT:
            raise Exception('Only {} matherships!'.format(theme.TEAMS_COUNT))

        field = Rect(w=theme.FIELD_WIDTH, h=theme.FIELD_HEIGHT)
        field.reduce(dw=Mathership.radius * 2, dh=Mathership.radius * 2)
        if matherships_count >= 2:
            field.reduce(dw=Mathership.radius * 2)
        if matherships_count >= 3:
            field.reduce(dh=Mathership.radius * 2)
        if field.w < Mathership.radius or field.h < Mathership.radius:
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

        field.x = Mathership.radius * 2
        field.y = Mathership.radius * 2
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
            asteroid = Asteriod(pos)
            self.__asteroids.append(asteroid)
            max_elerium += asteroid.payload
            i += 1
        max_elerium /= float(matherships_count)
        max_elerium = int(round((max_elerium / 1000.0) * 1.3)) * 1000
        if max_elerium < 1000:
            max_elerium = 1000
        for team in range(matherships_count):
            # TODO вычислять от размера игрового поля и радиуса матки
            if team == 0:
                pos = Point(90, 75)
            elif team == 1:
                pos = Point(theme.FIELD_WIDTH - 90, 75)
            elif team == 2:
                pos = Point(90, theme.FIELD_HEIGHT - 75)
            else:
                pos = Point(theme.FIELD_WIDTH - 90, theme.FIELD_HEIGHT - 75)
            mathership = Mathership(pos=pos, max_elerium=max_elerium)
            self.__matherships.append(mathership)

    def get_mathership(self, team):
        return self.__matherships[team - 1]

    @property
    def asteroids(self):
        return self.__asteroids



