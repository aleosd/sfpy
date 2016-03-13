# -*- coding: UTF-8 -*-
import logging
import time
import sys

import requests
from fake_useragent import UserAgent
from requests.exceptions import RequestException, Timeout

from .settings import LOGGER_NAME, AUTH_RETRY_DELAY_SECONDS, PAGE, DOMAIN, \
    USERNAME, PASSWORD, USER_AGENT, CHECK_URL


SF_PORTAL_URL = 'https://portal.sf.mail.ru/skyforgenews'
AUTH_URL = 'https://auth.mail.ru/cgi-bin/auth'


class Session:
    XHR_HEADERS = {
        'Accept': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
        'Host': 'portal.sf.mail.ru',
        'Referer': 'https://portal.sf.mail.ru/cult/missions',
        'User-Agent': USER_AGENT or UserAgent().random
    }

    def __init__(self):
        self.cookies = {}
        self.logger = logging.getLogger(LOGGER_NAME)
        self.session = requests.Session()

    def start(self):
        success = False
        while not success:
            try:
                self.authenticate()
                success = True
            except RequestException as e:
                self.logger.error(
                    u"Ошибка аутентификации: {}, повторный запрос через {} "
                    u"секунд".format(e, AUTH_RETRY_DELAY_SECONDS))
                time.sleep(AUTH_RETRY_DELAY_SECONDS)

    def reset(self):
        self.cookies = {}
        self.authenticate()

    def get_cookies(self):
        return self.cookies

    @property
    def csrf_token(self):
        return self.cookies['csrf_token']

    def authenticate(self):
        self.logger.info(u"Авторизируемся на сервере mail.ru")
        response = self.session.get(SF_PORTAL_URL)
        for cookie in response.cookies:
            self.cookies[cookie.name] = cookie.value
        self.logger.info(u"Отправляем данные для аутентификации")
        auth_data = {
            'Page': PAGE,
            'Login': USERNAME,
            'Domain': DOMAIN,
            'Password': PASSWORD,
            'saveauth': 0
        }
        r = self.session.post(AUTH_URL, data=auth_data, cookies=self.cookies)
        if 'fail=1' in r.url:
            logging.critical(u"Ошибка аутентификации на сервере")
            sys.exit(1)

    def get(self, url, **kwargs):
        params = kwargs.get('params', {})
        params.update({'csrf_token': self.csrf_token})
        kwargs['params'] = params
        success = False
        while not success:
            try:
                result = self.session.get(
                    url, headers=self.XHR_HEADERS, timeout=10, **kwargs)
                success = True
                return result
            except Timeout as e:
                self.logger.error(
                    u"Ошибка обращение к серверу, время ожидания истекло: "
                    u"{}".format(e))
                time.sleep(30)


    @staticmethod
    def healthchecks_request():
        if CHECK_URL:
            try:
                requests.get(CHECK_URL)
            except RequestException:
                pass
