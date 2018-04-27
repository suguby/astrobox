# -*- coding: utf-8 -*-
"""Тестовая игра"""
import random

from robogame_engine.theme import theme
from robogame_engine.geometry import Point
from astrobox.core import Dron, StarField


class WorkerDron(Dron):
    my_team_drones = []

    def is_other_dron_target(self, asteriod):
        for dron in WorkerDron.my_team_drones:
            if hasattr(dron, 'asteriod') and dron.asteriod and dron.asteriod.id == asteriod.id:
                return True
        return False

    def get_nearest_asteriod(self):
        asteriods_with_elerium = [asteriod for asteriod in self.asteriods if asteriod.elerium > 0]
        if not asteriods_with_elerium:
            return None
        nearest_asteroid = None
        for asteriod in asteriods_with_elerium:
            if self.is_other_dron_target(asteriod):
                continue
            if nearest_asteroid is None or self.distance_to(asteriod) < self.distance_to(nearest_asteroid):
                nearest_asteroid = asteriod
        return nearest_asteroid

    def go_next_asteriod(self):
        if self.is_full():
            self.move_at(self.my_mathership)
        else:
            self.asteriod = self.get_nearest_asteriod()
            if self.asteriod is not None:
                self.move_at(self.asteriod)
            elif self.payload > 0:
                self.move_at(self.my_mathership)
            else:
                i = random.randint(0, len(self.asteriods) - 1)
                self.move_at(self.asteriods[i])

    def on_born(self):
        WorkerDron.my_team_drones.append(self)
        self.go_next_asteriod()

    def on_stop_at_asteroid(self, asteriod):
        if asteriod.elerium > 0:
            self.load_from(asteriod)
        else:
            self.go_next_asteriod()

    def on_load_complete(self):
        self.go_next_asteriod()

    def on_stop_at_mathership(self, mathership):
        self.unload_to(mathership)

    def on_elerium_unloaded(self):
        self.go_next_asteriod()


class GreedyDron(WorkerDron):

    def get_nearest_asteriod(self):
        asteriods_with_elerium = [asteriod for asteriod in self.asteriods if asteriod.elerium > 0]
        if not asteriods_with_elerium:
            return None
        nearest_asteriod = None
        max_elerium = 0
        for asteriod in asteriods_with_elerium:
            if self.is_other_dron_target(asteriod):
                continue
            if asteriod.elerium > max_elerium:
                nearest_asteriod = asteriod
                max_elerium = asteriod.elerium
        if nearest_asteriod:
            return nearest_asteriod
        return random.choice(asteriods_with_elerium)


class HunterDron(GreedyDron):
    _hunters = []

    def on_born(self):
        if len(HunterDron._hunters) < 3:
            HunterDron._hunters.append(self)
        super(HunterDron, self).on_born()

    @classmethod
    def to_hunt(cls):
        commander = cls._hunters[0]
        drones = [dron for dron in commander.drons if not isinstance(dron, cls) and not dron.dead and dron.elerium > 0]
        drones = [dron for dron in drones if dron.distance_to(dron.my_mathership) > theme.MATHERSHIP_SAFE_DISTANCE]
        victim = None
        for dron in drones:
            if victim is None or (commander.distance_to(dron) < commander.distance_to(victim)):
                victim = dron
        if victim:
            can_sting = 0
            for hunter in cls._hunters:
                if hunter.distance_to(victim) < hunter.radius and hunter._health > theme.STING_POWER:
                    can_sting += 1
            if can_sting == len(cls._hunters):
                for hunter in cls._hunters:
                    hunter.sting(victim)
            else:
                for hunter in cls._hunters:
                    hunter.move_at(victim)
        else:
            drones = [dron for dron in commander.drons if not isinstance(dron, cls) and dron.dead and dron.elerium > 0]
            dead_elerium = sum(dron.elerium for dron in drones)
            hunter_elerium = sum(dron.elerium for dron in cls._hunters)
            hunters_capacity = sum(dron._max_elerium for dron in cls._hunters)
            if dead_elerium and hunter_elerium < hunters_capacity:
                victim = None
                for dron in drones:
                    if victim is None or (commander.distance_to(dron) < commander.distance_to(victim)):
                        victim = dron
                if victim:
                    if commander.distance_to(victim) < commander.radius:
                        for hunter in cls._hunters:
                            hunter.load_elerium_from(victim)
                    else:
                        for hunter in cls._hunters:
                            hunter.move_at(victim)
            if not dead_elerium and hunter_elerium:
                for hunter in cls._hunters:
                    hunter.move_at(hunter.my_mathership)

    def on_stop_at_asteroid(self, asteriod):
        HunterDron.to_hunt()
        super(HunterDron, self).on_stop_at_asteroid(asteriod)

    def on_stop_at_mathership(self, mathership):
        if self not in HunterDron._hunters:
            HunterDron.to_hunt()
        super(HunterDron, self).on_stop_at_mathership(mathership)

    def on_load_complete(self):
        HunterDron.to_hunt()
        super(HunterDron, self).on_load_complete()

    def on_elerium_unloaded(self):
        HunterDron.to_hunt()
        super(HunterDron, self).on_elerium_unloaded()


class Next2Dron(GreedyDron):
    pass


if __name__ == '__main__':
    star_field = StarField(
        name="Space war",
        speed=2,
        theme_mod_path='astrobox.themes.default',
        # field=(800, 600),
        asteroids_count=20,
        matherships_count=4,
    )

    count = 10
    drones = [WorkerDron(pos=Point(400, 400)) for i in range(count)]
    drones_2 = [GreedyDron() for i in range(count)]
    drones_3 = [HunterDron() for i in range(count)]
    drones_4 = [Next2Dron() for i in range(count)]

    dron = WorkerDron()
    dron.move_at(Point(1000, 1000))  # проверка на выход за границы экрана

    star_field.go()
