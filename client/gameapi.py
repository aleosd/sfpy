# -*- coding: UTF-8 -*-
import logging
import time
import sys

from .settings import LOGGER_NAME, HERO_BAG_URL


class ApiURLS:
    def __init__(self):
        self.logger = logging.getLogger(LOGGER_NAME)
        self.FINISH_PROGRESS_URL = ''
        self.START_MISSION_URL = ''
        self._empty = True

    @staticmethod
    def _data_valid(data):
        return ('finishProgressOperationLink' in data and
                'fuseOperationLink' in data)

    def set(self, data):
        if not self._data_valid(data):
            if self._empty:
                self.logger.critical(u"Данные не содержат информации по url")
                sys.exit(1)
            self.logger.warning(u"Данные не содержат информации о ссылках, "
                                u"используем старые")
        else:
            self.FINISH_PROGRESS_URL = data['finishProgressOperationLink']
            self.START_MISSION_URL = data['fuseOperationLink']
            self._empty = False


class APIManager:
    STATUS_SUCCESS = 0
    STATUS_ERROR = 1
    STATUS_ACTION_NOT_AVAILABLE = 2
    STATUS_GAME_ERROR = 3

    def __init__(self):
        self.logger = logging.getLogger(LOGGER_NAME)
        self.urls = ApiURLS()
        self.session = None
        self.started = False

    def start(self, session):
        self.session = session
        self.started = True
        return self.get_game_data()

    def get_game_data(self):
        assert self.started is True
        data = self._get_hero_bag()
        self.urls.set(data)
        return data

    def start_mission(self, mission, followers):
        params = {
            'followerId': [f.id for f in followers],
            'questId': mission.id,
        }
        self.logger.debug(u"Отправляем данные {}".format(params))
        result = self.session.get(self.urls.START_MISSION_URL, params=params)
        return self._process_api_response(result)

    def finish_progress(self, progress):
        u"""
        Завершает указанный прогресс по миссии

        :param progress: Progress obj
        """
        data = {'progressId': progress.id}
        result = self.session.get(self.urls.FINISH_PROGRESS_URL, params=data)
        return self._process_api_response(result)

    def _process_api_response(self, response_data):
        try:
            json_data = response_data.json()
        except ValueError:
            return self.STATUS_ERROR, u"Сервер не вернул корректного JSON"
        if json_data.get('spec'):
            if json_data['spec']['operationResult']['status'] == 'Success':
                return self.STATUS_SUCCESS, json_data['spec']
            else:
                return self.STATUS_GAME_ERROR, json_data['spec']
        return self.STATUS_ERROR, u"Ответ от сервера не содержит данных " \
                                  u"'spec': {}".format(json_data.keys())

    def _get_hero_bag(self):
        self.logger.info(u"Пробуем получить данные HeroBag")
        response_success = False
        while not response_success:
            r = self.session.get(HERO_BAG_URL)
            if r.status_code == 200:
                response_success = True
            else:
                self.logger.error(
                    u"Сервер вернул ответ со статусом {}, "
                    u"повторный запрос через 5 минут".format(r.status_code))
                time.sleep(300)
        try:
            response_json = r.json()
            self.session.healthchecks_request()
            return response_json['spec']
        except ValueError:
            self.logger.error(u"Ошибка обработки запроса HeroBag:"
                              u"\n\tстатус ответа: {}"
                              u"\n\tтекст ответа: {}".format(r.status_code,
                                                             r.text))
            return {}
        except KeyError:
            self.logger.error(u"Ответ не содержит данных heroBag: "
                              u"{}".format(r.json().keys()))
            return {}
