from config import load_config
import logging
import logging.config

settings = load_config('config/settings.yaml')

class Hyperthymesia(object):
    names = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'error': logging.ERROR,
        'warning': logging.WARNING,
        'critical': logging.CRITICAL
    }

    def __init__(self, *arguments, **keywords):

        logging.config.dictConfig(settings.logging)

	self.__set_log_level('debug')

    def __set_log_level(self, level):

        self.logger = logging.getLogger(level)

        try:
            level = self.names[level.lower()]
        except KeyError:
            level = logging.WARNING

        self.logger.setLevel(level)

    def info(self, message):

        self.__set_log_level('info')
        self.logger.info(message)

    def debug(self, message):

        self.__set_log_level('debug')
        self.logger.debug(message)

    def warn(self, message):

        self.__set_log_level('warn')
        self.logger.warn(message, exc_info=True)


