# -*- coding: utf-8 -*-
from robogame_engine.theme import theme


class Cargo(object):
    __payload = 0
    __max_volume = 0

    def __init__(self, owner, payload=0, max_payload=1):
        self.__owner = owner
        if max_payload < 1:
            raise ValueError("max_payload should be greater than 0")
        self.__payload = min(payload, max_payload)
        self.__max_payload = max_payload

    def __str__(self):
        return '[{}]{} payload {}/{}'.format(id(self), self.__class__.__name__, self.__payload, self.__max_payload)

    def _clip_payload(self, batch):
        if self.__payload < batch:
            batch = self.__payload
        self.__payload -= batch
        return batch

    def _transfer_payload(self, batch, cargo_from):
        batched = cargo_from._clip_payload(batch)
        self.__payload += batched
        return batched

    @property
    def owner(self):
        return self.__owner

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


class CargoTransition(object):
    selectable = False

    def __init__(self, cargo_from=None, cargo_to=None):
        super(CargoTransition, self).__init__()
        self.cargo_from = cargo_from
        self.cargo_to = cargo_to
        self.__distance = theme.CARGO_TRANSITION_DISTANCE
        self.__batch_processed = 0
        self.__transition_limit = max(min(self.cargo_to.free_space, self.cargo_from.payload), 0)
        self.__transition_speed = theme.CARGO_TRANSITION_SPEED
        if self.__transition_speed < 1:
            raise Exception("transition_speed should be greater than 0")
        self.__done = False
        self.__was_transfer = False

    @property
    def is_finished(self):
        return self.__done

    @property
    def was_transfer(self):
        return self.__was_transfer

    def game_step(self):
        self.__was_transfer = False
        # Ограничиваем дистанцию переноса
        if self.cargo_to.owner.distance_to(self.cargo_from.owner) >= self.__distance:
            self.__done = True
            return
        # Берем максимально возможный кусок который можем переместить за такт
        batch = min(self.__transition_speed,
                    self.__transition_limit - self.__batch_processed,
                    self.cargo_to.free_space, self.cargo_from.payload)
        if batch <= 0:
            self.__done = True
            return
        self.__batch_processed += self.cargo_to._transfer_payload(batch, self.cargo_from)
        self.__was_transfer = True
        if self.cargo_from.is_empty or self.cargo_to.is_full:
            self.__done = True
