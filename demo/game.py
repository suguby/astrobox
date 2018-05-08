# -*- coding: utf-8 -*-
import random

from robogame_engine.theme import theme
from robogame_engine.geometry import Point
from astrobox.core import Dron
from astrobox.spase_field import StarField


class WorkerDron(Dron):
    my_team_drones = []

    def is_other_dron_target(self, asteriod):
        for dron in WorkerDron.my_team_drones:
            if hasattr(dron, 'asteriod') and dron.asteriod and dron.asteriod.id == asteriod.id:
                return True
        return False

    def get_nearest_asteriod(self):
        asteriods_with_elerium = [asteriod for asteriod in self.asteroids if asteriod.payload > 0]
        if not asteriods_with_elerium:
            return None
        nearest_asteroid = None
        for asteriod in asteriods_with_elerium:
            if self.is_other_dron_target(asteriod):
                continue
            if nearest_asteroid is None or self.distance_to(asteriod.coord) < self.distance_to(nearest_asteroid.coord):
                nearest_asteroid = asteriod
        return nearest_asteroid

    def go_next_asteriod(self):
        if self.is_full:
            self.move_at(self.my_mathership)
        else:
            self.asteriod = self.get_nearest_asteriod()
            if self.asteriod is not None:
                self.move_at(self.asteriod)
            elif self.payload > 0:
                self.move_at(self.my_mathership)
            else:
                i = random.randint(0, len(self.asteroids) - 1)
                self.move_at(self.asteroids[i])

    def on_born(self):
        WorkerDron.my_team_drones.append(self)
        self.go_next_asteriod()

    def on_stop_at_asteroid(self, asteriod):
        if asteriod.payload > 0:
            self.load_from(asteriod)
        else:
            self.go_next_asteriod()

    def on_load_complete(self):
        self.go_next_asteriod()

    def on_stop_at_mathership(self, mathership):
        self.unload_to(mathership)

    def on_unload_complete(self):
        self.go_next_asteriod()


class GreedyDron(WorkerDron):

    def get_nearest_asteriod(self):
        asteriods_with_elerium = [asteriod for asteriod in self.asteroids if asteriod.payload > 0]
        if not asteriods_with_elerium:
            return None
        nearest_asteriod = None
        max_elerium = 0
        for asteriod in asteriods_with_elerium:
            if self.is_other_dron_target(asteriod):
                continue
            if asteriod.payload > max_elerium:
                nearest_asteriod = asteriod
                max_elerium = asteriod.payload
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
        drones = [dron for dron in commander.drones if not isinstance(dron, cls) and not dron.dead and dron.payload > 0]
        drones = [dron for dron in drones if dron.distance_to(dron.my_mathership.coord) > theme.MATHERSHIP_SAFE_DISTANCE]
        victim = None
        for dron in drones:
            if victim is None or (commander.distance_to(dron.coord) < commander.distance_to(victim.coord)):
                victim = dron
        if victim:
            can_sting = 0
            for hunter in cls._hunters:
                if hunter.distance_to(victim.coord) < hunter.radius and hunter._health > theme.STING_POWER:
                    can_sting += 1
            if can_sting == len(cls._hunters):
                for hunter in cls._hunters:
                    hunter.sting(victim)
            else:
                for hunter in cls._hunters:
                    hunter.move_at(victim)
        else:
            drones = [dron for dron in commander.drons if not isinstance(dron, cls) and dron.dead and dron.payload > 0]
            dead_elerium = sum(dron.payload for dron in drones)
            hunter_elerium = sum(dron.payload for dron in cls._hunters)
            hunters_capacity = sum(dron._max_elerium for dron in cls._hunters)
            if dead_elerium and hunter_elerium < hunters_capacity:
                victim = None
                for dron in drones:
                    if victim is None or (commander.distance_to(dron.coord) < commander.distance_to(victim.coord)):
                        victim = dron
                if victim:
                    if commander.distance_to(victim.coord) < commander.radius:
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

    def on_unload_complete(self):
        HunterDron.to_hunt()
        super(HunterDron, self).on_unload_complete()


class RunnerDron(Dron):

    def on_born(self):
        x = 1000 + random.randint(0, 500) if self.coord.x < 300 else random.randint(0, 100)
        y = 1000 + random.randint(0, 500) if self.coord.y < 300 else random.randint(0, 100)
        self.move_at(Point(x, y))  # проверка на выход за границы экрана


if __name__ == '__main__':
    star_field = StarField(
        name="Space war",
        speed=1,
        theme_mod_path='astrobox.themes.default',
        field=(1600, 800),
        asteroids_count=20,
    )

    count = 3
    drones = [WorkerDron() for i in range(count)]
    # drones_2 = [GreedyDron() for i in range(count)]
    # drones_3 = [HunterDron() for i in range(count)]
    drones_4 = [RunnerDron() for i in range(count)]

    star_field.go()
