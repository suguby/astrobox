from robogame_engine.theme import theme

class Cargo:
    __payload = 0
    __max_volume = 0
    def __init__(self, owner, payload=0, max_payload=1):
        self.__owner = owner
        if (max_payload<1):
            raise Exception("max_payload should be greater than 0");
        self.__payload = min(payload, max_payload)
        self.__max_payload = max_payload

    def __str__(self):
        return '[{}]{} payload {}/{}'.format(id(self), self.__class__.__name__, self.__payload, self.__max_payload)

    def _clip_payload(self, batch):
        self.__payload-=batch
        return 0

    def _transfer_payload(self, batch, cargo_from):
        cargo_from._clip_payload(batch)
        self.__payload+=batch

    @property
    def owner(self):
        return self.__owner

    @property
    def payload(self):
        return self.__payload

    @property
    def cargo_fullness(self):
        return self.__payload / float(self.__max_payload)

    @property
    def is_cargo_empty(self):
        return self.__payload <= 0

    @property
    def is_cargo_full(self):
        return self.__payload >= self.__max_payload

    @property
    def free_space(self):
        return self.__max_payload - self.__payload


class CargoTransition:
    __transition_speed = 0
    def __init__(self, cargo_from=None, cargo_to=None, transition_speed=None, transition_limit=None):
        self.cargo_from = cargo_from
        self.cargo_to = cargo_to
        self.__batch_processed = 0
        if transition_limit is None:
            transition_limit = self.cargo_to.free_space
        self.__transition_limit = transition_limit
        if transition_speed is None:
            transition_speed = theme.CARGO_TRANSITION_SPEED
        if transition_speed < 1:
            raise Exception("transition_speed should be greater than 0")
        self.__transition_speed = transition_speed
        self.__done = False

    @property
    def is_finished(self):
        return self.__done

    def game_step(self):
        if self.cargo_from.owner.team >= 0 and self.cargo_from.owner.team != self.cargo_to.owner.team:
            # Не можем загружать из чужих живых объектов
            if self.cargo_from.owner.is_alive:
                self.__done = True
                return
        # Неживые объекты не могут принимать
        if not self.cargo_to.owner.is_alive:
            self.__done = True
            return
        #print(self.__class__.__name__+"::game_step",
        #            self.__transition_speed,
        #            self.__transition_limit - self.__batch_processed,
        #            self.cargo_to.owner.__class__.__name__, self.cargo_to.free_space,
        #            self.cargo_from.owner.__class__.__name__, self.cargo_from.payload)
        batch = min(self.__transition_speed,
                    self.__transition_limit - self.__batch_processed,
                    self.cargo_to.free_space, self.cargo_from.payload)
        if batch <= 0:
            self.__done = True
            return
        self.__batch_processed += batch
        self.cargo_to._transfer_payload(batch, self.cargo_from)

