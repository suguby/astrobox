# -*- coding: utf-8 -*-

from astrobox.space_field import SpaceField
from astrobox.core import Drone, Unit
from astrobox.utils import nearest_angle_distance
from demo.strategies import *
from robogame_engine.geometry import Vector
from robogame_engine.theme import theme


class DroneUnitWithStrategies(Drone):
    def __init__(self, **kwargs):
        super(DroneUnitWithStrategies, self).__init__(**kwargs)
        self.__strategies = []

    def append_strategy(self, strategy):
        if strategy.is_group_unique:
            for s in self.__strategies:
                if s.group == strategy.group:
                    self.__strategies.remove(s)
        self.__strategies.append(strategy)

    def clear_strategies(self):
        self.__strategies = []

    def is_strategy_finished(self):
        return len(self.__strategies) == 0

    def game_step(self):
        self.native_game_step()
        for s in self.__strategies:
            if s.is_finished:
                self.__strategies.remove(s)
                continue
            s.game_step()
            break;

    @property
    def elerium_stocks(self):
        """возвращает все объекты мира из которых можно добывать ресурсы """
        return [es for es in self.scene.get_objects_by_type(Unit) if hasattr(es, 'cargo') and not es.is_alive]

    def native_game_step(self):
        """Позволяет обращаться к чистому обработчику из стратегий """
        super(DroneUnitWithStrategies, self).game_step()


class WorkerDrone(DroneUnitWithStrategies):
    counter_attrs = dict(size=22, position=(75, 135), color=(255, 255, 255))

    def __init__(self, **kwargs):
        super(WorkerDrone, self).__init__(**kwargs)
        self._elerium_stock = None

    @property
    def elerium_stock(self):
        return self._elerium_stock

    def set_elerium_stock(self, stock):
        self._elerium_stock = stock

    def on_born(self):
        super(WorkerDrone, self).on_born()
        self.append_strategy(StrategyHarvesting(unit=self))


class GreedyDrone(WorkerDrone):

    def __init__(self, **kwargs):
        super(GreedyDrone, self).__init__(**kwargs)

    def get_nearest_elerium_stock(self):
        elerium_stocks = [es for es in self.scene.asteroids if es.cargo.payload > 0]
        for drone in self.teammates:
            if drone.elerium_stock is not None and \
                    not drone.cargo.is_full and \
                    drone.elerium_stock in elerium_stocks:
                elerium_stocks.remove(drone.elerium_stock)

        if not elerium_stocks:
            return None
        # Берем наибольшее кол-во elerium-а, что сможем унести, из ближайшего
        elerium_stocks = sorted(elerium_stocks, key=lambda x: x.distance_to(self))
        nearest_stock = None
        max_elerium = 0
        for stock in elerium_stocks:
            if stock.cargo.payload >= self.cargo.free_space:
                return stock
            if stock.cargo.payload > max_elerium:
                nearest_stock = stock
                max_elerium = stock.cargo.payload
        if nearest_stock:
            return nearest_stock
        return random.choice(elerium_stocks)


class HunterDrone(GreedyDrone):
    _hunters = []

    def __init__(self, **kwargs):
        super(HunterDrone, self).__init__(**kwargs)
        self._hunting_strategy = None
        self._approach_strategy = None
        self._victim = None
        # self._no_victim_strategy = False
        self._victim_stamp = 0
        self._next_victim = None
        self.substrategy = None

    @property
    def victim(self):
        return self._victim

    def on_born(self):
        super(WorkerDrone, self).on_born()
        if self.have_gun:
            self._hunting_strategy = StrategyHunting.getTeamStrategy(self.team, self)
        else:
            self.append_strategy(StrategyHarvesting(unit=self))

    def on_stop(self):
        pass

    def get_nearest_elerium_stock(self):
        # Сперва сбор элериума с жертв
        elerium_stocks = [drone for drone in self.scene.drones
                          if not drone.is_alive and drone.cargo.payload > 0]
        for drone in self.teammates:
            if drone.elerium_stock is not None and \
                    not drone.cargo.is_full and \
                    drone.elerium_stock in elerium_stocks:
                elerium_stocks.remove(drone.elerium_stock)
        if elerium_stocks:
            elerium_stocks = sorted(elerium_stocks, key=lambda x: x.distance_to(self))
            return elerium_stocks[0]

        # Потом с астероидов
        elerium_stocks = [asteriod for asteriod in self.scene.asteroids if asteriod.cargo.payload > 0]
        for drone in self.teammates:
            if drone.elerium_stock is not None and \
                    not drone.cargo.is_full and \
                    drone.elerium_stock in elerium_stocks:
                elerium_stocks.remove(drone.elerium_stock)
        if not elerium_stocks:
            return None
        elerium_stocks = sorted(elerium_stocks, key=lambda x: x.distance_to(self))
        return elerium_stocks[0]

    def set_victim(self, victim):
        self._next_victim = None
        self._victim = victim
        self._victim_stamp = 0
        if not self.substrategy.is_finished:
            self.stop()
            self.state.stop()
        self.substrategy.reset()
        return victim.coord.copy()

    @property
    def is_unloading(self):
        return self.cargo.is_full or (self.substrategy is not None and
                                      self.substrategy.current_strategy_id == "approach&unload")

    def game_step(self):
        if not self.have_gun:
            super(HunterDrone, self).game_step()
            return

        self.native_game_step()
        if self._hunting_strategy is None:
            return
        self._hunting_strategy.game_step(self)
        if self.victim is not None:
            vector = Vector.from_points(self.coord, self.victim.coord,
                                        module=self.gun.shot_distance)
            if int(self.distance_to(self.victim)) < 1 or (
                    self.distance_to(self.victim) < vector.module
                    and abs(nearest_angle_distance(vector.direction, self.direction)) < 7
            ):
                self.gun.shot(self.victim)
        else:
            enemies = [enemy for enemy in self.scene.drones
                       if enemy.team != self.team and enemy.is_alive and
                       enemy.distance_to(self) < self.gun.shot_distance]
            enemie = sorted(enemies, key=lambda x: -x.cargo.payload)
            for enemy in enemies:
                vector = Vector.from_points(self.coord, enemy.coord)
                if abs(nearest_angle_distance(vector.direction, self.direction)) < 7:
                    self.gun.shot(enemy)
                    break
        pass


class RunnerDrone(DroneUnitWithStrategies):

    def any_asteroid(self):
        return random.choice(self.scene.asteroids)

    def on_born(self):
        self.append_strategy(StrategyApproach(unit=self, target_point=self.any_asteroid().coord, distance=0))

    def game_step(self):
        super(RunnerDrone, self).game_step()
        if self.is_strategy_finished():
            self.append_strategy(StrategyApproach(unit=self, target_point=self.any_asteroid().coord, distance=0))


class DestroyerDrone(DroneUnitWithStrategies):
    _hunters = []

    def __init__(self, **kwargs):
        super(DestroyerDrone, self).__init__(**kwargs)
        self._victim = None
        self._next_victim = None
        self._target_mship = None
        self._elerium_stock = None

    @property
    def elerium_stock(self):
        return self._elerium_stock

    def set_elerium_stock(self, stock):
        self._elerium_stock = stock

    def on_born(self):
        if self.have_gun:
            self.append_strategy(StrategyDestroyer(unit=self))
        else:
            self.append_strategy(StrategyHarvesting(unit=self))

    def game_step(self):
        super(DestroyerDrone, self).game_step()
        if self.have_gun:
            if self.is_strategy_finished():
                self.append_strategy(StrategyHarvesting(unit=self))


if __name__ == '__main__':
    space_field = SpaceField(
        name="Space war",
        speed=5,
        field=(1600, 800),
        asteroids_count=30,
        # can_fight=True,
    )

    teamA = [WorkerDrone() for _ in range(5)]
    teamB = [GreedyDrone() for _ in range(5)]
    teamC = [HunterDrone() for _ in range(5)]
    teamD = [DestroyerDrone() for _ in range(5)]

    space_field.go()
