import logging
import logging.config
import os
from colorama import Fore
def logMsg(msg):
    if logging.getLogger().isEnabledFor(logging.DEBUG):
        os.write(1, str.encode(Fore.LIGHTBLUE_EX + msg.__repr__() + '\n'))


def logError(msg):
    if logging.getLogger().isEnabledFor(logging.DEBUG):
        os.write(1, str.encode(Fore.YELLOW + msg.__repr__() + '\n'))
