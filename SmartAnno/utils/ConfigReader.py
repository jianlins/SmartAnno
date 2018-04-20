import json
import os

from SmartAnno.utils.NoteBookLogger import logError, logMsg


class ConfigReader(object):
    """Read configuration parameters from a json file.
    By default, the file is 'conf/smartanno_conf2.json'."""
    configurations = None
    config_file = ''

    def __init__(self, config_file='conf/smartanno_conf.json'):
        self.root = os.path.abspath(os.path.dirname(os.path.dirname(ConfigReader.config_file)))
        if ConfigReader.configurations is None:
            self.load(config_file)
        pass

    def __initDirs(self):
        directory = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(ConfigReader.config_file))),
                                 'data')
        if not os.path.exists(directory):
            os.makedirs(directory)

    def load(self, config_file):
        if not os.path.isfile(config_file):
            current_dir = os.getcwd()
            logMsg('current_dir=' + current_dir)
            root_pos = current_dir.rfind(os.sep + 'SmartAnno' + os.sep)
            root = current_dir[:root_pos + 11] if root_pos > 0 else current_dir
            self.root = root
            logMsg('root=' + root)
            config_file = os.path.join(root, config_file)
        if os.path.isfile(config_file):
            with open(config_file, 'r') as f:
                ConfigReader.configurations = json.load(f)
        else:
            if not os.path.exists(os.path.join(root, 'conf')):
                os.makedirs(os.path.join(root, 'conf'))
            from SmartAnno.conf.DefaultRules import smartanno_config
            with open(config_file, 'w+') as f:
                f.write(smartanno_config)
            ConfigReader.configurations = json.loads(smartanno_config)
            logError('File "' + config_file + '" doesn\'t exist, create ' + os.path.abspath(
                config_file) + ' using default settings.')
        ConfigReader.config_file = config_file
        self.setUpDirs()
        self.dumpDefaultRules()

    def setUpDirs(self):
        if not os.path.exists(os.path.join(self.root, 'data')):
            os.makedirs(os.path.join(self.root, 'data'))
        if not os.path.exists(os.path.join(self.root, 'data/whoosh_idx')):
            os.makedirs(os.path.join(self.root, 'data/whoosh_idx'))
        if not os.path.exists(os.path.join(self.root, 'models')):
            os.makedirs(os.path.join(self.root, 'models'))
        if not os.path.exists(os.path.join(self.root, 'models/saved')):
            os.makedirs(os.path.join(self.root, 'models/saved'))

    def dumpDefaultRules(self):
        conf_path = os.path.join(self.root, 'conf')
        if not os.path.exists(os.path.join(conf_path, 'rush_rules.tsv')):
            from SmartAnno.conf.DefaultRules import rush_rules
            self.writeFile(os.path.join(conf_path, 'rush_rules.tsv'), rush_rules)
        if not os.path.exists(os.path.join(conf_path, 'general_modifiers.yml')):
            from SmartAnno.conf.DefaultRules import pycontext_rules
            self.writeFile(os.path.join(conf_path, 'general_modifiers.yml'), pycontext_rules)

    def writeFile(self, filepath, content):
        with open(filepath, "w") as text_file:
            text_file.write(content)
        pass

    @classmethod
    def getValue(cls, key):
        value = ConfigReader.configurations
        for key in key.split('/'):
            if key in value:
                value = value[key]
                if key.endswith('path'):
                    if not os.path.isabs(value) and len(value) > 0:
                        # automatically adjust the path if this class is not initiated from project root path
                        value = os.path.join(
                            os.path.abspath(os.path.dirname(os.path.dirname(ConfigReader.config_file))),
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
