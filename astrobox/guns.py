
from robogame_engine import GameObject
from robogame_engine.constants import ROTATE_TURNING
from robogame_engine.theme import theme
from robogame_engine.geometry import Vector, Point, normalise_angle

from astrobox.strategies import nearest_angle_distance
        

class Gun:
    def __init__(self, owner):
        self._owner = owner

    @property
    def owner(self):
        return self._owner

    @property
    def can_shot(self):
        return False

    def shot(self):
        pass

class PlasmaProjectile(GameObject):
    coord = None
    rotate_mode = ROTATE_TURNING
    radius = 15
    selectable = False
    layer = 3
    _max_distance = 580.0
    
    def __init__(self, owner=None, **kwargs):
        super(PlasmaProjectile, self).__init__(**kwargs)
        self.__initial_coord = owner.coord.copy()
        self._owner = owner
        self.__ttl = theme.PROJECTILE_TTL
        self.__attached_to = None
        self.__attached_distance = None
        self.__attached_direction = None
        self.__ttl_attached = 0

    @property
    def sprite_filename(self):
        return "plasma_ball_small.png"

    @property
    def zoom(self):
        t = int(theme.PROJECTILE_TTL/4)
        if self.__attached_to is not None:
            return (1.0*self.__ttl_attached/t if self.__ttl_attached>0 else 0.5)
        else:
            if self.__ttl > 10:
                return 0.5
            else:
                return 0.5*self.__ttl/10

    @property
    def is_alive(self):
        return self.__ttl > 0

    def game_step(self):
        if self.is_alive:
            self.__ttl = max(self.__ttl-1, 0)
        if self.__ttl_attached > 0:
            self.__ttl_attached = max(self.__ttl_attached-1, 0)

        # Останавливаемся если отжили цикл полета
        if not self.is_alive:
            self.stop()
            # Используем прямой вызов останова, вместе с событием
            self.state.stop()
        if self.is_alive:
            #print(self.__class__.__name__+"::game_step", "state", self.state.__class__.__name__, self.__ttl, theme.PROJECTILE_TTL*theme.PROJECTILE_SPEED)
            pass

        # ни в кого не попали еще
        if self.__attached_to is None:
            if self.__ttl == 0:
                # Промах, никакой анимации
                atdist = Vector.from_points(self.coord, self.__initial_coord)
                #print(self.__class__, "::died at distance", atdist.module)
                self.scene.remove_object(self)
            else:
                # Обычный цикл полета пока живы
                super(PlasmaProjectile, self).game_step()
            return

        # Были прикреплены к оппоненту, анимируем
        vector = Vector.from_direction(self.__attached_to.direction + self.__attached_direction, module=self.__attached_distance)
        newcoord = Point(self.__attached_to.x + vector.x, self.__attached_to.y + vector.y)
        # Небольшое сглаживание, чтобы небыло телепортаций снаряда
        self.coord.x = newcoord.x if abs(self.coord.x - newcoord.x) < 2 else (self.coord.x + newcoord.x)/2
        self.coord.y = newcoord.y if abs(self.coord.y - newcoord.y) < 2 else (self.coord.y + newcoord.y)/2

        if not self.is_alive and self.__ttl_attached <= 0:
            #print(self.__class__.__name__+"::die", "attached", self.state.__class__.__name__,
            #      self.__attached_to, theme.PROJECTILE_TTL*theme.PROJECTILE_SPEED)
            self.scene.remove_object(self)
            return


    def turn_to(self, target, speed=None):
        # Снаряд не управляемый
        pass

    def move_at(self, target, speed=None):
        # Двигаемся только по прямой, незачем иметь возможность изменять маршрут
        pass

    def on_born(self):
        print(self.__class__.__name__+"::on_born", PlasmaProjectile._max_distance)
        vector = Vector.from_direction(self._owner.direction, module=PlasmaProjectile._max_distance)
        point = self._owner.coord.copy() + vector
        super(PlasmaProjectile, self).move_at(point, speed=theme.PROJECTILE_SPEED)

    def on_stop(self):
        #print(self._owner.__class__.__name__, self.__class__.__name__, "on_stop")
        pass

    def on_collide_detected_with(self, obj_status):
        # Пролетаем свои и некомандные объекты
        if obj_status.team < 0 or obj_status.team == self._owner.team:
            return
        # За премя жизни ни в кого не попали
        if not obj_status.is_alive or not self.is_alive:
            return
        self.__ttl = 0
        self.__ttl_attached = int(theme.PROJECTILE_TTL/4)
        self.__attached_distance = int(obj_status.distance_to(self)/2)
        self.__attached_direction = nearest_angle_distance(obj_status.direction, Vector.from_points(obj_status.coord, self.coord).direction)
        self.__attached_to = obj_status
        self.stop()
        self.state.stop()
        obj_status.damage_taken(theme.PROJECTILE_DAMAGE)
        print(self._owner.__class__.__name__, self.__class__.__name__, "on_collide_with",
                self._owner.team, obj_status.team,
                self.__attached_to, self.__attached_distance, self.__attached_direction)
        pass

class PlasmaGun(Gun):
    _projectile = PlasmaProjectile

    def __init__(self, owner=None):
        super(PlasmaGun, self).__init__(owner=owner)
        self._cooldown = 0

    @property
    def shot_distance(self):
        return PlasmaGun._projectile._max_distance

    def can_shot(self):
        return self._cooldown <= 0

    def shot(self, target):
        if self._cooldown > 0:
            return
        self._cooldown = theme.PLASMAGUN_COOLDOWN_TIME
        coord = self.owner.coord.copy()
        prtl = self._projectile(coord=coord.copy(), owner=self.owner, direction=self.owner.direction)
        prtl.set_team(self.owner.team)

    def game_step(self):
        if self._cooldown>0:
            self._cooldown = max(self._cooldown-theme.PLASMAGUN_COOLDOWN_RATE, 0)

        

