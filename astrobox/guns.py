# -*- coding: utf-8 -*-
from robogame_engine import GameObject
from robogame_engine.constants import ROTATE_TURNING
from robogame_engine.theme import theme
from robogame_engine.geometry import Vector, Point, normalise_angle

from astrobox.utils import nearest_angle_distance

# Хранит информацию о цели и имееют свое время жизни для
# для поддержания жизнеспособности Projectile с анимацией
class ProjectileAnimation(object):
    def __init__(self, projectile=None, target=None, distance=None, direction=None, ttl=0):
        self.__projectile = projectile
        self.__target = target
        self.__distance = distance
        self.__direction = direction
        self.__initial_ttl = ttl
        self.__ttl = ttl

    @property
    def zoom(self):
        t = self.__initial_ttl
        return (1.0*self.__ttl/t if self.__ttl>0 else 0.5)
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
            self.__ttl = max(self.__ttl-1, 0)
        else:
            return

        # Были прикреплены к оппоненту, анимируем попадание
        vector = Vector.from_direction(self.__target.direction + self.__direction, module=self.__distance)
        newcoord = Point(self.__target.x + vector.x, self.__target.y + vector.y)
        # Небольшое сглаживание, чтобы небыло телепортаций снаряда
        self.__projectile.coord.x = newcoord.x if abs(self.__projectile.coord.x - newcoord.x) < 2 else (self.__projectile.coord.x + newcoord.x)/2
        self.__projectile.coord.y = newcoord.y if abs(self.__projectile.coord.y - newcoord.y) < 2 else (self.__projectile.coord.y + newcoord.y)/2

        if not self.is_alive:
            self.__projectile.scene.remove_object(self.__projectile)

    
# Projectile описывает поведение полета снаряда.
class Projectile(GameObject):
    coord = None
    rotate_mode = ROTATE_TURNING
    friendly_fire = True
    radius = 1
    selectable = False
    layer = 3

    animation = ProjectileAnimation
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
    def ttl(self):
        return self.__ttl

    @property
    def has_hit(self):
        return self.__attached is not None
    @property
    def attached(self):
        return self.__attached;

    @property
    def zoom(self):
        if self.has_hit:
            return self.__attached.zoom
        return 0.5

    @property
    def is_alive(self):
        return self.__ttl > 0

    def game_step(self):
        if self.has_hit:
            self.__attached.game_step()
            return

        if self.is_alive:
            self.__ttl = max(self.__ttl-1, 0)
            # Обычный цикл полета пока живы
            super(Projectile, self).game_step()
        else:
            # Останавливаемся если отжили цикл полета
            # Используем прямой вызов останова, вместо события
            self.state.stop()
            # Промах, никакой анимации
            #atdist = Vector.from_points(self.coord, self.__initial_coord)
            #print(self.__class__, "::died at distance", atdist.module)
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
        #print(self.__class__.__name__+"::on_born", PlasmaProjectile.max_distance)
        vector = Vector.from_direction(self._owner.direction, module=PlasmaProjectile.max_distance)
        point = self._owner.coord.copy() + vector
        super(Projectile, self).move_at(point, speed=self.__speed)

    def on_overlap_with(self, obj_status):
        # Пролетаем некомандные объекты
        if obj_status.team < 0:
            return
        if Projectile.friendly_fire:
            # Пролетаем свои объекты
            if obj_status.team == self._owner.team:
                return
        else:
            # Не наносим урон себе
            if obj_status == self._owner:
                return
        # За премя жизни ни в кого не попали
        if not obj_status.is_alive or not self.is_alive:
            return
        self.__ttl = 0
        self.stop()
        self.state.stop()
        obj_status.damage_taken(theme.PROJECTILE_DAMAGE)
        self.__attached = self.animation(projectile=self, target=obj_status, distance=int(obj_status.distance_to(self)/2),
                                              direction=nearest_angle_distance(obj_status.direction,
                                                        Vector.from_points(obj_status.coord, self.coord).direction),
                                              ttl=self.__attached_ttl)

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
        if not self.can_shot:
            return
        self._cooldown = theme.PLASMAGUN_COOLDOWN_TIME
        coord = self.owner.coord.copy()
        prtl = self.projectile(coord=coord.copy(), owner=self.owner, direction=self.owner.direction)
        prtl.set_team(self.owner.team)

    def game_step(self):
        # Восстановление после выстрела
        if self._cooldown>0:
            self._cooldown = max(self._cooldown-theme.PLASMAGUN_COOLDOWN_RATE, 0)


# Снаряд используемый снаряд
class PlasmaProjectile(Projectile):
    radius = 15
    max_distance = 580.0
    
    def __init__(self, **kwargs):
        super(PlasmaProjectile, self).__init__(speed=theme.PROJECTILE_SPEED,
                                               ttl=theme.PROJECTILE_TTL,
                                               attached_ttl=int(theme.PROJECTILE_TTL/4), **kwargs)
    @property
    def sprite_filename(self):
        return "plasma_ball_small.png"

    @property
    def zoom(self):
        if self.has_hit:
            # Эффект попадания в цель
            return self.attached.zoom;
        else:
            # Эффект растворения в космосе в конце дистанции 
            return 0.5 if self.ttl > 10 else 0.5*self.ttl/10


# Используемое оружие
class PlasmaGun(Gun):
    projectile = PlasmaProjectile

    def __init__(self, owner=None):
        super(PlasmaGun, self).__init__(owner=owner)

        

