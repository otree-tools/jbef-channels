from os import environ

# if you set a property in SESSION_CONFIG_DEFAULTS, it will be inherited by all configs
# in SESSION_CONFIGS, except those that explicitly override it.
# the session config can be accessed from methods in your apps as self.session.config,
# e.g. self.session.config['participation_fee']

EXTENSION_APPS = ['minimum', 'auctionone', 'realefforttask']

AWS_ACCESS_KEY_ID = environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = environ.get('AWS_SECRET_ACCESS_KEY')

SESSION_CONFIG_DEFAULTS = {
    'real_world_currency_per_point': 1.00,
    'participation_fee': 0.00,
    'doc': "",
}

SESSION_CONFIGS = [
    # {
    #     'name': 'minimum_ret',
    #     'display_name': 'Simple RET example',
    #     'num_demo_participants': 1,
    #     'app_sequence': ['minimum'],
    #
    # },
    {
        'name': 'realefforttask',
        'display_name': 'Real Effort Task - 2 matrices',
        'num_demo_participants': 1,
        'app_sequence': ['realefforttask'],
        'task': 'TwoMatrices',
        'task_params': {'difficulty': 10},
    },
    {
        'name': 'realefforttask2',
        'display_name': 'Real Effort Task - sum of N numbers',
        'num_demo_participants': 1,
        'app_sequence': ['realefforttask'],
        'task': 'SumNumbers',
        'task_params': {'difficulty': 2},
    },

    {
        'name': 'realefforttask3',
        'display_name': 'Real Effort Task - count 0s',
        'num_demo_participants': 1,
        'app_sequence': ['realefforttask'],
        'task': 'CountZeroes',
        'task_params': {'num_rows': 10, 'num_columns': 5},
    },
    {
        'name': 'realefforttask4',
        'display_name': 'Real Effort Task - Decoding',
        'num_demo_participants': 1,
        'app_sequence': ['realefforttask'],
        'task': 'Decoding',
        'task_params': {'dict_length': 10, 'task_len': 5},
    },
    {
        'name': 'auctionone',
        'display_name': 'One sided auction and RET',
        'num_demo_participants': 4,
        'app_sequence': ['auctionone'],

    },
]

# ISO-639 code
# for example: de, fr, ja, ko, zh-hans
LANGUAGE_CODE = 'en'

# e.g. EUR, GBP, CNY, JPY
REAL_WORLD_CURRENCY_CODE = 'USD'
USE_POINTS = True

# AUTH_LEVEL:
# this setting controls which parts of your site are freely accessible,
# and which are password protected:
# - If it's not set (the default), then the whole site is freely accessible.
# - If you are launching a study and want visitors to only be able to
#   play your app if you provided them with a start link, set it to STUDY.
# - If you would like to put your site online in public demo mode where
#   anybody can play a demo version of your game, but not access the rest
#   of the admin interface, set it to DEMO.

# for flexibility, you can set it in the environment variable OTREE_AUTH_LEVEL
AUTH_LEVEL = environ.get('OTREE_AUTH_LEVEL')

ADMIN_USERNAME = 'admin'
# for security, best to set admin password in an environment variable
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD')

# Consider '', None, and '0' to be empty/false
DEBUG = (environ.get('OTREE_PRODUCTION') in {None, '', '0'})

DEMO_PAGE_INTRO_HTML = """ """

# don't share this with anybody.
SECRET_KEY = '%&w(ic-c^8avzg9833mspr)3uyvm5p9ce4y%iv$n@6@d9f9b-u'

# if an app is included in SESSION_CONFIGS, you don't need to list it here
INSTALLED_APPS = ['otree']
