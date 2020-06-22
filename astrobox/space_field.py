# -*- coding: utf-8 -*-
import datetime
import math
import random
import uuid
from collections import Counter, defaultdict

from robogame_engine import Scene
from robogame_engine.geometry import Point, Vector

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
        self._prev_endgame_state = {}
        self._game_over_tics = 0
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
        # нужно тиков что бы дрону пролететь экран по диагонали
        _screen_diagonal = (theme.FIELD_WIDTH ** 2 + theme.FIELD_HEIGHT ** 2) ** .5
        self._game_over_tics = int(_screen_diagonal / theme.DRONE_SPEED)

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
            self.warning("Warning: not enough space cells to asteroids")

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

    def game_step(self):
        super().game_step()
        for base in self.motherships:
            if not base.is_alive:
                continue
            for drone in self.drones:
                if drone.team == base.team:
                    continue
                dist = base.radius - base.distance_to(drone)
                if dist < 0:
                    continue
                step_back_vector = Vector.from_points(base.coord, drone.coord, module=dist + 3)
                drone.coord += step_back_vector

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

    def _get_game_state(self):
        game_state = defaultdict(defaultdict)
        for team, objects in self.teams.items():
            game_state[team]['drones'] = sum(obj.payload if obj.is_alive else 0 for obj in objects)
        for ship in self.motherships:
            game_state[ship.team]['base'] = ship.payload if ship.is_alive else 0
        if theme.DRONES_CAN_FIGHT:
            # есть ли кто живой
            for team, objects in self.teams.items():
                game_state[team]['low_health'] = sum(obj.health for obj in objects if obj.is_alive)
            # база жива
            for ship in self.motherships:
                game_state[ship.team]['low_health'] += ship.health
        game_state['countdown'] = self._game_over_tics
        return game_state

    def print_game_statistics(self, stats):
        if self._game_statistics_printed:
            # пока висит экран, статистика может печаться
            return
        print()
        print('Rating after {} game steps:'.format(self._step))
        print('-' * 35)
        dead_teams = [ship.team for ship in self.motherships if not ship.is_alive]
        _rating = []
        for team in sorted(self.teams):
            elerium = stats[team]['base'] + stats[team]['drones']
            _rating.append((elerium, team, team in dead_teams))
        _rating.sort()
        _rating.reverse()
        for elerium, team, was_dead in _rating:
            mess = '{:<20}:{:>6} elerium'.format(team, elerium)
            if theme.DRONES_CAN_FIGHT and was_dead:
                mess += ' (was eliminated)'
            print(mess)
        self._game_statistics_printed = True

    def get_game_result(self):
        if self.hold_state:
            return False, {}
        _cur_state = self._get_game_state()
        if self._step > 17000:
            # абсолютный стоп, что бы там не было
            self.print_game_statistics(stats=_cur_state)
            return True, self._make_game_result(_cur_state)
        if not self._prev_endgame_state:
            self._prev_endgame_state = _cur_state
            return False, {}
        has_any_diff = False
        for team in self.teams:
            has_any_diff |= self._prev_endgame_state[team]['drones'] != _cur_state[team]['drones']
            has_any_diff |= self._prev_endgame_state[team]['base'] != _cur_state[team]['base']
            if theme.DRONES_CAN_FIGHT:
                has_any_diff |= abs(self._prev_endgame_state[team]['low_health'] - _cur_state[team]['low_health']) > 10
            if has_any_diff:
                break
        if has_any_diff:
            self._prev_endgame_state = _cur_state
            return False, {}
        self._prev_endgame_state['countdown'] -= 1
        is_game_over = self._prev_endgame_state['countdown'] <= 0
        if is_game_over:
            self.print_game_statistics(stats=_cur_state)
            return True, self._make_game_result(_cur_state)
        return False, {}

    def _make_game_result(self, _cur_state):
        _cur_state.pop('countdown')
        now = datetime.datetime.now()
        game_result = dict(game_steps=self._step, uuid=str(uuid.uuid4()), happened_at=now.strftime('%Y-%m-%d %H:%M:%S'))
        game_result['collected'] = {}
        for team, stat in _cur_state.items():
            game_result['collected'][team] = stat['drones'] + stat['base']
        if theme.DRONES_CAN_FIGHT:
            game_result['dead'] = {}
            for team, objects in self.teams.items():
                game_result['dead'][team] = sum(1 for obj in objects if not obj.is_alive)
        return game_result


