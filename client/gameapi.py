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
        json_data = result.json()
        if json_data.get('spec'):
            if json_data['spec']['operationResult']['status'] == 'Success':
                return self.STATUS_SUCCESS, json_data['spec']
            else:
                return self.STATUS_ERROR, json_data['spec']
        return self.STATUS_ERROR, u"Ответ от сервера: {}".format(result.text)

    def finish_progress(self, progress):
        u"""
        Завершает указанный прогресс по миссии

        :param progress: Progress obj
        """
        if not progress.is_finished():
            self.logger.warning(u"Нельзя завершить незаконченное задание!")
        else:
            data = {'progressId': progress.id}
            r = self.session.get(self.urls.FINISH_PROGRESS_URL, params=data)
            if r.status_code == 200:
                self.logger.info(u"Успешно подтвердили завершение миссии")
            else:
                self.logger.warning(u"Запрос на завершение миссии вернул "
                                    u"статус код {}".format(r.status_code))

    def _get_hero_bag(self):
        self.logger.info(u"Пробуем получить данные HeroBag")
        r = self.session.get(HERO_BAG_URL)
        try:
            response_json = r.json()
            return response_json['spec']
        except ValueError:
            self.logger.error(u"Ошибка обработки запроса HeroBag:"
                              u"\n\tстатус ответа: {}"
                              u"\n\tтекст ответа: {}".format(r.status_code,
                                                             r.text))
        except KeyError:
            self.logger.error(u"Ответ не содержит данных heroBag: "
                              u"{}".format(r.json().keys()))
        finally:
            return {}
