# -*- coding: UTF-8 -*-
import logging
import time
import random

from .settings import LOGGER_NAME, NEXT_REQUEST_DELAY_MINUTES
from .auth import Session
from .gamedata import Game


class Client:
    def __init__(self):
        self.session = Session()
        self.logger = logging.getLogger(LOGGER_NAME)
        self.game = Game()

    def run(self):
        self.logger.info(u"Запускается консольный клиент SkyForge")
        self.session.start()
        self.game.start(self.session)
        while True:
            next_request_delay = self._get_next_request_time()
            self.logger.info(u"До следующего запроса {} "
                             u"секунд".format(next_request_delay))
            time.sleep(next_request_delay)
            self.game.turn()

    @staticmethod
    def _get_next_request_time():
        u"""
        Вычисляет время до следующего запроса. Выбирается случайное число в
        диапазоне +- 25% от заданного в настройках

        :return: seconds, int
        """
        seconds = NEXT_REQUEST_DELAY_MINUTES * 60
        delay_range_start = seconds - int(seconds * 0.25)
        delay_range_end = seconds + int(seconds * 0.25)
        return random.randint(delay_range_start, delay_range_end)
