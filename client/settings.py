# -*- coding: UTF-8 -*-
import configparser
import os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir)
CONFIG_FILE = 'sfpy.conf'


def get_config():
    conf = configparser.ConfigParser()
    conf.read(os.path.join(ROOT, CONFIG_FILE))
    return conf

config = get_config()

PAGE = config.get('Auth', 'Page')
USERNAME = config.get('Auth', 'Login')
DOMAIN = config.get('Auth', 'Domain')
PASSWORD = config.get('Auth', 'Password')
USER_AGENT = config.get('Auth', 'UserAgent', fallback=None)

LOGGER_NAME = 'sf-logger'

NEXT_REQUEST_DELAY_MINUTES = 6
AUTH_RETRY_DELAY_SECONDS = 60

HERO_BAG_URL = 'https://portal.sf.mail.ru/cult/HeroBag:loadData'


if not all([USERNAME, DOMAIN, PASSWORD, PAGE]):
    raise RuntimeError(u"Не указаны данные для подключения")
