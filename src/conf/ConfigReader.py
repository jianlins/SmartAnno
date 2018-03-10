import json
import os


class ConfigReader(object):
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

	def getValue(self, key):
		if key in ConfigReader.configurations:
			return ConfigReader.configurations[key]
		else:
			return None

	def refresh(self):
		self.load(self.config_file)
		pass
