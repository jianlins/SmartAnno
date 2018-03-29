import logging
import os
from logging.config import fileConfig

class InitLogger(object):

    @classmethod
    def initLogger(cls):
        config_file = '../conf/logging.ini'
        print(os.path.abspath(config_file))
        if not os.path.isfile(config_file):
            config_file = 'conf/logging.ini'
            print(os.path.abspath(config_file))
        if not os.path.isfile(config_file):
            config_file = 'logging.ini'
            print(os.path.abspath(config_file))
        if not os.path.isfile(config_file):
            print('write', os.path.abspath(config_file))
#             with open(config_file, 'w') as f:
#                 f.write('''[loggers]
# keys=root
# [handlers]
# keys=consoleHandler
# [formatters]
# keys=simpleFormatter
# [logger_root]
# level=WARNING
# handlers=consoleHandler
# [handler_consoleHandler]
# class=StreamHandler
# level=WARNING
# formatter=simpleFormatter
# args=(sys.stdout,)
# [formatter_simpleFormatter]
# format=%(asctime)s - %(name)s - %(levelname)s - %(message)s
# datefmt=
#         ''')
        fileConfig(config_file)
        logging.getLogger().setLevel(logging.DEBUG)
