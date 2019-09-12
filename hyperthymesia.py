from config import load_config
import logging
from logging import config, Handler

settings = load_config('config/settings.yaml')


# Logging, but with more syllables
class Hyperthymesia(object):
    names = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'error': logging.ERROR,
        'warning': logging.WARNING,
        'critical': logging.CRITICAL
    }

    def __init__(self, *arguments, **keywords):
        #logging.config.dictConfig('settings.logging')
        return

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


class ChatHandler(logging.Handler):
        def __init__(self, cx):
                logging.Handler.__init__(self)
                self.cortex = cx

        def emit(self, record):
                self.brain.thalamus.send(record)
