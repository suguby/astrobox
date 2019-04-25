# -*- coding: utf-8 -*-
from robogame_engine import GameObject
from robogame_engine.constants import ROTATE_TURNING
from robogame_engine.geometry import Vector
from robogame_engine.theme import theme


class Projectile(GameObject):
    """описывает поведение полета снаряда."""
    coord = None
    rotate_mode = ROTATE_TURNING
    radius = 1
    selectable = False
    layer = 3

    death_animation = None
    max_distance = 100.0

    def __init__(self, owner=None, speed=None, ttl=None, attached_ttl=None, **kwargs):
        super(Projectile, self).__init__(**kwargs)
        self.__initial_coord = owner.coord.copy()
        self._owner = owner
        self.__ttl = ttl
        self.__speed = speed
        self.__attached = None
        self.__attached_ttl = attached_ttl

    @property
    def sprite_filename(self):
        return "not-found.png"

    @property
    def owner(self):
        return self._owner

    @property
    def ttl(self):
        return self.__ttl

    @property
    def has_hit(self):
        return self.__attached is not None

    @property
    def attached(self):
        return self.__attached

    @property
    def zoom(self):
        if self.has_hit:
            return self.__attached.zoom
        return 0.5

    @property
    def is_alive(self):
        return self.__ttl > 0

    def game_step(self):
        if not theme.DRONES_CAN_FIGHT:
            return

        if self.has_hit:
            self.__attached.game_step()
            return

        if self.is_alive:
            self.__ttl = max(self.__ttl - 1, 0)
            # Обычный цикл полета пока живы
            super(Projectile, self).game_step()
        else:
            # Останавливаемся если отжили цикл полета
            # Используем прямой вызов останова, вместо события
            self.state.stop()
            # Промах, никакой анимации
            self.scene.remove_object(self)

    def turn_to(self, target, speed=None):
        # Снаряд не управляемый
        pass

    def move_at(self, target, speed=None):
        # Двигаемся только по прямой, незачем иметь возможность изменять маршрут
        pass

    def on_stop(self):
        pass

    def on_born(self):
        if not theme.DRONES_CAN_FIGHT:
            self.scene.remove_object(self)
            return
        vector = Vector.from_direction(self._owner.direction, module=PlasmaProjectile.max_distance)
        point = self._owner.coord.copy() + vector
        super(Projectile, self).move_at(point, speed=self.__speed)

    def on_overlap_with(self, obj_status):
        if not hasattr(obj_status, "damage_taken"):
            return
        # Пролетаем некомандные объекты
        if obj_status.team is None:
            return
        if theme.TEAM_DRONES_FRIENDLY_FIRE:
            # Не наносим урон себе
            if obj_status.id == self._owner.id:
                return
        else:
            # Пролетаем свои объекты
            if obj_status.team == self._owner.team:
                return
        # За премя жизни ни в кого не попали
        if not obj_status.is_alive or not self.is_alive:
            return
        self.__ttl = 0
        self.stop()
        self.state.stop()
        obj_status.damage_taken(theme.PROJECTILE_DAMAGE)
        if self.death_animation is not None:
            self.__attached = self.death_animation(
                projectile=self, target=obj_status,
                distance=int(obj_status.distance_to(self) / 2),
                direction=Vector.from_points(obj_status.coord, self.coord).direction,
                ttl=self.__attached_ttl
            )


class Gun(object):
    projectile = None

    def __init__(self, owner=None):
        self._owner = owner
        self._cooldown = 0

    @property
    def owner(self):
        return self._owner

    @property
    def can_shot(self):
        return self._cooldown <= 0

    @property
    def shot_distance(self):
        return self.projectile.max_distance

    def shot(self, target):
        if not self._owner.is_alive:
            return
        if not theme.DRONES_CAN_FIGHT or not self.can_shot:
            return
        self._cooldown = theme.PLASMAGUN_COOLDOWN_TIME
        coord = self.owner.coord.copy()
        prtl = self.projectile(coord=coord.copy(), owner=self.owner, direction=self.owner.direction)
        prtl.set_team(self.owner.team)

    def game_step(self):
        # Восстановление после выстрела
        if self._cooldown > 0:
            self._cooldown = max(self._cooldown - theme.PLASMAGUN_COOLDOWN_RATE, 0)

    @property
    def cooldown(self):
        return self._cooldown


class PlasmaProjectile(Projectile):
    """Используемый снаряд"""
    radius = 15
    max_distance = 580.0

    class __DeathAnimation(object):
        """
            хранит информацию о цели и имееют свое время жизни для
            для поддержания жизнеспособности projectile с анимацией
        """
        def __init__(self, projectile=None, target=None, distance=None, direction=None, ttl=0):
            self.__projectile = projectile
            self.__target = target
            self.__distance = distance
            self.__direction = direction
            self.__initial_target_direction = target.direction
            self.__initial_ttl = ttl
            self.__ttl = ttl

        @property
        def zoom(self):
            t = self.__initial_ttl
            return 1.0 * self.__ttl / t if self.__ttl > 0 else 0.5

        @property
        def sprite_filename(self):
            return "teams/any_projectile_explosion.png"

        @property
        def target(self):
            return self.__target

        @property
        def distance(self):
            return self.__distance

        @property
        def direction(self):
            return self.__direction

        @property
        def ttl(self):
            return self.__ttl

        @property
        def is_alive(self):
            return self.__ttl > 0

        def game_step(self):
            if self.is_alive:
                self.__ttl = max(self.__ttl - self.__projectile._owner.scene.game_speed, 0)
            else:
                return

            # Были прикреплены к оппоненту, анимируем попадание
            direction = - self.__initial_target_direction + self.__target.direction + self.__direction
            vector = Vector.from_direction(direction, module=self.__distance)
            self.__projectile.coord.x = self.__target.x + vector.x
            self.__projectile.coord.y = self.__target.y + vector.y

            if not self.is_alive:
                self.__projectile.scene.remove_object(self.__projectile)

    death_animation = __DeathAnimation

    def __init__(self, **kwargs):
        super(PlasmaProjectile, self).__init__(
            speed=theme.PROJECTILE_SPEED,
            ttl=theme.PROJECTILE_TTL,
            attached_ttl=int(theme.PROJECTILE_TTL / 4), **kwargs
        )

    @property
    def sprite_filename(self):
        if self.is_alive or self.attached is None:
            return "teams/{}/projectile.png".format(self.owner.team)
        return self.attached.sprite_filename

    @property
    def zoom(self):
        if self.has_hit:
            # Эффект попадания в цель
            return self.attached.zoom
        else:
            # эффект появления, чтобы снаряд не возникал из ниоткуда
            showTime = 5
            bornTime = theme.PROJECTILE_TTL - self.ttl
            if bornTime < showTime:
                return 1.0 * (bornTime / showTime)
            # Эффект растворения в космосе в конце дистанции 
            return 1.0 if self.ttl > 10 else 1.0 * self.ttl / 10


# Используемое оружие
class PlasmaGun(Gun):
    projectile = PlasmaProjectile

    def __init__(self, owner=None):
        super(PlasmaGun, self).__init__(owner=owner)
