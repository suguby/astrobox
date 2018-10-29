# -*- coding: utf-8 -*-

from .theme import theme
from .events import EventStoppedAtTargetPoint, EventStopped
from .geometry import Vector
from .utils import CanLogging


class ObjectState(CanLogging):

    def __init__(self, obj, target=None, speed=None, **kwargs):
        self.obj = obj
        self.kwargs = kwargs
        self.target_point = target.coord if hasattr(target, 'coord') else target
        self.speed = theme.MAX_SPEED if speed is None else speed
        if self.target_point:
            self.vector = Vector.from_points(self.obj.coord, self.target_point, module=self.speed)
        else:
            self.vector = None

    def move(self, target, speed):
        if self.obj.rotate_mode == theme.ROTATE_TURNING:
            self.obj.state = StateTurning(obj=self.obj, target=target, speed=speed)
            self.obj.state.move_at_target = True
        else:
            self.obj.state = StateMoving(obj=self.obj, target=target, speed=speed)

    def stop(self):
        self.obj.state = StateStopped(obj=self.obj)

    def turn(self, vector, target, speed=None):
        self.obj.state = StateTurning(obj=self.obj, vector=vector, target=target, speed=speed)

    def step(self):
        raise NotImplementedError

    def __str__(self):
        return "{}: {}".format(self.__class__.__name__, self.__dict__)


class StateTurning(ObjectState):
    move_at_target = False

    def __init__(self, obj, target=None, speed=None, **kwargs):
        super(StateTurning, self).__init__(obj=obj, target=target, speed=speed, **kwargs)
        self.turn_speed = speed if speed else theme.MAX_TURN_SPEED

    def step(self):
        obj = self.obj
        delta = self.vector.direction - obj.direction
        if abs(delta) < self.turn_speed:
            obj.vector = self.vector
            if self.move_at_target:
                obj.state = StateMoving(obj=obj, target=self.target_point, speed=self.speed)
            else:
                obj.state = StateStopped(obj=obj)
                event = EventStopped()
                self.obj.add_event(event)
        else:
            if -180 < delta < 0 or delta > 180:
                obj.vector.rotate(-self.turn_speed)
            else:
                obj.vector.rotate(self.turn_speed)


class StateMoving(ObjectState):

    def step(self):
        distance_to_target = self.obj.coord.distance_to(self.target_point)
        if distance_to_target < self.vector.module:
            self.obj.coord += Vector.from_direction(self.vector.direction, distance_to_target)
            self.obj.state = StateStopped(obj=self.obj)
            event = EventStoppedAtTargetPoint(self.target_point)
            self.obj.add_event(event)
        else:
            self.obj.coord += self.vector
            self.obj.vector = self.vector


class StateStopped(ObjectState):

    def stop(self):
        pass

    def step(self):
        pass


class StateDead(ObjectState):

    def move(self, target, speed):
        pass

    def stop(self):
        pass

    def turn(self, vector, target, speed=None):
        pass

    def step(self):
        pass
