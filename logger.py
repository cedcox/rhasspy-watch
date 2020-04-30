# coding: utf8

import sys
import logging
from logging.handlers import SysLogHandler
import colorlog

LOG_COLORS = {'DEBUG':    'cyan',
              'INFO':     'green',
              'WARNING':  'yellow',
              'ERROR':    'red',
              'CRITICAL': 'bold_red'}


def get_logger(name, verbose):
    """Return a Logger object with the right level, formatter and handler."""

    handler = colorlog.StreamHandler(stream=sys.stdout)
    formatter = colorlog.ColoredFormatter('[%(asctime)s] %(log_color)s %(message)s',datefmt='%Y-%m-%d %H:%M:%S',
                                            log_colors=LOG_COLORS)
    logger = colorlog.getLogger(name)

    if verbose:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    logging.basicConfig(filename='rhasspy.log')

    return logger