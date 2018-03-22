import json
import os


class ConfigReader(object):
    """Read configuration parameters from a json file.
    By default, the file is 'conf/smartanno_conf.json'."""
    configurations = None

    def __init__(self, config_file='conf/smartanno_conf.json'):
        self.config_file = config_file
        if ConfigReader.configurations is None:
            self.load(config_file)
        pass

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

    def getValue(self, key):
        value = ConfigReader.configurations
        for key in key.split('/'):
            if key in value:
                value = value[key]
            else:
                return None
        return value

    def refresh(self):
        self.load(self.config_file)
        pass

    def setValue(self, key=None, value=None):
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
                    else:
                        chain[key] = value
                        break

    def saveStatus(self, status=None, status_key='status/default'):
        if status is not None:
            if not status_key.startswith("status/"):
                status_key = "status/" + status_key
            self.setValue(status_key, status)
        self.saveConfig()

    def saveConfig(self):
        with open(self.config_file, 'w') as outfile:
            json.dump(ConfigReader.configurations, outfile, indent=2)
