# -*- coding: utf-8 -*-
import math
import random

from robogame_engine import GameObject
from robogame_engine.constants import ROTATE_TURNING
from robogame_engine.theme import theme

from .guns import PlasmaGun
from .cargo import Cargo, CargoTransition


class Unit(GameObject):
    coord = None  # переопределяется в потомках
    radius = 0
    _cargo = None

    def __init__(self, payload=0, max_payload=1, **kwargs):
        super(Unit, self).__init__(**kwargs)
        self._move_target = None
        self._cargo = Cargo(self, payload=payload, max_payload=max_payload)
        self._transition = None

    @property
    def cargo(self):
        return self._cargo

    @property
    def payload(self):
        return self._cargo.payload

    @property
    def fullness(self):
        return self._cargo.fullness

    @property
    def is_empty(self):
        return self._cargo.is_empty

    @property
    def is_full(self):
        return self._cargo.is_full

    @property
    def free_space(self):
        return self._cargo.free_space

    @property
    def sprite_filename(self):
        return 'not-found.png'

    def game_step(self):
        if self._transition:
            if not self._transition.is_finished:
                self._transition.game_step()
            if self._transition.is_finished:
                if self._transition.cargo_to == self._cargo:
                    self.on_load_complete()
                if self._transition.cargo_from == self._cargo:
                    self.on_unload_complete()
                self._transition = None

        super(Unit, self).game_step()

    def move_at(self, target, speed=None):
        if self._move_target == target:
            return
        self._move_target = target
        super(Unit, self).move_at(target, speed=speed)

    def turn_to(self, target, speed=None):
        super(Unit, self).turn_to(target, speed=speed)

    def load_from(self, source):
        if self._cargo.free_space:
            self._transition = CargoTransition(cargo_from=source._cargo, cargo_to=self._cargo)

    def unload_to(self, target):
        if not self._cargo.is_empty:
            self._transition = CargoTransition(cargo_from=self._cargo, cargo_to=target._cargo)

    def on_load_complete(self):
        pass

    def on_unload_complete(self):
        pass


class Drone(Unit):
    rotate_mode = ROTATE_TURNING
    radius = 44
    auto_team = True
    layer = 2

    class __DeathAnimation(object):
        def __init__(self, owner):
            self._owner = owner
            self.__sprites = ['teams/{}/blow_up_{}.png'.format(owner.team, i + 1) for i in range(3)]
            self.__sprites.append('teams/any_drone_explosion.png')
            self.__sprites.append('teams/{}/drone_crashed.png'.format(owner.team))
            self.__animation_speed = 10  # фреймов на спрайт
            self.__animation_frame = 0  # счетчик фреймов
            self.__current_sprite = self.__sprites[0]

        def sprite_filename(self):
            # последний в списке?
            if self.__sprites.index(self.__current_sprite) >= len(self.__sprites) - 1:
                return self.__current_sprite
            if self.__animation_frame < self.__animation_speed:
                self.__animation_frame += self._owner.scene.game_speed
            else:
                self.__animation_frame = 0
                # переключиться на следующий
                self.__current_sprite = self.__sprites[self.__sprites.index(self.__current_sprite) + 1]
            return self.__current_sprite

    def __init__(self, **kwargs):
        self._mothership = None
        self._gun = None
        if theme.DRONES_CAN_FIGHT:
            self._gun = PlasmaGun(self)
        self.__health = theme.DRONE_MAX_SHIELD
        super(Drone, self).__init__(max_payload=theme.MAX_DRONE_ELERIUM, **kwargs)

        self.__dead_flight_speed = theme.DRONE_DEAD_SPEED
        self.__angle_of_death = None
        self.__death_animaion = self.__DeathAnimation(self)

    @property
    def have_gun(self):
        return self._gun is not None

    @property
    def gun(self):
        return self._gun

    @property
    def teammates(self):
        return [mate for mate in self.scene.drones
                if mate != self and mate.team == self.team and mate.is_alive]

    @property
    def sprite_filename(self):
        if self.is_alive:
            return 'teams/{}/drone.png'.format(self.team)
        return self.__death_animaion.sprite_filename()

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
        self.__health = max(self.__health - damage, 0)
        if self.__health <= 0:
            self.stop()

    def __heal_taken(self, healed_on=0):
        if self.__health > 0:
            self.__health = min(self.__health + healed_on, theme.DRONE_MAX_SHIELD)

    @property
    def mothership(self):
        if self._mothership is None:
            self._mothership = self.scene.get_mothership(self.team)
            assert self._mothership is not None
        return self._mothership

    def __dead_game_step(self):
        if self.__dead_flight_speed < 0.0:
            return
        if self.__angle_of_death is None:
            self.layer = 1
            self.__angle_of_death = random.randint(0, 359)

        x = self.__dead_flight_speed * math.sin(self.__angle_of_death)
        y = self.__dead_flight_speed * math.cos(self.__angle_of_death)
        self.coord.x = min(theme.FIELD_WIDTH - self.radius, max(self.radius, self.coord.x + x))
        self.coord.y = min(theme.FIELD_HEIGHT - self.radius, max(self.radius, self.coord.y + y))

        self.__dead_flight_speed -= theme.DRONE_DEAD_SPEED_DECELERATION * self.scene.game_speed
        super(Drone, self).game_step()

    def game_step(self):
        if not self.is_alive:
            self.__dead_game_step()
            return
        if self.mothership and self.mothership.is_alive and \
                self.distance_to(self.mothership.coord) < theme.MOTHERSHIP_HEALING_DISTANCE:
            self.__heal_taken(theme.MOTHERSHIP_HEALING_RATE)
        else:
            self.__heal_taken(theme.DRONE_SHIELD_RENEWAL_RATE)
        if self.have_gun:
            self.gun.game_step()
        super(Drone, self).game_step()

    def move_at(self, target, speed=None):
        if not self.is_alive:
            return
        super(Drone, self).move_at(target, speed=theme.DRONE_SPEED)

    def turn_to(self, target, speed=None):
        if not self.is_alive:
            return
        super(Drone, self).turn_to(target, speed=theme.DRONE_TURN_SPEED)

    @property
    def my_mothership(self):
        return self.mothership

    @property
    def asteroids(self):
        return self.scene.asteroids

    def on_stop_at_target(self, target):
        for asteroid in self.asteroids:
            if asteroid.near(target):
                self.on_stop_at_asteroid(asteroid)
                return
        else:
            for ship in self.scene.motherships:
                if ship.near(target):
                    self.on_stop_at_mothership(ship)
                    return
        self.on_stop_at_point(target)

    def on_stop_at_point(self, target):
        pass

    def on_stop_at_asteroid(self, asteroid):
        pass

    def on_stop_at_mothership(self, mothership):
        pass


class Asteroid(Unit):
    rotate_mode = ROTATE_TURNING
    radius = 50
    selectable = False
    counter_attrs = dict(size=16, position=(0, 0), color=(255, 255, 255))
    layer = 1

    def __init__(self, elerium=None, **kwargs):
        if "direction" not in kwargs:
            kwargs["direction"] = random.randint(0, 360)
        self.__sprite_num = random.randint(1, 5)
        self._size = (elerium / theme.MIN_ASTEROID_ELERIUM) * .8
        super(Asteroid, self).__init__(payload=elerium, max_payload=elerium, **kwargs)

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
        # super(Unit, self).on_born()
        self.turn_to(self.direction + 90, speed=theme.ASTEROID_ROTATION_SPEED)

    def on_stop(self):
        # super(Asteroid, self).on_stop()
        self.turn_to(self.direction + 90, speed=theme.ASTEROID_ROTATION_SPEED)

    def on_hearbeat(self):
        pass


class MotherShip(Unit):
    radius = 90
    selectable = False
    counter_attrs = dict(size=22, position=(75, 135), color=(255, 255, 255))
    layer = 1

    class __DeathAnimation(object):
        def __init__(self, owner):
            assert owner.team is not None
            self._owner = owner
            self.__sprites = ['motherships/{}/blow_up_{}.png'.format(owner.team, i + 1) for i in range(2)]
            self.__sprites.append('motherships/any_mothership_explosion.png')
            self.__sprites.append('motherships/{}/crashed.png'.format(owner.team))
            self.__animation_speed = 10  # фреймов на спрайт
            self.__animation_frame = 0  # счетчик фреймов
            self.__current_sprite = self.__sprites[0]

        def sprite_filename(self):
            # последний в списке?
            if self.__sprites.index(self.__current_sprite) >= len(self.__sprites) - 1:
                return self.__current_sprite
            if self.__animation_frame < self.__animation_speed:
                self.__animation_frame += self._owner.scene.game_speed
            else:
                self.__animation_frame = 0
                # переключиться на следующий
                self.__current_sprite = self.__sprites[self.__sprites.index(self.__current_sprite) + 1]
            return self.__current_sprite

    def __init__(self, max_payload=0, **kwargs):
        super(MotherShip, self).__init__(max_payload=max_payload, **kwargs)
        self.__health = theme.MOTHERSHIP_MAX_SHIELD
        # WARN: на момент создания материнского корабля не известен № комманды
        # поэтому создаем в момент первого обращения
        self.__death_animaion = None

    @property
    def sprite_filename(self):
        if self.is_alive:
            return 'teams/{}/mothership.png'.format(self.team)
        if self.__death_animaion is None:
            self.__death_animaion = self.__DeathAnimation(self)
        return self.__death_animaion.sprite_filename()  # 'mothership_{}_crashed.png'.format(self.team)

    @property
    def meter_1(self):
        return min(self._cargo.fullness, 1.0)

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
        self.__health = max(self.__health - damage, 0)

    def __heal_taken(self, healed_on=0):
        if self.__health > 0:
            self.__health = min(self.__health + healed_on, theme.MOTHERSHIP_MAX_SHIELD)

    def game_step(self):
        self.__heal_taken(theme.MOTHERSHIP_SHIELD_RENEWAL_RATE)

    def on_hearbeat(self):
        pass

    def on_stop(self):
        pass
