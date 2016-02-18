#!/usr/bin/env python
# -*- coding: UTF-8 -*-
from client import sfclient, settings, logger


if __name__ == '__main__':
    log = logger.configure_logger(settings.LOGGER_NAME)

    client = sfclient.Client()
    try:
        client.run()
    except KeyboardInterrupt:
        log.info(u"Завершение работы клиента")
