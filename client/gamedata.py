# -*- coding: UTF-8 -*-
import datetime


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

    def is_free(self):
        return not (self._price['currencies'] or self._price['resources'])

    def is_available(self):
        return not self.in_progress

    def get_profession_ids(self):
        return [i['id'] for i in self._professions]


class Follower:
    def __init__(self, **kwargs):
        self.id = kwargs['id']
        self.efficiency = kwargs['efficiency']
        self.in_progress = kwargs['inProgress']
        self.profession = kwargs['profession']

    def is_free(self):
        return not self.in_progress

    @property
    def profession_id(self):
        return self.profession['id']
