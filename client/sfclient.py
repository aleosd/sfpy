# -*- coding: UTF-8 -*-
import logging
import time
import random

from .settings import LOGGER_NAME, NEXT_REQUEST_DELAY_MINUTES, HERO_BAG_URL
from .auth import Session
from .gameapi import APIManager


class Client:
    def __init__(self):
        self.session = Session()
        self.logger = logging.getLogger(LOGGER_NAME)
        self.manager = None
        self.progresses = None
        self.missions = None

    def run(self):
        self.logger.info(u"Запускается консольный клиент SkyForge")
        self.session.start()
        while True:
            hero_bag_data = self._get_hero_bag()
            if not hero_bag_data:
                time.sleep(60)
                self.logger.info(u"Пробуем переустановить сессию")
                self.session.reset()
            else:
                self.parse_data(hero_bag_data['spec'])
                self.process_state()

                next_request_delay = self._get_next_request_time()
                self.logger.info(u"До следующего запроса {} "
                                 u"секунд".format(next_request_delay))
                time.sleep(next_request_delay)

    def process_state(self):
        self.logger.info(u"Приступаем к обработке состояния")
        self.logger.info(u"Проверяем прогресс по миссиям")
        self.manager.process_game_state()

    def _get_hero_bag(self):
        self.logger.info(u"Пробуем получить данные HeroBag")
        r = self.session.get(HERO_BAG_URL)
        try:
            return r.json()
        except ValueError:
            self.logger.error(u"Ошибка обработки запроса HeroBag:"
                              u"\n\tстатус ответа: {}"
                              u"\n\tтекст ответа: {}".format(r.status_code,
                                                             r.text))
            return {}

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

    def parse_data(self, data):
        if not self.manager:
            self.manager = APIManager(data, session=self.session)
        else:
            self.manager.update_game_data(data)
