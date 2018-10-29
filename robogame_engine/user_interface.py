#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

from collections import defaultdict
import os
import random
import pygame
from pygame.locals import *
from pygame.sprite import DirtySprite

from pygame.font import Font
from pygame.transform import flip
from pygame.draw import line, circle, rect, aalines
from pygame.display import set_caption, set_mode
from pygame.time import Clock

from .constants import (
    ROTATE_NO_TURN, ROTATE_TURNING, ROTATE_FLIP_VERTICAL, ROTATE_FLIP_HORIZONTAL, ROTATE_FLIP_BOTH)
from .geometry import Point
from .utils import CanLogging
from .theme import theme


class RoboSprite(DirtySprite, CanLogging):
    """
        Show sprites on screen
    """

    def __init__(self, id, status):
        """
            Link object with its sprite
        """
        self.__images_cash = defaultdict(dict)
        self.id = id
        self.status = status

        layer = int(self.status.layer)
        if layer > theme.MAX_LAYERS:
            layer = theme.MAX_LAYERS
        if layer < 0:
            layer = 0
        super(RoboSprite, self).__init__(UserInterface.sprites_all, UserInterface.sprites_by_layer[layer])

        self.image = self.images[0].copy()
        self.rect = self.image.get_rect()
        self._debug_color = (
            random.randint(200, 255),
            random.randint(50, 255),
            0
        )
        self._id_font = Font(theme.FONT_FILE_NAME, 20)
        self._selected = False
        # for animated sprites
        self._animcycle = 3
        self._drawed_count = 0

    def update_status(self, status):
        self.status = status

    def __str__(self):
        return 'sprite({}: rect={} layer={})'.format(self.id, self.rect, self._layer)

    def __repr__(self):
        return str(self)

    @property
    def images(self):
        sprite_filename = self.status.sprite_filename
        if 0 in self.__images_cash[sprite_filename]:
            image = self.__images_cash[sprite_filename][0]
        else:
            image = load_image(name=sprite_filename, colorkey=-1)
            self.__images_cash[sprite_filename][0] = image
        return [image, flip(image, 1, 0), flip(image, 0, 1), flip(image, 1, 1)]

    @property
    def font(self):
        if not hasattr(self, '_font'):
            self._font = pygame.font.Font(theme.FONT_FILE_NAME, self.counter_attrs['size'])
        return self._font

    @property
    def counter_attrs(self):
        try:
            return self.status.counter_attrs
        except AttributeError:
            return dict(size=27, position=(30, 30), color=(128, 128, 128))

    def _show_meters(self):
        if hasattr(self.status, 'meter_1') and self.status.meter_1 > 0:
            if self.status.meter_1 > 1:
                self.warning("meter_1 {meter} must be expressed as a decimal", meter=self.status.meter_1)
                self.status.meter_1 = 1
            bar_px = int(self.status.meter_1 * self.rect.width)
            line(self.image, theme.METER_1_COLOR, (0, 3), (bar_px, 3), 2)
        if hasattr(self.status, 'meter_2') and self.status.meter_2 > 0:
            if self.status.meter_2 > 1:
                self.warning("meter_2 {meter} must be expressed as a decimal", meter=self.status.meter_2)
                self.status.meter_2 = 1
            bar_px = int(self.status.meter_2 * self.rect.width)
            line(self.image, theme.METER_2_COLOR, (0, 5), (bar_px, 5), 2)
        if hasattr(self.status, 'counter') and self.status.counter is not None:
            txt = "{}".format(self.status.counter)
            txt_image = self.font.render(txt, 1, self.counter_attrs['color'])
            self.image.blit(txt_image, self.counter_attrs['position'])

    def _show_selected(self):
        if self._selected:
            outline_rect = pygame.Rect(0, 0, self.rect.width, self.rect.height)
            rect(self.image, self._debug_color, outline_rect, 1)

    def _show_id(self):
        if hasattr(self.status, 'id'):
            id_image = self._id_font.render(
                str(self.status.id),
                0,
                self._debug_color)
            self.image.blit(id_image, (5, 5))

    def _show_detection(self):
        if hasattr(self.status, 'detected_by'):
            radius = 0
            for obj in self.status.detected_by:
                if obj.selected:
                    radius += 6
                    pos = (self.rect.width // 2, self.rect.height // 2)
                    circle(self.image, obj._debug_color, pos, radius, 3)

    def update(self):
        """
            Internal function for refreshing internal variables.
            Do not call in your code!
        """
        rotate_mode = self.status.rotate_mode
        if rotate_mode != ROTATE_NO_TURN:
            if rotate_mode == ROTATE_TURNING:
                self.image = self._rotate_image()
            elif rotate_mode == ROTATE_FLIP_VERTICAL:
                if 90 <= self.status.direction <= 270:
                    self.image = self.images[1].copy()
                else:
                    self.image = self.images[0].copy()
            elif rotate_mode == ROTATE_FLIP_HORIZONTAL:
                if self.status.direction > 180:
                    self.image = self.images[2].copy()
                else:
                    self.image = self.images[0].copy()
            elif rotate_mode == ROTATE_FLIP_BOTH:
                if 90 <= self.status.direction <= 180:
                    self.image = self.images[1].copy()
                elif 180 < self.status.direction <= 270:
                    self.image = self.images[2].copy()
                elif 270 < self.status.direction < 360:
                    self.image = self.images[3].copy()
                else:
                    self.image = self.images[0].copy()
            else:
                self.image = self.images[0].copy()
        elif self.status.animated:
            # TODO брать таки кадры из гифок
            self._drawed_count += 1
            self.image = self.images[self._drawed_count // self._animcycle % 4]
        else:
            self.image = self.images[0].copy()

        self.rect = self.image.get_rect()
        self.rect.center = Point(self.status.x, self.status.y).to_screen()

        self._show_meters()
        self._show_selected()
        if hasattr(self.status, 'debug') and self.status.debug:
            self._show_id()
            self._show_detection()

    def _rotate_image(self):
        angle = int(self.status.direction)
        zoom = float(getattr(self.status, 'zoom', 1))
        image = self.images[0]
        rot_image = pygame.transform.rotozoom(image, angle, zoom)
        return rot_image.copy()


class UserInput:
    """
        Key pressing and mouse select
    """
    def __init__(self):
        self.one_step = False
        self.switch_debug = False
        self.the_end = False
        self.selected_ids = []

        self.mouse_pos = None
        self.mouse_buttons = None

    def __eq__(self, other):
        return not self.__ne__(other)

    def __ne__(self, other):
        return (self.one_step != other.one_step or
                self.switch_debug != other.switch_debug or
                self.the_end != other.the_end or
                self.selected_ids != other.selected_ids)


class UserInterface(CanLogging):
    """
        Show sprites and get feedback from user
    """
    _max_fps = 50  # ограничиваем для стабильности отклика клавы/мыши
    sprites_by_layer = []
    sprites_all = []

    def __init__(self, name, current_theme):
        """
            Make game window
        """
        theme.set_theme_module(current_theme)

        UserInterface.sprites_all = pygame.sprite.LayeredUpdates()
        UserInterface.sprites_by_layer = [pygame.sprite.LayeredUpdates(layer=i) for i in range(theme.MAX_LAYERS + 1)]

        pygame.init()

        screenrect = Rect((0, 0),
                          (theme.FIELD_WIDTH, theme.FIELD_HEIGHT))
        self.screen = set_mode(screenrect.size)
        set_caption(name)

        self.background = pygame.Surface(self.screen.get_size())  # и ее размер
        self.background = self.background.convert()
        try:
            image = load_image(theme.BACKGROUND_IMAGE, -1)
            self.background.blit(image, (0, 0))
        except (SystemExit, AttributeError):
            self.background.fill(theme.BACKGROUND_COLOR)  # заполняем цветом
        self.clear_screen()

        global clock
        clock = Clock()

        self.fps_meter = Fps(color=(255, 255, 0))

        self._step = 0
        self.debug = False

        self.game_objects = {}
        self.ui_state = UserInput()

        self._debug = False
        self.child_conn = None

    def run(self, child_conn):
        self.child_conn = child_conn
        while True:
            try:
                objects_state = self._get_states()
                if objects_state:
                    # были получены данные - обновляемся
                    try:
                        self.update_state(objects_state)
                    except Exception as exc:
                        self.logger.error('UI update_state: {}'.format(exc))

                # проверяем - изменилось ли что-то у пользователя
                if self.ui_state_changed() or self.ui_state.one_step:
                    # изменилось - отсылаем состояние в трубу
                    self.child_conn.send(self.ui_state)
                    # пользователь захотел закончить - выходим
                    if self.ui_state.the_end:
                        break
                # отрисовываемся
                try:
                    self.draw()
                except Exception as exc:
                    self.logger.error('UI draw: {}'.format(exc))
            except Exception as exc:
                self.logger.error('UI: {}'.format(exc))
        # очистка
        for group in self.sprites_by_layer:
            for sprite in group:
                sprite.kill()
        pygame.quit()

    def _get_states(self):
        # проверяем есть ли данные на том конце трубы
        while self.child_conn.poll(0):
            # данные есть - считываем все что есть
            return self.child_conn.recv()

    def update_state(self, objects_status):
        """
            renew game objects states, create/delete sprites if need
        """
        new_ids = set(objects_status)
        old_ids = set(self.game_objects)
        new_game_objects = {}

        to_delete = old_ids - new_ids
        for obj_id in to_delete:
            # старые объекты - убиваем спрайты
            sprite = self.game_objects[obj_id]
            sprite.kill()
        self.info('deleted {count} objs', count=len(to_delete))

        to_create = new_ids - old_ids
        for obj_id in to_create:
            # новые объекты - создаем спрайты
            sprite = RoboSprite(id=obj_id, status=objects_status[obj_id])
            new_game_objects[obj_id] = sprite
        self.info('created {count} objs', count=len(to_create))

        to_update = old_ids & new_ids
        for obj_id in to_update:
            # существующие объекты - обновляем состояния
            sprite = self.game_objects[obj_id]
            status = objects_status[obj_id]
            sprite.update_status(status)
            new_game_objects[obj_id] = sprite
        self.info('updated {count} objs', count=len(to_update))

        self.game_objects = new_game_objects

    def ui_state_changed(self):
        """
            check UI state - if changed it will return UI state
        """
        prev_ui_state = self.ui_state
        self.ui_state = UserInput()

        for event in pygame.event.get():
            if event.type == KEYDOWN and event.key == K_f:
                self.fps_meter.show = not self.fps_meter.show

            if ((event.type == QUIT) or
                    (event.type == KEYDOWN and event.key == K_ESCAPE) or
                    (event.type == KEYDOWN and event.key == K_q)):
                self.ui_state.the_end = True
            if event.type == KEYDOWN and event.key == K_d:
                self.ui_state.switch_debug = True
            if event.type == KEYDOWN and event.key == K_s:
                self.ui_state.one_step = True
        key = pygame.key.get_pressed()
        if key[pygame.K_g]:  # если нажата и удерживается
            self.ui_state.one_step = True
        pygame.event.pump()

        self._select_objects()

        if self.ui_state.switch_debug:
            if self._debug:
                # были в режиме отладки
                self.clear_screen()
            # переключаем и тут тоже - потому что отдельный процесс
            self._debug = not self._debug

        return self.ui_state != prev_ui_state

    def _select_objects(self):
        """
            selecting objects with mouse
        """
        self.ui_state.mouse_pos = pygame.mouse.get_pos()
        self.ui_state.mouse_buttons = pygame.mouse.get_pressed()

        if self.ui_state.mouse_buttons[0] and not self.mouse_buttons[0]:
            # mouse down
            for obj_id, obj in self.game_objects.items():
                if obj.status.selectable and \
                   obj.rect.collidepoint(self.ui_state.mouse_pos):
                    # координаты экранные
                    obj._selected = not obj._selected
                elif not self._debug:
                    # возможно выделение множества танков
                    # только на режиме отладки
                    obj._selected = False
        self.mouse_buttons = self.ui_state.mouse_buttons
        self.ui_state.selected_ids = [
            _id for _id in self.game_objects
            if self.game_objects[_id]._selected
        ]

    def clear_screen(self):
        self.screen.blit(self.background, (0, 0))
        pygame.display.flip()

    def _draw_radar_outline(self, obj):
        from math import pi, cos, sin

        angle = theme.tank_radar_angle
        angle_r = (obj.status.direction - angle // 2) / 180.0 * pi
        angle_l = (obj.status.direction + angle // 2) / 180.0 * pi
        radar_range = theme.tank_radar_range
        points = [
            Point(obj.status.x + cos(angle_r) * radar_range,
                  obj.status.y + sin(angle_r) * radar_range),
            Point(obj.status.x + cos(angle_l) * radar_range,
                  obj.status.y + sin(angle_l) * radar_range),
            Point(obj.status.x,
                  obj.status.y)
        ]
        points = [x.to_screen() for x in points]
        aalines(self.screen, obj._debug_color, True, points)

    def draw(self):
        """
            Drawing sprites on screen
        """

        # update all the sprites
        for group in self.sprites_by_layer:
            try:
                group.update()
            except Exception as exc:
                self.logger.exception('UI group.update: {}'.format(exc))

        # draw the scene
        # if self._debug:
        if True:  # TODO разобраться с частичным обновлением
            self.screen.blit(self.background, (0, 0))
            for group in self.sprites_by_layer:
                try:
                    group.draw(self.screen)
                except Exception as exc:
                    self.logger.error('UI group.draw: {}'.format(exc))
            # for obj in self.all:
            #     if hasattr(obj, 'status') and \
            #        hasattr(obj.status, 'gun_heat') and \
            #        obj._selected:
            #         self._draw_radar_outline(obj)
            pygame.display.flip()
        else:
            # clear/erase the last drawn sprites
            for group in self.sprites_by_layer:
                group.clear(self.screen, self.background)
                dirty = group.draw(self.screen)
                pygame.display.update(dirty)
            # self.sprites_all.clear(self.screen, self.background)
            # dirty = self.sprites_all.draw(self.screen)
            # pygame.display.update(dirty)

        # cap the framerate
        clock.tick(self._max_fps)
        return True


class Fps(DirtySprite):
    """
        Show game FPS
    """
    _layer = 5

    def __init__(self, color=(255, 255, 255)):
        """
                Make indicator
            """
        super(Fps, self).__init__(UserInterface.sprites_by_layer[0])
        self.show = False
        self.font = pygame.font.Font(theme.FONT_FILE_NAME, 20)
        self.color = color
        self.image = self.font.render('-', 0, self.color)
        self.rect = self.image.get_rect()
        self.rect = self.rect.move(theme.FIELD_WIDTH - 100, 10)
        self.fps = []

    def update(self):
        """
            Refresh indicator
        """
        global clock
        current_fps = clock.get_fps()
        del self.fps[100:]
        self.fps.append(current_fps)
        if self.show:
            fps = sum(self.fps) / len(self.fps)
            msg = '{:5.0f} FPS'.format(fps)
        else:
            msg = ''
        self.image = self.font.render(msg, 1, self.color)


def load_image(name, colorkey=None):
    """
        Load image from file
    """
    fullname = os.path.join(theme.PICTURES_PATH, name)
    try:
        image = pygame.image.load(fullname)
    except pygame.error as exc:
        print("Cannot load image:", fullname)
        raise SystemExit(exc)
        #image = image.convert()
    if colorkey is not None:
        if colorkey is -1:
            colorkey = image.get_at((0, 0))
        image.set_colorkey(colorkey, RLEACCEL)
    return image
