# -*- coding: UTF-8 -*-
import logging
import time

import requests
from requests.exceptions import RequestException

from .settings import LOGGER_NAME, AUTH_RETRY_DELAY_SECONDS, PAGE, DOMAIN, \
    USERNAME, PASSWORD


SF_PORTAL_URL = 'https://portal.sf.mail.ru/skyforgenews'
AUTH_URL = 'https://auth.mail.ru/cgi-bin/auth'


class Session:
    XHR_HEADERS = {
        'Accept': 'application/json',
        'X-Requested-With': 'XMLHttpRequest',
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
        self.session.post(AUTH_URL, data=auth_data, cookies=self.cookies)

    def get(self, url, **kwargs):
        params = kwargs.get('params', {})
        params.update({'csrf_token': self.csrf_token})
        kwargs['params'] = params
        return self.session.get(url, headers=self.XHR_HEADERS, **kwargs)


if __name__ == '__main__':
    URL = 'https://portal.sf.mail.ru/cult/HeroBag:loadData'

    session = Session()
    session.start()
    r = session.get(URL)
    print(r.json())
