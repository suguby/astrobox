#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

import os

MAX_SPEED = 5
MAX_TURN_SPEED = 10
HEARTBEAT_INTERVAL = 5
MAX_LAYERS = 5

GAME_STEP_MIN_TIME = 0.015

DEBUG = False

ROTATE_TURNING = 'TURNING'
ROTATE_FLIP_VERTICAL = 'FLIP_VERTICAL'
ROTATE_FLIP_HORIZONTAL = 'FLIP_HORIZONTAL'
ROTATE_FLIP_BOTH = 'FLIP_BOTH'
ROTATE_NO_TURN = 'NO_TURN'

BACKGROUND_COLOR = (128, 128, 128)

TEAMS_COUNT = 1

LOGGING = {
    'version': 1,
    # 'disable_existing_loggers': False,
    'formatters': {
        'console': {
            'format': "[%(levelname)s]: %(message)s",
            'datefmt': "%Y-%m-%d %I:%M:%S"
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'console',
        },
    },
    'loggers': {
        'robogame': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    }
}
LOGLEVEL = logging.WARNING

FONT_FILE_NAME = os.path.join(os.path.dirname(__file__), 'fonts', 'TerminusTTF-Bold-4.39.ttf')
