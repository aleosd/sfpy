# -*- coding: UTF-8 -*-
import datetime
import logging

from .settings import LOGGER_NAME
from .gameapi import APIManager


class Progress:
    def __init__(self, **kwargs):
        self.id = kwargs['id']
        self.mission_id = kwargs['fuseData']['missionId']
        self.finished = kwargs['finished']
        self.start_time = self.time_from_ms(kwargs['startTime'])
        self.end_time = self.time_from_ms(kwargs['endTime'])

    @staticmethod
    def time_from_ms(ms):
        return datetime.datetime.fromtimestamp(ms // 1000)

    def is_finished(self):
        return self.finished

    def time_elapsed(self):
        return self.end_time - datetime.datetime.now()

    def time_elapsed_verbose(self):
        eta = self.time_elapsed()
        return "{}:{}:{}".format(
            eta.seconds // 3600,
            (eta.seconds // 60) % 60,
            eta.seconds % 60
        )


class Mission:
    def __init__(self, **kwargs):
        self.id = kwargs['id']
        self.in_progress = kwargs['inProgress']
        self.difficulty = kwargs['difficulty']
        self.duration = kwargs['duration']
        self.experience = kwargs['experience']
        self._price = kwargs['price']
        self._professions = kwargs['professions']
        self.slot_count = kwargs['slotCount']
        self.quality_name = kwargs['missionQualityName']

    def is_free(self):
        return not (self._price['currencies'] or self._price['resources'])

    def is_available(self):
        return not self.in_progress

    def get_profession_ids(self):
        return [i['id'] for i in self._professions]

    def is_mining(self):
        return self.quality_name == u"Добыча ресурсов" and self.is_free()

    def is_battle(self):
        return self.quality_name == u"Боевое задание"

    def is_cult(self):
        return self.quality_name == u"Развитие культа"

    def is_invasion(self):
        return self.quality_name == u"Вторжение"


class Follower:
    def __init__(self, **kwargs):
        self.id = kwargs['id']
        self.efficiency = kwargs['efficiency']
        self.in_progress = kwargs['inProgress']
        self.profession = kwargs['profession']

    def is_available(self):
        return not self.in_progress

    @property
    def profession_id(self):
        return self.profession['id']


class ProgressManager:
    def __init__(self):
        self.progresses = {}
        self.logger = logging.getLogger(LOGGER_NAME)

    def add_progress(self, data):
        p = Progress(**data)
        self.progresses[p.id] = p
        self.logger.debug(u"Добавляем прогресс id {}".format(p.id))
        return p

    def remove_progress(self, progress):
        del self.progresses[progress.id]

    def add_many(self, data, clear=True):
        self.logger.info(u"Добавляем информацию по прогрессам")
        if clear:
            self.clear()
        for progress_data in data:
            self.add_progress(progress_data)

    def clear(self):
        self.progresses = {}

    def get_progress_list(self):
        return self.progresses.values()


class MissionManager:
    def __init__(self):
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

    def mining_missions(self):
        u"""
        Возвращает список с миссиями, доступными для выполнения и не требующими
        ресурсов. Список отсортирован по возрастанию длинтельности миссии и
        количества адептов, необходимых для её выполнения

        :return: List of missions
        """
        missions = [m for m in self.missions.values() if m.is_mining() and
                    m.is_available()]
        return sorted(missions, key=lambda m: (m.duration, m.slot_count))


class FollowerManager:
    def __init__(self):
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
        return {k: f for k, f in self.followers.items() if f.is_available()}

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


class Game:
    def __init__(self):
        self.logger = logging.getLogger(LOGGER_NAME)
        self.progress_manager = ProgressManager()
        self.mission_manager = MissionManager()
        self.follower_manager = FollowerManager()
        self.api = APIManager()
        self.data_has_changed = False

    def start(self, session):
        start_data = self.api.start(session)
        self.update_state(start_data)
        self.process_state()

    def turn(self):
        data = self.api.get_game_data()
        self.update_state(data)
        self.process_state()

    def update_state(self, data):
        self.progress_manager.add_many(data.get('progresses', []))
        self.mission_manager.add_many(data.get('missions', []))
        self.follower_manager.add_many(data.get('followers', []))

    def process_state(self):
        self.process_progresses(self.progress_manager.get_progress_list())
        mining_missions = self.mission_manager.mining_missions()
        if len(mining_missions) > 0:
            self.process_mining_missions(mining_missions)
        if self.data_has_changed:
            self.logger.info(u"Данные изменились, обрабатываем повторно")
            self.data_has_changed = False
            self.process_state()

    def process_progresses(self, progresses):
        u"""
        Проверяет состояние текущих прогресов, если есть завершенные -
        отправляет запрос к API.

        :param progresses: Список прогрессов
        """
        for p in progresses:
            if self.data_has_changed:
                break
            self.logger.info(u"Проверяем состояние прогресса {}".format(p.id))
            if p.is_finished():
                self.logger.info(
                    u"Прогресс {} завершен, отправляем запрос".format(p.id))
                status, result = self.api.finish_progress(p)
                self._handle_call_result(status, result)
            else:
                self.logger.info(u"До окончания прогресса {} еще {}".format(
                    p.id, p.time_elapsed_verbose()))

    def process_mining_missions(self, missions):
        self.logger.info(u"Доступно миссий по добыче ресурсов: {}".format(
            len(missions)))
        for mission in missions:
            if self.data_has_changed:
                break
            status, result = self.process_mining_mission(mission)
            self._handle_call_result(status, result)

    def process_mining_mission(self, mission):
        self.logger.info(u"Пробуем запустить миссию {}".format(mission.id))
        followers = self.follower_manager.free_followers()
        if mission.slot_count > len(followers):
            return self.api.STATUS_ACTION_NOT_AVAILABLE, \
                   u"Недостаточно последователей"

        matched_followers = self.follower_manager.get_for_profession(
            mission.get_profession_ids(), free=True)
        if len(matched_followers) < mission.slot_count:
            additional_followers = self.follower_manager.get_efficient(
                mission.slot_count - len(matched_followers), free=True,
                exclude=matched_followers
            )

            matched_followers = matched_followers + additional_followers
        return self.api.start_mission(mission, matched_followers)

    def _handle_call_result(self, status, result):
        if status == self.api.STATUS_SUCCESS:
            self.logger.info(u"Успешный запрос, сервер вернул \"{}\"".format(
                result['operationResult']['actionFailCause']
            ))
            self.update_state(result['updateData'])
            self.data_has_changed = True
        elif status == self.api.STATUS_ACTION_NOT_AVAILABLE:
            self.logger.info(result)
        elif status == self.api.STATUS_GAME_ERROR:
            self.logger.error(u"Ошибка выполнения запроса: \"{}\"".format(
                result['operationResult']['actionFailCause']
            ))
        else:
            self.logger.critical(result)
