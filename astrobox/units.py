# -*- coding: utf-8 -*-
import random

from robogame_engine import GameObject
from robogame_engine.constants import ROTATE_TURNING
from robogame_engine.theme import theme

from .cargo import *

class Unit(GameObject):
    coord = None  # переопределяется в потомках
    radius = 0
    _cargo = None

    def __init__(self, team=-1, **kwargs):
        super(Unit, self).__init__(**kwargs);
        self.set_team(team)
        self._move_target = None

    @property
    def cargo(self):
        return self._cargo

    @property
    def sprite_filename(self):
        return 'not-found.png'

    def move_at(self, target, speed=None):
        if self._move_target == target:
            return;
        self._move_target = target
        super(Unit, self).move_at(target, speed=speed)

    def turn_to(self, target, speed=None):
        super(Unit, self).turn_to(target, speed=speed)

    def on_stop(self):
        pass

class DroneUnit(Unit):
    rotate_mode = ROTATE_TURNING
    radius = 44
    auto_team = True
    layer = 2

    def __init__(self, **kwargs):
        super(DroneUnit, self).__init__(**kwargs)
        self.__mothership = None
        self._cargo = Cargo(self, payload=0, max_payload=theme.DRONE_CARGO_PAYLOAD)
        self.__health = theme.DRONE_MAX_SHIELD

    @property
    def teammates(self):
        return [mate for mate in self.scene.drones if mate != self and mate.team == self.team and mate.is_alive]

    @property
    def sprite_filename(self):
        if self.is_alive:
            return 'dron_{}.png'.format(self.team)
        return 'dron_{}_crashed.png'.format(self.team)

    @property
    def meter_1(self):
        return min(self._cargo.fullness, 1.0)

    @property
    def meter_2(self):
        return float(self.__health) / theme.DRONE_MAX_SHIELD

    @property
    def is_alive(self):
        return self.__health > 0

    def damage_taken(self, damage=0):
        #print(self.__class__.__name__+"::damage_taken", damage)
        self.__health = max(self.__health-damage, 0)
        if self.__health<=0:
            self.stop()

    def __heal_taken(self, healed_on=0):
        if self.__health>0:
            self.__health = min(self.__health+healed_on, theme.DRONE_MAX_SHIELD)

    def mothership(self):
        if self.__mothership is None:
            self.__mothership = self.scene.get_mothership(self.team)
        return self.__mothership

    def game_step(self):
        if self.mothership() and self.mothership().is_alive and \
                self.distance_to(self.mothership().coord) < theme.MOTHERSHIP_HEALING_DISTANCE:
            self.__heal_taken(theme.MOTHERSHIP_HEALING_RATE)
        else:
            self.__heal_taken(theme.DRONE_SHIELD_RENEWAL_RATE)
        if hasattr(self, 'gun'):
            self.gun.game_step()
        super(DroneUnit, self).game_step()


    def on_born(self):
        super(DroneUnit, self).on_born()

    def move_at(self, target, speed=None):
        if not self.is_alive:
            return
        super(DroneUnit, self).move_at(target, speed=theme.DRONE_SPEED)

    def turn_to(self, target, speed=None):
        if not self.is_alive:
            return
        super(DroneUnit, self).turn_to(target, speed=theme.DRONE_TURN_SPEED)

class Asteroid(Unit):
    rotate_mode = ROTATE_TURNING
    radius = 50
    selectable = False
    counter_attrs = dict(size=16, position=(0, 0), color=(255, 255, 255))

    def __init__(self, max_payload=None, **kwargs):
        if "direction" not in kwargs:
            kwargs["direction"] = random.randint(0, 360)
        max_elerium = random.randint(theme.MIN_ASTEROID_ELERIUM, theme.MAX_ASTEROID_ELERIUM)
        self._cargo = Cargo(self, payload=max_elerium, max_payload=max_elerium)
        self.__sprite_num = random.randint(1, 5)
        self._size = (max_elerium / theme.MIN_ASTEROID_ELERIUM) * .8
        super(Asteroid, self).__init__(**kwargs);

    @property
    def cargo(self):
        return self._cargo

    @property
    def sprite_filename(self):
        return 'asteroids/{}.png'.format(self.__sprite_num)

    @property
    def zoom(self):
        return .4 + self.cargo.fullness * .6 * self._size

    @property
    def is_alive(self):
        return False

    @property
    def counter(self):
        return self.cargo.payload if self._cargo is not None else 0

    def on_born(self):
        #super(Unit, self).on_born()
        self.turn_to(self.direction + 90, speed=theme.ASTEROID_ROTATION_SPEED)

    def on_stop(self):
        #super(Asteroid, self).on_stop()
        self.turn_to(self.direction + 90, speed=theme.ASTEROID_ROTATION_SPEED)

    def on_hearbeat(self):
        pass


class MotherShip(Unit):
    radius = 75
    selectable = False
    counter_attrs = dict(size=22, position=(75, 135), color=(255, 255, 255))

    def __init__(self,  max_payload=0, **kwargs):
        super(MotherShip, self).__init__(**kwargs)
        self._cargo = Cargo(self, payload=0, max_payload=max_payload);
        self.__health = theme.MOTHERSHIP_MAX_SHIELD

    @property
    def sprite_filename(self):
        if self.is_alive:
            return 'mothership_{}.png'.format(self.team)
        return 'mothership_{}_crashed.png'.format(self.team)

    @property
    def meter_2(self):
        return self.__health / theme.MOTHERSHIP_MAX_SHIELD

    @property
    def counter(self):
        return self.cargo.payload

    @property
    def is_alive(self):
        return self.__health > 0

    def damage_taken(self, damage=0):
        self.__health = max(self.__health-damage, 0)

    def __heal_taken(self, healed_on=0):
        if self.__health>0:
            self.__health = min(self.__health+healed_on, theme.MOTHERSHIP_MAX_SHIELD)

    def game_step(self):
        self.__heal_taken(theme.MOTHERSHIP_SHIELD_RENEWAL_RATE)

    def on_hearbeat(self):
        pass
    def on_stop(self):
        pass
