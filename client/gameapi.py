# -*- coding: UTF-8 -*-
import logging

from .settings import LOGGER_NAME, HERO_BAG_URL


class ApiURLS:
    FINISH_PROGRESS_URL = ''
    START_MISSION_URL = ''

    def __init__(self, data):
        self.FINISH_PROGRESS_URL = data['finishProgressOperationLink']
        self.START_MISSION_URL = data['fuseOperationLink']


class APIManager:
    STATUS_SUCCESS = 0
    STATUS_ERROR = 1
    STATUS_ACTION_NOT_AVAILABLE = 2
    STATUS_GAME_ERROR = 3

    def __init__(self):
        self.logger = logging.getLogger(LOGGER_NAME)
        self.urls = None
        self.session = None
        self.started = False

    def start(self, session):
        self.session = session
        self.started = True
        return self.get_game_data()

    def get_game_data(self):
        assert self.started is True
        data = self._get_hero_bag()
        self.urls = ApiURLS(data)
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
        r = self.session.get(HERO_BAG_URL)
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
