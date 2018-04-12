import json
import os

from utils.NoteBookLogger import logError, logMsg


class ConfigReader(object):
	"""Read configuration parameters from a json file.
	By default, the file is 'conf/smartanno_conf2.json'."""
	configurations = None
	config_file = ''

	default_config_str = '''
{
  "setup_instruction": "if there is no 'smartanno_conf2.json' under 'conf' directory, need to copy this file and rename it to 'smartanno_conf2.json'. ",
  "api_key": "",
  "api_key_comment": "api key for UMLS access",
  "db_header": "sqlite+pysqlite:///",
  "db_path": "data/demo.sqlite",
  "learning_steps": 10,
  "learning_steps_comment": "reclassify the rest of samples after review every # of samples",
  "status": {
    "default": 0,
    "workflow1": 1,
    "workflow_0": 1,
    "tasknamer_2": "task1",
    "types_6": [
      "Typea",
      "Typeb"
    ],
    "tasknamer_5": "task1",
    "types_9": [
      "Typea",
      "Typeb",
      "neutral"
    ],
    "tasknamer_6": "task1",
    "types_10": [
      "Typea",
      "Typeb",
      "neutral"
    ],
    "tasknamer_25": "task1",
    "types_29": [
      "Typea",
      "Typeb"
    ],
    "umls_extender_loop": 10,
    "w_e_extender_loop": 12,
    "rb_review_loop": 17
  },
  "glove": {
    "vocab": 1900000,
    "vector": 300,
    "model_path": "models/saved/glove/glove.42B.300d.bin"
  },
  "rush_rules_path": "conf/rush_rules.tsv",
  "umls": {
    "sources": [
      "SNOMEDCT_US"
    ],
    "filter_by_length": 0,
    "filter_by_contains": true,
    "max_query": 50
  },
  "review": {
    "review_comment": "configurations of sample data reviewing window",
    "div_height": "200px",
    "div_height_comment": "height of textarea to display the sample",
    "meta_columns": [
      "DOC_ID",
      "DATE",
      "REF_DATE"
    ],
    "rb_model_threshold": 10,
    "rb_model_threshold_comment": "max_documents_for_rb_model",
    "show_meta_name": true,
    "ml_learning_pace": 5
  },
  "cnn_model": {
    "max_token_per_sentence": 5000,
    "stopwords_file": "",
    "learning_pace": 10
  },
  "nb_model": {
    "learning_pace": 10
  },
  "logisticbow_model": {
    "learning_pace": 10
  }
}'''

	def __init__(self, config_file='conf/smartanno_conf2.json'):
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
			with open(config_file, 'w+') as f:
				f.write(self.default_config_str)
			ConfigReader.configurations = json.loads(self.default_config_str)
			logError('File "' + config_file + '" doesn\'t exist, create ' + os.path.abspath(
				config_file) + ' using default settings.')
		ConfigReader.config_file = config_file

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
