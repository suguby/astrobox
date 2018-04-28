# -*- coding: utf-8 -*-
from __future__ import print_function

import random

from robogame_engine import GameObject
from robogame_engine.constants import ROTATE_TURNING
from robogame_engine.theme import theme
from .cargo_box import CargoBox


class AstroUnit(GameObject, CargoBox):

    @property
    def image(self):
        image = super(AstroUnit, self).image
        image.payload = self.payload
        return image


class Dron(AstroUnit):
    rotate_mode = ROTATE_TURNING
    radius = 44
    _part_of_team = True
    __my_mathership = None
    _dead = False

    def __init__(self, coord=None):
        super(Dron, self).__init__(coord=self.my_mathership.coord if coord is None else coord)
        CargoBox.__init__(self, initial_cargo=0, maximum_cargo=theme.MAX_DRON_ELERIUM)
        self._objects_holder = self.scene
        self.__health = theme.MAX_HEALTH

    @property
    def sprite_filename(self):
        return 'dron_{}.png'.format(self.team)

    @property
    def my_mathership(self):
        if self.__my_mathership is None:
            try:
                self.__my_mathership = self.scene.get_mathership(team=self.team)
            except IndexError:
                raise Exception("No mathership for {} - check matherships_count!".format(self.__class__.__name__))
        return self.__my_mathership

    @property
    def radar_marks(self):
        return self.scene.radar_marks

    @property
    def meter_1(self):
        return self.fullness

    @property
    def meter_2(self):
        return float(self.__health) / theme.MAX_HEALTH

    @property
    def is_alive(self):
        return self.__health > 0

    @property
    def asteroids(self):
        return [obj for obj in self.radar_marks if obj.kind == 'Asteroid']

    @property
    def matherships(self):
        return [obj for obj in self.radar_marks if obj.kind == 'MatherShip']

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
            for ship in self.matherships:
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


class Asteroid(AstroUnit):
    radius = 50
    selectable = False
    counter_attrs = dict(size=16, position=(43, 45), color=(128, 128, 128))

    def __init__(self, coord, max_elerium=None):
        super(Asteroid, self).__init__(coord=coord)
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


class MatherShip(AstroUnit):
    radius = 75
    selectable = False
    counter_attrs = dict(size=22, position=(60, 92), color=(255, 255, 0))

    def __init__(self, coord, max_elerium):
        super(MatherShip, self).__init__(coord=coord)
        CargoBox.__init__(self, initial_cargo=0, maximum_cargo=max_elerium)

    @property
    def sprite_filename(self):
        # TODO тут надо допилить что бы матка была тоже в команде? иначе как спрайт рендерить?
        # return 'mathership_{}.png'.format(self.team)
        return 'mathership_1.png'

    @property
    def counter(self):
        return self.payload



