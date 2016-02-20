# -*- coding: UTF-8 -*-
import logging

from .gamedata import Progress, Mission, Follower
from .settings import LOGGER_NAME


STATUS_SUCCESS = 0
STATUS_ERROR = 1
STATUS_ACTION_NOT_AVAILABLE = 2


class ApiURLS:
    FINISH_PROGRESS_URL = ''
    START_MISSION_URL = ''

    def __init__(self, data):
        self.FINISH_PROGRESS_URL = data['finishProgressOperationLink']
        self.START_MISSION_URL = data['fuseOperationLink']


class ProgressManager:
    def __init__(self, urls, session):
        self.urls = urls
        self.session = session
        self.progresses = {}
        self.logger = logging.getLogger(LOGGER_NAME)

    def add_progress(self, data):
        p = Progress(**data)
        self.progresses[p.id] = p
        self.logger.debug(u"Добавляем прогресс id {}".format(p.id))
        return p

    def add_many(self, data, clear=True):
        self.logger.info(u"Добавляем информацию по прогрессам")
        if clear:
            self.clear()
        for progress_data in data:
            self.add_progress(progress_data)

    def clear(self):
        self.progresses = {}

    def process(self):
        u"""
        Проверяет состояние текущих прогресов, если есть завершенные -
        отправляет запрос к API.
        """
        finished = []
        for pid, progress in self.progresses.items():
            self.logger.info(u"Проверяем состояние прогресса {}".format(pid))
            if progress.is_finished():
                self.logger.info(
                    u"Прогресс {} завершен, отправляем запрос".format(pid))
                self.finish_progress(progress)
                finished.append(progress.id)
            else:
                self.logger.info(u"До окончания прогресса {} еще {}".format(
                    pid, progress.time_elapsed_verbose()))
        # если были завершенные задачи - удаляем их из списка
        for finished_id in finished:
            del self.progresses[finished_id]

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


class MissionManager:
    def __init__(self, urls, session):
        self.urls = urls
        self.session = session
        self.missions = {}
        self.logger = logging.getLogger(LOGGER_NAME)

    def add_mission(self, data):
        mission = Mission(**data)
        self.missions[mission.id] = mission
        self.logger.debug(u"Добавляем миссию id {}".format(mission.id))

    def add_many(self, data, clear=True):
        if clear:
            self.clear()
        self.logger.info(u"Добавляем миссии: {}".format(len(data)))
        for mission_data in data:
            self.add_mission(mission_data)

    def clear(self):
        self.missions = {}

    def free_missions(self):
        u"""
        Возвращает список с миссиями, доступными для выполнения и не требующими
        ресурсов. Список отсортирован по возрастанию длинтельности миссии и
        количества адептов, необходимых для её выполнения

        :return: List of missions
        """
        missions = [m for m in self.missions.values() if m.is_free() and
                    m.is_available()]
        return sorted(missions, key=lambda m: (m.duration, m.slot_count))


class FollowerManager:
    def __init__(self, urls, session):
        self.urls = urls
        self.session = session
        self.followers = {}
        self.logger = logging.getLogger(LOGGER_NAME)

    def add_follower(self, data):
        follower = Follower(**data)
        self.followers[follower.id] = follower

    def add_many(self, data, clear=True):
        if data and clear:
            self.clear()
        for follower in data:
            self.add_follower(follower)

    def clear(self):
        self.followers = {}

    def free_followers(self):
        return {k: f for k, f in self.followers.items() if f.is_free()}

    def get_for_profession(self, profession, free=False):
        u"""
        Возвращает список сотрудников с определенной профессией
        :param free: Bool, учитывать только не занятых адептов
        :param profession: int, profession id
        :return: list
        """
        if free:
            followers = self.free_followers().values()
        else:
            followers = self.followers.values()
        if isinstance(profession, (list, tuple)):
            return [f for f in followers if f.profession_id in profession]
        if isinstance(profession, int):
            return [f for f in followers if f.profession_id == profession]
        raise ValueError(u"Profession must be an int or list or tuple")

    def get_efficient(self, count=-1, free=False, exclude=None):
        u"""
        Возвращает отсортированный по эффективности список адептов.
        При помощи count можно указать ограничение на количество возвращаемых
        значений.
        :param free: Bool, учитывать только не занятых адептов
        :param count: int
        :param exclude: followers list to exclude from result
        :return: list
        """
        if free:
            followers = self.free_followers().values()
        else:
            followers = self.followers.values()

        if exclude:
            followers = [f for f in followers if f not in exclude]
        fs = sorted(followers, key=lambda k: k.efficiency, reverse=True)
        return fs[0:count]


class APIManager:
    def __init__(self, data, session):
        self.urls = ApiURLS(data)
        self.session = session
        self.logger = logging.getLogger(LOGGER_NAME)
        self.progress_manager = ProgressManager(self.urls, self.session)
        self.mission_manager = MissionManager(self.urls, self.session)
        self.follower_manager = FollowerManager(self.urls, self.session)
        self.update_game_data(data)

    def _handle_call_result(self, status, result):
        if status == STATUS_SUCCESS:
            self.logger.info(u"Успешный запрос, сервер вернул \"{}\"".format(
                result['operationResult']['actionFailCause']
            ))
            self.update_game_data(result['updateData'])
            self.process_game_state()
        elif status == STATUS_ACTION_NOT_AVAILABLE:
            self.logger.info(result)
        else:
            self.logger.error(u"Ошибка выполнения запроса: \"{}\"".format(
                result['operationResult']['actionFailCause']
            ))

    def update_game_data(self, data):
        self.progress_manager.add_many(data.get('progresses', []))
        self.mission_manager.add_many(data.get('missions', []))
        self.follower_manager.add_many(data.get('followers', []))

    def process_game_state(self):
        self.progress_manager.process()
        free_missions = self.mission_manager.free_missions()
        if len(free_missions) > 0:
            self.process_free_missions(free_missions)

    def process_free_missions(self, missions):
        self.logger.info(u"Доступно бесплатных миссий: {}".format(
            len(missions)))
        for mission in missions:
            self._handle_call_result(self.process_free_mission(mission))

    def process_free_mission(self, mission):
        self.logger.info(u"Проверяем доступность миссии {}".format(mission.id))
        followers = self.follower_manager.free_followers()
        if mission.slot_count > len(followers):
            return STATUS_ACTION_NOT_AVAILABLE, u"Недостаточно последователей"

        matched_followers = self.follower_manager.get_for_profession(
            mission.get_profession_ids(), free=True)
        if len(matched_followers) < mission.slot_count:
            additional_followers = self.follower_manager.get_efficient(
                mission.slot_count - len(matched_followers), free=True,
                exclude=matched_followers
            )

            matched_followers = matched_followers + additional_followers

        params = {
            'followerId': [f.id for f in matched_followers],
            'questId': mission.id,
        }
        self.logger.debug(u"Отправляем данные {}".format(params))
        result = self.session.get(self.urls.START_MISSION_URL, params=params)
        json_data = result.json()
        if json_data.get('spec'):
            if json_data['spec']['operationResult']['status'] == 'Success':
                return STATUS_SUCCESS, json_data['spec']
            else:
                return STATUS_ERROR, json_data['spec']
        return STATUS_ERROR, u"Ответ от сервера: {}".format(result.text)
