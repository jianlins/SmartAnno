import json
import os


class ConfigReader(object):
    """Read configuration parameters from a json file.
    By default, the file is 'conf/smartanno_conf.json'."""
    configurations = None

    def __init__(self, config_file='conf/smartanno_conf.json'):
        if ConfigReader.configurations is None:
            self.load(config_file)
        self.config_file = config_file
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

    def getValue(self, status_key):
        value = ConfigReader.configurations
        for key in status_key.split('/'):
            if key in value:
                value = value[key]
        if isinstance(value, dict):
            return None
        return value

    def refresh(self):
        self.load(self.config_file)
        pass

    def saveStatus(self, status=None, status_key='status/default'):
        print(status)
        if status is not None:
            value = ConfigReader.configurations
            if not status_key.startswith("status/"):
                status_key = "status/" + status_key
            keys = status_key.split("/")
            for i in range(0, len(keys)):
                key = keys[i]
                if key in value:
                    if not isinstance(value[key], dict):
                        value[key] = status
                        break
                    value = value[key]
                else:
                    if i < len(keys) - 1:
                        value[key] = {}
                    else:
                        value[key] = status
                        break
        print(ConfigReader.configurations)
        with open(self.config_file, 'w') as outfile:
            json.dump(ConfigReader.configurations, outfile, indent=2)
