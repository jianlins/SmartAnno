import json
import os


class ConfigReader(object):
    """Read configuration parameters from a json file.
    By default, the file is 'conf/smartanno_conf.json'."""
    configurations = None
    config_file = ''

    def __init__(self, config_file='conf/smartanno_conf.json'):
        if ConfigReader.configurations is None:
            self.load(config_file)
            ConfigReader.config_file = config_file
        pass

    def __initDirs(self):
        directory=os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(ConfigReader.config_file))),
                     'data')
        if not os.path.exists(directory):
            os.makedirs(directory)

    def load(self, config_file):
        if not os.path.isfile(config_file):
            current_dir = os.getcwd()
            root_pos = current_dir.find(os.sep + 'src' + os.sep)
            root = current_dir[:root_pos + 5]
            config_file = root + config_file
        if os.path.isfile(config_file):
            with open(config_file, 'r') as f:
                ConfigReader.configurations = json.load(f)
        else:
            raise FileExistsError('File "' + config_file + '" doesn\'t exist')

    @classmethod
    def getValue(cls, key):
        value = ConfigReader.configurations
        for key in key.split('/'):
            if key in value:
                value = value[key]
                if key.endswith('path'):
                    if not os.path.isabs(value):
                    # automatically adjust the path if this class is not initiated from project root path
                        value = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(ConfigReader.config_file))),
                                         value)
            else:
                return None
        return value

    def refresh(self):
        self.load(ConfigReader.config_file)
        pass

    @classmethod
    def setValue(cls, key=None, value=None):
        if value is not None and key is not None:
            chain = ConfigReader.configurations
            keys = key.split("/")
            for i in range(0, len(keys)):
                key = keys[i]
                if key in chain:
                    if not isinstance(chain[key], dict):
                        chain[key] = value
                        break
                    chain = chain[key]
                else:
                    if i < len(keys) - 1:
                        chain[key] = {}
                        chain = chain[key]
                    else:
                        chain[key] = value
                        break

    @classmethod
    def saveStatus(cls, status=None, status_key='status/default'):
        if status is not None:
            if not status_key.startswith("status/"):
                status_key = "status/" + status_key
            cls.setValue(status_key, status)
        cls.saveConfig()

    @classmethod
    def saveConfig(cls):
        with open(ConfigReader.config_file, 'w') as outfile:
            json.dump(ConfigReader.configurations, outfile, indent=2)
