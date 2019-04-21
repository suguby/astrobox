# -*- coding: utf-8 -*-
import random

from robogame_engine.theme import theme

from astrobox.cargo import CargoTransition


class Strategy(object):
    def __init__(self, unit=None, id=None, group=None, is_group_unique=False):
        self.__unit = unit
        self.__id = id
        self.__group = group
        self.__group_unique = is_group_unique

    @property
    def unit(self):
        return self.__unit

    @property
    def id(self):
        return self.__id

    @property
    def group(self):
        return self.__group

    @property
    def is_group_unique(self):
        return self.__group_unique

    def reset(self):
        pass

    @property
    def is_finished(self):
        return False

    def game_step(self):
        pass

    def on_stop(self):
        pass


# Атомарные стратегии
class StrategyCargoLoading(Strategy):
    def __init__(self, cargo_transition, **kwargs):
        kwargs['id'] = "cargo|loading"
        kwargs['group'] = "cargo"
        super(StrategyCargoLoading, self).__init__(kwargs)
        self.__transition = cargo_transition

    @property
    def is_finished(self):
        return self.__transition.is_finished

    def game_step(self):
        self.__transition.game_step()


class StrategyCargoUnloading(Strategy):
    def __init__(self, cargo_transition, **kwargs):
        kwargs['id'] = "cargo|unloading"
        kwargs['group'] = "cargo"
        super(StrategyCargoUnloading, self).__init__(**kwargs)
        self.__transition = cargo_transition

    @property
    def is_finished(self):
        return self.__transition.is_finished

    def game_step(self):
        self.__transition.game_step()


class StrategyApproach(Strategy):
    def __init__(self, target_point=None, distance=0, condition=None, **kwargs):
        if "id" not in kwargs:              kwargs["id"] = "approach"
        if "group" not in kwargs:           kwargs["group"] = "approach"
        if "is_group_unique" not in kwargs: kwargs["is_group_unique"] = True
        super(StrategyApproach, self).__init__(**kwargs)
        self._target_point = target_point
        self._target_distance = distance
        self.__done = False
        self.__last_distance = None
        self.__conditional_approach = condition

    @property
    def is_finished(self):
        # Если усnановлено условие сближения и оно ложно, заканчиваем выполненение
        if self.__conditional_approach is not None and not self.__conditional_approach():
            return True
        return int(self.unit.distance_to(self._target_point)) <= self._target_distance

    def game_step(self):
        new_distance = int(self.unit.distance_to(self._target_point))
        if self.__last_distance is not None and new_distance < self.__last_distance:
            self.__last_distance = new_distance
            return
        if self.unit.is_moving:
            return
        if new_distance > self._target_distance:
            self.__last_distance = new_distance
            self.unit.move_at(self._target_point.copy(), speed=theme.DRONE_SPEED)


# Комбинированные стратегии
class StrategySequence(Strategy):
    def __init__(self, *strategies, **kwargs):
        super(StrategySequence, self).__init__(**kwargs)
        self.__strategies = strategies
        self.__current_strategy = self.__strategies[0]

    def _next_strategy(self):
        if self.__current_strategy is None:
            return False
        strategy_id = self.__strategies.index(self.__current_strategy)
        if strategy_id < 0 or strategy_id + 1 >= len(self.__strategies):
            self.__current_strategy = None
            return False
        self.__current_strategy = self.__strategies[strategy_id + 1]
        return True

    def __str__(self):
        strout = "{} {} {}(".format(self.__class__.__name__, self.unit.__class__.__name__, self.unit)
        for s in self.__strategies:
            strout += ("{}" if self.__strategies.index(s) == 0 else ", {}").format(str(s))
        return strout + ")"

    @property
    def is_finished(self):
        return self.__current_strategy is None

    def game_step(self):
        if self.__current_strategy is None:
            return
        if self.__current_strategy.is_finished:
            if not self._next_strategy():
                return
        self.__current_strategy.game_step()


class StrategyApproachAndLoad(StrategySequence):
    def __init__(self, unit=None, target_unit=None, distance=None, **kwargs):
        if distance is None:
            distance = theme.CARGO_TRANSITION_DISTANCE - 1
        super(StrategyApproachAndLoad, self).__init__(
            StrategyApproach(unit=unit, target_point=target_unit.coord, distance=distance,
                             condition=self.check_target_have_elerium),
            StrategyCargoLoading(CargoTransition(cargo_from=target_unit.cargo, cargo_to=unit.cargo),
                                 unit=unit, is_group_unique=True),
            unit=unit, id="approach&load", group="approach", is_group_unique=True)
        self.__target_unit = target_unit

    def check_target_have_elerium(self):
        return self.__target_unit.cargo.payload > 0


class StrategyApproachAndUnload(StrategySequence):
    def __init__(self, unit=None, target_unit=None, distance=0, **kwargs):
        super(StrategyApproachAndUnload, self).__init__(
            StrategyApproach(unit=unit, target_point=target_unit.coord, distance=distance),
            StrategyCargoUnloading(CargoTransition(cargo_from=unit.cargo, cargo_to=target_unit.cargo),
                                   unit=unit, is_group_unique=True),
            unit=unit, id="approach&unload", group="approach", is_group_unique=True)
        self.__cargo_unloading = None


# Комплексные стратегии
class StrategyHarvesting(Strategy):
    def __init__(self, unit=None):
        super(StrategyHarvesting, self).__init__(unit=unit, id="harvesting", group="harvest", is_group_unique=True)
        self.__substrategy = None
        assert unit is not None
        assert hasattr(unit, 'elerium_stock')

    def anyAsteroid(self):
        return random.choice(self.unit.scene.asteroids)

    def reset(self):
        self.__substrategy = None

    @property
    def current_strategy_id(self):
        if self.__substrategy is not None:
            return self.__substrategy.id
        return ""

    def get_nearest_elerium_stock(self):
        elerium_stocks = [asteriod for asteriod in self.unit.scene.asteroids if asteriod.cargo.payload > 0]
        elerium_stocks += [drone for drone in self.unit.scene.drones if not drone.is_alive and drone.cargo.payload > 0]
        for drone in self.unit.teammates:
            if drone.elerium_stock is not None and \
                    not drone.cargo.is_full and \
                    drone.elerium_stock in elerium_stocks:
                elerium_stocks.remove(drone.elerium_stock)

        if not elerium_stocks:
            return None
        elerium_stocks = sorted(elerium_stocks, key=lambda x: x.distance_to(self.unit))
        return elerium_stocks[0]

    def game_step(self):
        # Даем возможность переопределять выбор источника elerium'а
        nearest_calc = self.unit if hasattr(self.unit, 'get_nearest_elerium_stock') else self
        if self.__substrategy is None or self.__substrategy.is_finished:
            if self.unit.cargo.is_full:
                self.unit.set_elerium_stock(None)
                self.__substrategy = StrategyApproachAndUnload(unit=self.unit, target_unit=self.unit.mothership)
            else:
                near_elerium_stock = nearest_calc.get_nearest_elerium_stock()
                if near_elerium_stock is not None:
                    self.unit.set_elerium_stock(near_elerium_stock)
                    self.__substrategy = StrategyApproachAndLoad(unit=self.unit, target_unit=near_elerium_stock)
                else:
                    if self.unit.cargo.payload > 0 and not self.unit.mothership.cargo.is_full:
                        self.unit.set_elerium_stock(None)
                        self.__substrategy = StrategyApproachAndUnload(unit=self.unit,
                                                                       target_unit=self.unit.mothership)
                    else:
                        # Делаем видимость загруженности дрона работой
                        self.__substrategy = StrategyApproach(unit=self.unit, target_point=self.anyAsteroid().coord)
        if self.__substrategy is not None:
            self.__substrategy.game_step()


class StrategyHunting(Strategy):
    _teams_strategies = {}

    @classmethod
    def getTeamStrategy(cls, team, hunter):
        if team not in cls._teams_strategies:
            cls._teams_strategies[team] = StrategyHunting(unit=hunter, id="hunting", group="hunting",
                                                          is_group_unique=True)
        return cls._teams_strategies[team]

    def __init__(self, **kwargs):
        super(StrategyHunting, self).__init__(**kwargs)
        self._hunters = []
        self._victims = []

    def get_victim(self, hunter):
        if hunter not in self._hunters:
            self._hunters.append(hunter)

        if hunter.victim is not None \
                and hunter.victim.distance_to(hunter.victim.mothership) > theme.MOTHERSHIP_SAFE_DISTANCE \
                and hunter.victim.cargo.payload > 0:
            return hunter.victim

        # Все дроны оппонентов с непустым карго
        enemies = [drone for drone in hunter.scene.drones if
                   drone.team != hunter.team and drone.is_alive and drone.cargo.payload > 0]
        # Дроны оппонетнов дальше, чем дистанция до их mothership-а
        enemies = [enemy for enemy in enemies if enemy.distance_to(enemy.mothership) > theme.MOTHERSHIP_SAFE_DISTANCE]
        for mate in self._hunters:
            if hunter != mate and mate.victim is not None and mate.victim in enemies:
                enemies.remove(mate.victim)
        victim = None
        for enemy in enemies:
            if victim is None or hunter.distance_to(enemy) < hunter.distance_to(victim):
                victim = enemy
        return victim

    def game_step(self, hunter):
        if not hasattr(hunter, 'substrategy') or hunter.substrategy is None:
            hunter.substrategy = StrategyHarvesting(unit=hunter)

        if hunter.victim is not None and (not hunter.victim.is_alive or
                                          int(hunter.victim.distance_to(
                                              hunter.victim.mothership)) < theme.MOTHERSHIP_HEALING_DISTANCE):
            hunter._victim = None
            hunter._victim_stamp = 0

        move_at_point = None
        DRONE_VICTIM_FOCUS_TIME = 4
        if hunter.victim is not None:
            # Счетчик повторного поиска жертвы
            hunter._victim_stamp = min(hunter._victim_stamp + 1, DRONE_VICTIM_FOCUS_TIME)

        # Разгрузимся, чтобы не потерять нажитое
        if hunter.is_unloading:
            # Собираем елериум пока не нашли жертву
            # print(self.__class__.__name__+"::game_step", "bringing elerium to mothership")
            hunter.substrategy.game_step()
            return

        # Получим ближайшую жертву от другого вызова game_step
        if hunter._next_victim is not None:
            if hunter.victim is None:
                move_at_point = hunter.set_victim(hunter._next_victim)

        # Выберем ближашего свободного союзника
        victim = None
        while True:
            victim = self.get_victim(hunter)
            if victim is None:
                break
            victim_distance = victim.distance_to(hunter)
            closertm = [mate for mate in hunter.teammates if
                        mate.victim is None and mate.distance_to(victim) < victim_distance]
            closertm = [mate for mate in closertm if mate._next_victim is None and not mate.is_unloading]
            if not closertm:
                # нет никого свобожного ближе
                break
            closertm = sorted(closertm, key=lambda x: x.distance_to(victim))
            closertm[0]._next_victim = victim
            victim = None
        is_new_victim = victim is not None and hunter.victim != victim

        if is_new_victim:
            move_at_point = hunter.set_victim(victim)
        elif hunter.victim is not None:
            if hunter.state.target_point != hunter.victim.coord and hunter._victim_stamp >= DRONE_VICTIM_FOCUS_TIME:
                # Обновим вектор движения раз в несколько циклов
                hunter._victim_stamp = 0
                move_at_point = hunter.victim.coord.copy()
        if move_at_point is not None and int(hunter.distance_to(move_at_point)) > hunter.radius:
            hunter.move_at(move_at_point.copy(), speed=theme.DRONE_SPEED)

        # Собираем елериум пока не нашли жертву
        if hunter.victim is None and victim is None:
            hunter.substrategy.game_step()


class StrategyDestroyer(Strategy):
    def __init__(self, **kwargs):
        super(StrategyDestroyer, self).__init__(**kwargs)
        self.__substrategy = None
        self._target_unit = None
        self.__done = False
        self.__substrategy = None
        ms = self.nearest_enemy_mothership()
        if ms is not None:
            self.__substrategy = StrategyApproach(unit=self.unit, target_point=ms.coord.copy(),
                                                  distance=self.unit.gun.shot_distance)
        self._target_unit = ms
        assert self.unit is not None
        # Требуется для StrategyHarvesting
        assert hasattr(self.unit, 'elerium_stock')

    def nearest_enemy_mothership(self):
        motherships = [m for m in self.unit.scene.motherships if m.team != self.unit.team and m.is_alive]
        if motherships:
            motherships = sorted(motherships, key=lambda x: x.distance_to(self.unit))
            return motherships[0]
        return None

    @property
    def is_finished(self):
        return self.__done

    def game_step(self):
        if self.__substrategy is not None:
            self.__substrategy.game_step()
            if not self.__substrategy.is_finished:
                return
            self.__substrategy = None

        if self._target_unit and self._target_unit.is_alive:
            self.unit.gun.shot(self._target_unit)
            return

        if self._target_unit is not None and not self._target_unit.is_alive:
            ms = self.nearest_enemy_mothership()
            if ms is not None:
                self.__substrategy = StrategyApproach(unit=self.unit, target_point=ms.coord.copy(),
                                                      distance=self.unit.gun.shot_distance)
            self._target_unit = ms
            return

        if self._target_unit is None:
            self.__done = True
