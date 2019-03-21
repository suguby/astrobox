# -*- coding: utf-8 -*-
import math
import random

from robogame_engine import GameObject
from robogame_engine.constants import ROTATE_TURNING
from robogame_engine.theme import theme

from .guns import PlasmaGun
from .cargo import Cargo


class Unit(GameObject):
    coord = None  # переопределяется в потомках
    radius = 0
    _cargo = None

    def __init__(self, **kwargs):
        super(Unit, self).__init__(**kwargs)
        self._move_target = None

    @property
    def cargo(self):
        return self._cargo

    @property
    def sprite_filename(self):
        return 'not-found.png'

    def move_at(self, target, speed=None):
        if self._move_target == target:
            return
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
        self.__mothership = None
        self._cargo = Cargo(self, payload=0, max_payload=theme.DRONE_CARGO_PAYLOAD)
        self.__gun = None
        if theme.DRONES_CAN_FIGHT:
            self.__gun = PlasmaGun(self)
        self.__health = theme.DRONE_MAX_SHIELD
        super(DroneUnit, self).__init__(**kwargs)

        self.__dead_flight_speed = theme.DRONE_DEAD_SPEED
        self.__angle_of_death = None
        self.__death_animaion = self.__DeathAnimation(self)

    @property
    def have_gun(self):
        return self.__gun is not None

    @property
    def gun(self):
        return self.__gun

    @property
    def teammates(self):
        return [mate for mate in self.scene.drones if mate != self and mate.team == self.team and mate.is_alive]

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
        # print(self.__class__.__name__+"::damage_taken", damage)
        self.__health = max(self.__health - damage, 0)
        if self.__health <= 0:
            self.stop()

    def __heal_taken(self, healed_on=0):
        if self.__health > 0:
            self.__health = min(self.__health + healed_on, theme.DRONE_MAX_SHIELD)

    def mothership(self):
        if self.__mothership is None:
            self.__mothership = self.scene.get_mothership(self.team)
            assert self.__mothership is not None
        return self.__mothership

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
        super(DroneUnit, self).game_step()

    def game_step(self):
        if not self.is_alive:
            self.__dead_game_step()
            return
        if self.mothership() and self.mothership().is_alive and \
                self.distance_to(self.mothership().coord) < theme.MOTHERSHIP_HEALING_DISTANCE:
            self.__heal_taken(theme.MOTHERSHIP_HEALING_RATE)
        else:
            self.__heal_taken(theme.DRONE_SHIELD_RENEWAL_RATE)
        if self.have_gun:
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


# XXX: удалить этот класс после завершения курса
class Drone(DroneUnit):
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
        self._cargo = Cargo(self, payload=elerium, max_payload=elerium)
        self.__sprite_num = random.randint(1, 5)
        self._size = (elerium / theme.MIN_ASTEROID_ELERIUM) * .8
        super(Asteroid, self).__init__(**kwargs)

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
    radius = 75
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
        super(MotherShip, self).__init__(**kwargs)
        self._cargo = Cargo(self, payload=0, max_payload=max_payload)
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
