from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))
with open(path.join(here, 'README'), encoding='utf-8') as f:
    long_description = f.read()
setup(
    name='SmartAnno',
    packages=['SmartAnno.db', 'SmartAnno.gui', 'SmartAnno.conf', 'SmartAnno.models', 'SmartAnno.umls',
              'SmartAnno.utils', 'SmartAnno'],
    # find_packages(
    #     include=['SmartAnno.conf.*', 'SmartAnno.db.*', 'SmartAnno.gui.*', 'SmartAnno.models.*', 'SmartAnno.umls.*',
    #              'SmartAnno.utils.*', 'SmartAnno'],
    # exclude=['*.json', '*.sqlite', 'SmartAnno.test', '*.ipynb_checkpoints', '*.ini']
    # ),
    # this must be the same as the name above
    version='1.0.26.dev',
    description='A smart snippet annotation tool with deep learning backbone.',
    author='Jianlin',
    author_email='jianlinshi.cn@gmail.com',
    url='https://github.com/jianlins/SmartAnno',  # use the URL to the github repo
    download_url='https://github.com/jianlins/SmartAnno/archive/1.0.0.zip',  # I'll explain this in a second
    keywords=['SmartAnno', 'NLP', 'annotation', 'Deep Learning', 'Machine Learning', 'semi-supervised'],
    long_description=long_description,
    classifiers=[
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Development Status :: 3 - Alpha',
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Linguistic",
    ],
    install_requires=[
        'PyRuSH', 'sqlalchemy-dao', 'keras', 'spacy', 'ipywidgets', 'jupyter', 'scikit-learn', 'numpy', 'sqlalchemy',
        'colorama', 'textblob', 'Whoosh'
    ],
    include_package_data=True,
    extras_require={
        "tf": ["tensorflow"],
        "tf_gpu": ["tensorflow-gpu"],
    },
    package_data={'SmartAnno/conf': ['rush_rules.tsv', 'general_modifiers.yml', 'smartanno_conf.json.bk']},
    data_files=[('SmartAnno/conf', ['SmartAnno/conf/rush_rules.tsv', 'SmartAnno/conf/general_modifiers.yml',
                                    'SmartAnno/conf/smartanno_conf.json.bk'])],
)
