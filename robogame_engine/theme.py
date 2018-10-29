# -*- coding: utf-8 -*-

import re
from importlib import import_module

from robogame_engine.exceptions import RobogameException
from . import constants


class Theme(object):
    mod_path = None
    module = constants

    def set_theme_module(self, mod_path=None):
        self.mod_path = 'default_theme' if mod_path is None else mod_path
        try:
            self.module = import_module(self.mod_path)
            # Due to some constants already defined it should be overriden for access from __getattr__
            test = re.compile(r"^[A-Z][A-Z_]+$")
            for k in dir(constants):
                if test.match(k) is not None and hasattr(self.module, k):
                    self.__dict__['TEAMS_COUNT'] = self.module.__dict__[k]
        except ImportError:
            raise RobogameException("Can't load theme {}".format(self.mod_path))

    def __getattr__(self, item):
        if item not in self.__dict__:
            try:
                value = getattr(self.module, item)
            except AttributeError:
                try:
                    value = getattr(constants, item)
                except AttributeError:
                    import inspect
                    stack = inspect.stack()
                    caller_frame = stack[1]
                    raise AttributeError(
                        "No constant {theme}.{item}\nFile \"{file}\", line {lineno}, in {func}\n\t{code} ".format(
                            item=item,
                            theme=self.mod_path,
                            file=caller_frame[1],
                            lineno=caller_frame[2],
                            func=caller_frame[3],
                            code=caller_frame[4][0].strip()
                        ))
            self.__dict__[item] = value
        return self.__dict__[item]


theme = Theme()
