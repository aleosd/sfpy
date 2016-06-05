# -*- coding: UTF-8 -*-
import logging

import colorlog


def configure_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    # create formatter
    formatter = colorlog.ColoredFormatter(
        '%(cyan)s%(asctime)s%(reset)s - %(name)s:%(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        log_colors={
            'DEBUG':    'cyan',
            'INFO':     'green',
            'WARNING':  'yellow',
            'ERROR':    'red',
            'CRITICAL': 'red,bg_white',
        },
    )
    # removing milliseconds from logger time
    formatter.default_msec_format = formatter.default_time_format

    # add formatter to ch
    ch.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(ch)
    logger.propagate = False
    return logger
