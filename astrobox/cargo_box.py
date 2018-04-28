# -*- coding: utf-8 -*-

from robogame_engine.utils import CanLogging
from robogame_engine.theme import theme


class CargoBox(CanLogging):
    """Класс кузова для перевозки и хранения элериума"""
    __load_speed = None
    __load_distance = None
    __payload = 0
    __max_payload = 0
    # TODO подумать держать __cargo_source и __cargo_target, без стейта,
    # TODO тогда можно трансферить елериум - сразу и загружать и разгружать
    __cargo_jack = None
    __cargo_state = 'hold'
    coord = None  # переопределяется в потомках

    def __init__(self, initial_cargo, maximum_cargo):
        self.__payload = initial_cargo
        if maximum_cargo <= 0:
            raise Exception("max_payload must be positive!")
        self.__max_payload = maximum_cargo
        if CargoBox.__load_speed is None:
            CargoBox.__load_speed = theme.LOAD_SPEED
            CargoBox.__load_distance = theme.LOAD_DISTANCE

    def __str__(self):
        return '{} payload {}/{}'.format(self.__class__.__name__, self.__payload, self.__max_payload)

    @property
    def payload(self):
        return self.__payload

    @property
    def fullness(self):
        return self.__payload / float(self.__max_payload)

    @property
    def is_empty(self):
        return self.__payload <= 0

    @property
    def is_full(self):
        return self.__payload >= self.__max_payload

    @property
    def free_space(self):
        return self.__max_payload - self.__payload

    def load_from(self, source):
        if isinstance(source, CargoBox):
            self.__cargo_jack = source
            self.__cargo_state = 'loading'
        else:
            raise Exception('Source for CargoBox can be only CargoBox!')

    def unload_to(self, target):
        if isinstance(target, CargoBox):
            self.__cargo_jack = target
            self.__cargo_state = 'unloading'
        else:
            raise Exception('Target for CargoBox can be only CargoBox!')

    def on_load_complete(self):
        pass

    def on_unload_complete(self):
        pass

    def game_step(self):
        if self.__cargo_jack is None or self.__cargo_state == 'hold':
            return
        if not self.__at_load_distance(self.__cargo_jack):
            self.__stop_transfer()
        elif self.__cargo_state == 'unloading':
            self.__proceed_unloading()
        elif self.__cargo_state == 'loading':
            self.__proceed_loading()

    def __proceed_loading(self):
        if self.is_full or self.__cargo_jack.is_empty:
            self.__end_exchange(event=self.on_load_complete)
            return
        batch = self.__cargo_jack.__get_cargo(for_target=self)
        self.__put_cagro(batch)
        if self.is_full or self.__cargo_jack.is_empty:
            self.__end_exchange(event=self.on_load_complete)

    def __proceed_unloading(self):
        if self.is_empty or self.__cargo_jack.is_full:
            self.__end_exchange(event=self.on_unload_complete)
            return
        batch = self.__get_cargo(for_target=self.__cargo_jack)
        self.__cargo_jack.__put_cagro(batch)
        if self.is_empty or self.__cargo_jack.is_full:
            self.__end_exchange(event=self.on_unload_complete)

    def __at_load_distance(self, other):
        # TODO тут еще подключить радиус обьекта, что бы можно было с края астероида выкачивать
        distance = ((self.coord.x - other.coord.x) ** 2 + (self.coord.y - other.coord.y) ** 2) ** .5
        return distance < self.__load_distance

    def __end_exchange(self, event):
        self.__stop_transfer()
        try:
            event()
        except Exception as exc:
            self.error("Exception at {} event {} handle: {}".format(self, event, exc))

    def __stop_transfer(self):
        self.__cargo_jack = None
        self.__cargo_state = 'hold'

    def __get_cargo(self, for_target):
        batch = min(self.__payload, for_target.free_space, self.__load_speed)
        self.__payload -= batch
        return batch

    def __put_cagro(self, value):
        part = min(value, self.__max_payload - self.__payload)
        self.__payload += part



