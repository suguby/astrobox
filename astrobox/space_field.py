# -*- coding: utf-8 -*-
import math
import random
from collections import Counter

from robogame_engine import Scene
from robogame_engine.geometry import Point

from .core import MotherShip, Asteroid, Drone
from .theme import theme


class TooManyDrones(Exception):
    pass


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
        return "[{}] {}x{} ({}, {})".format(id(self), self.w, self.h, self.x, self.y)


class SpaceField(Scene):
    check_collisions = False
    detect_overlaps = True
    _CELL_JITTER = 0.7

    def __init__(self, *args, **kwargs):
        self.__motherships = {}
        self.__asteroids = []
        self.__drones = []
        if 'theme_mod_path' not in kwargs:
            kwargs['theme_mod_path'] = 'astrobox.themes.default'
        if 'can_fight' in kwargs:
            theme.DRONES_CAN_FIGHT = kwargs.pop('can_fight')
        self.max_drones_at_team = theme.MAX_DRONES_AT_TEAM
        self._prev_endgame_state = self._game_over_tics = None
        self._game_statistics_printed = False
        super(SpaceField, self).__init__(*args, **kwargs)

    def prepare(self, asteroids_count=5, max_drones_at_team=None):
        if max_drones_at_team is not None:
            self.max_drones_at_team = max_drones_at_team
        team_counter = Counter(drone.team for drone in self.drones)
        for team, count in team_counter.items():
            if count > self.max_drones_at_team:
                raise TooManyDrones(
                    'at team {team}. Only {max_drones_at_team} drones available'.format(
                        team=team, max_drones_at_team=self.max_drones_at_team
                    ))
        self._fill_space(
            asteroids_count=asteroids_count
        )
        # нужно тиков что бы дрону пролететь 3/4 экрана по диагонали
        _screen_diagonal = (theme.FIELD_WIDTH ** 2 + theme.FIELD_HEIGHT ** 2) ** .5
        self._game_over_tics = int((_screen_diagonal / theme.DRONE_SPEED) * .75)

    def _get_team_pos(self, team_number):
        radius = MotherShip.radius
        if team_number == 0:
            return Point(radius, radius)
        elif team_number == 1:
            return Point(theme.FIELD_WIDTH - radius, radius)
        elif team_number == 2:
            return Point(radius, theme.FIELD_HEIGHT - radius)
        else:
            return Point(theme.FIELD_WIDTH - radius, theme.FIELD_HEIGHT - radius)

    def _fill_space(self, asteroids_count, field_reduce_rate=1.5):
        field = Rect(w=theme.FIELD_WIDTH, h=theme.FIELD_HEIGHT)
        field.reduce(dw=MotherShip.radius * field_reduce_rate, dh=MotherShip.radius * field_reduce_rate)
        if self.teams_count >= 2:
            field.reduce(dw=MotherShip.radius * field_reduce_rate)
        if self.teams_count >= 3:
            field.reduce(dh=MotherShip.radius * field_reduce_rate)
        if field.w < MotherShip.radius or field.h < MotherShip.radius:
            raise Exception("Too little field...")
        self.info("Initial field {}".format(field))

        cells_in_width = int(math.ceil(math.sqrt(float(field.w) / field.h * asteroids_count)))
        cells_in_height = int(math.ceil(float(asteroids_count) / cells_in_width))
        cells_count = cells_in_height * cells_in_width
        self.info("Cells count {} {} {}".format(cells_count, cells_in_width, cells_in_height))
        if cells_count < asteroids_count:
            self.warning("Warning: not enough space sells to asteroids")

        cell = Rect(w=int(field.w / cells_in_width), h=int(field.h / cells_in_height))

        self.info("Adjusted cell {}".format(cell))

        cell_numbers = [i for i in range(cells_count)]

        jit_box = Rect(w=int(cell.w * self._CELL_JITTER), h=int(cell.h * self._CELL_JITTER))
        jit_box.shift(dx=(cell.w - jit_box.w) // 2, dy=(cell.h - jit_box.h) // 2)
        self.info("Jit box {}".format(jit_box))

        field.w = cells_in_width * cell.w + jit_box.w
        field.h = cells_in_height * cell.h + jit_box.h
        self.info("Adjusted field{}".format(field))

        field.x = MotherShip.radius * field_reduce_rate
        field.y = MotherShip.radius * field_reduce_rate
        self.info("Shifted field {}".format(field))

        # Генерируем количество элериума для астероидов
        asteroid_payloads = []
        for p in range(asteroids_count):
            payload = random.randint(theme.MIN_ASTEROID_ELERIUM, theme.MAX_ASTEROID_ELERIUM)
            asteroid_payloads.append(payload)
        # Отсортируем по убыванию
        asteroid_payloads.sort(key=lambda p: -p)

        # Генерируем позиции астероидов
        asteroid_coords = []
        for i in range(asteroids_count):
            cell_number = random.choice(cell_numbers)
            cell_numbers.remove(cell_number)
            cell.x = (cell_number % cells_in_width) * cell.w
            cell.y = (cell_number // cells_in_width) * cell.h
            dx = random.randint(0, jit_box.w)
            dy = random.randint(0, jit_box.h)
            pos = Point(field.x + cell.x + dx, field.y + cell.y + dy)
            asteroid_coords.append(pos)
        center_of_scene = Point(field.w / 2, field.h / 2)
        # Отсортируем по удалению от центра карты. Делается для того чтобы обеспечить
        # примерно равные условия для всех игроков, распределяя более объемные ресурсы
        # ближе к центру, что дает больше возможностей к выбору стратегий. Дает некий игровой баланс.
        # (например, постараться отхватить жирный кусок или подстрелить жаждущих наживы)
        asteroid_coords.sort(key=lambda c: c.distance_to(center_of_scene))

        for i, pos in enumerate(asteroid_coords):
            asteroid_payload = asteroid_payloads[i]
            asteroid = Asteroid(coord=pos, elerium=asteroid_payload)
            self.__asteroids.append(asteroid)

        max_elerium = round(sum(asteroid_payloads), -2) + 100
        if not theme.DRONES_CAN_FIGHT:
            max_elerium = round(max_elerium * 1.5 / self.teams_count, -2)
        if max_elerium < 1000:
            max_elerium = 1000

        for i, team_name in enumerate(self.teams):
            pos = self._get_team_pos(team_number=i)
            mothership = MotherShip(coord=pos.copy(), max_payload=max_elerium)
            mothership.set_team(team_name)
            self.__motherships[team_name] = mothership

        for drone in self.drones:
            # Перемещаем дронов к их месту спуна
            drone.coord = drone.mothership.coord.copy()

    def get_mothership(self, team_name):
        return self.__motherships.get(team_name)

    @property
    def drones(self):
        return self.get_objects_by_type(Drone)

    @property
    def asteroids(self):
        return self.get_objects_by_type(Asteroid)

    @property
    def motherships(self):
        return self.get_objects_by_type(MotherShip)

    def _get_endgame_state(self):
        endgame_state = dict(drones={}, bases={}, countdown=self._game_over_tics)
        if theme.DRONES_CAN_FIGHT:
            endgame_state['health'] = {}
        for team, objects in self.teams.items():
            endgame_state['drones'][team] = sum(obj.payload for obj in objects)
        for ship in self.motherships:
            endgame_state['bases'][ship.team] = ship.payload
        if theme.DRONES_CAN_FIGHT:
            # проверяем, есть ли кто живой со слабым здоровьем и что база не атакуется
            _drone_half_health = theme.DRONE_MAX_SHIELD * .33
            endgame_state['low_health'] = {}
            for team, objects in self.teams.items():
                endgame_state['low_health'][team] = any(obj.health < _drone_half_health
                                                        for obj in objects if obj.is_alive)
            for ship in self.motherships:
                endgame_state['low_health'][ship.team] |= (ship.is_alive
                                                           and ship.health < theme.MOTHERSHIP_MAX_SHIELD * .75)
        return endgame_state

    def print_game_statistics(self, game_over=False):
        if game_over and not self._game_statistics_printed:
            print()
            print('After {} game steps teams collect:'.format(self._step))
            print('-' * 35)
            winner, max_elerium = None, 0
            dead_teams = [ship.team for ship in self.motherships if not ship.is_alive]
            for team in sorted(self.teams):
                elerium = self._prev_endgame_state['bases'][team] + self._prev_endgame_state['drones'][team]
                if not theme.DRONES_CAN_FIGHT or team in dead_teams:
                    print('{:<20}:{:>6} elerium (but dead)'.format(team, elerium))
                else:
                    print('{:<20}:{:>6} elerium'.format(team, elerium))
                    if max_elerium < elerium:
                        winner, max_elerium = team, elerium
            print('-' * 35)
            print('Winner {:>28}'.format(winner))
            print()
            self._game_statistics_printed = True
        return game_over

    def is_game_over(self):
        if self._step > 27000:
            # абсолютный стоп, что бы там не было
            return self.print_game_statistics(True)
        _cur_state = self._get_endgame_state()
        if self._prev_endgame_state is None:
            self._prev_endgame_state = _cur_state
            return False
        has_drones_diff = any(self._prev_endgame_state['drones'][team] != elerium
                              for team, elerium in _cur_state['drones'].items())
        has_bases_diff = any(self._prev_endgame_state['bases'][team] != elerium
                             for team, elerium in _cur_state['bases'].items())
        has_low_health = False
        if theme.DRONES_CAN_FIGHT:
            has_low_health = any(low_health
                                 for team, low_health in _cur_state['low_health'].items())
        if has_drones_diff or has_bases_diff or has_low_health:
            self._prev_endgame_state = _cur_state
            return False
        self._prev_endgame_state['countdown'] -= 1
        return self.print_game_statistics(self._prev_endgame_state['countdown'] <= 0)


