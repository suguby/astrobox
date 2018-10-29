#!/usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import logging.config


# def _collide_circle(left, right):
#     """
#         Detect collision by radius of objects
#     """
#     return left.distance_to(right) <= left.radius + right.radius
#
#
# def _overlapped(left, right):
#     """
#         Is two objects overlapped
#     """
#     return int((left.radius + right.radius) - left.distance_to(right))


class CanLogging(object):
    __logger = None

    @property
    def logger(self):
        from .theme import theme
        if self.__logger is None:
            logging.config.dictConfig(theme.LOGGING)
            self.__logger = logging.getLogger('robogame')
            if theme.DEBUG:
                self.__logger.setLevel('DEBUG')
            else:
                self.__logger.setLevel(theme.LOGLEVEL)
        return self.__logger

    def debug(self, pattern, *args, **kwargs):
        if self.logger.level <= logging.DEBUG:
            self._log(self.logger.debug, pattern, args, kwargs)

    def info(self, pattern, *args, **kwargs):
        if self.logger.level <= logging.INFO:
            self._log(self.logger.info, pattern, args, kwargs)

    def warning(self, pattern, *args, **kwargs):
        if self.logger.level <= logging.WARNING:
            self._log(self.logger.warning, pattern, args, kwargs)

    def error(self, pattern, *args, **kwargs):
        if self.logger.level <= logging.ERROR:
            self._log(self.logger.error, pattern, args, kwargs)

    def _log(self, log_fun, pattern, args, kwargs):
        kwargs['cls'] = self.__class__.__name__
        kwargs.update(self.__dict__)
        if 'id' in kwargs:
            pattern = '{cls}:{id}: ' + pattern
        else:
            pattern = '{cls}: ' + pattern
        log_fun(pattern.format(*args, **kwargs))
