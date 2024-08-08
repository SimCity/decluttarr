#!/usr/bin/env python
from config.parser import get_config_value
from config.parser import get_instances
from config.env_vars import *
# Define data types and default values for settingsDict variables
# General   
LOG_LEVEL                       = get_config_value('LOG_LEVEL',                     'general',      False,  str,    'INFO')
TEST_RUN                        = get_config_value('TEST_RUN',                      'general',      False,  bool,   False)
SSL_VERIFICATION                = get_config_value('SSL_VERIFICATION',              'general',      False,  bool,   True)

# Features  
REMOVE_TIMER                    = get_config_value('REMOVE_TIMER',                  'features',     False,  float,  10)
REMOVE_FAILED                   = get_config_value('REMOVE_FAILED',                 'features',     False,  bool,   False)
REMOVE_FAILED_IMPORTS           = get_config_value('REMOVE_FAILED_IMPORTS' ,        'features',     False,  bool,   False)
REMOVE_METADATA_MISSING         = get_config_value('REMOVE_METADATA_MISSING',       'features',     False,  bool,   False)
REMOVE_MISSING_FILES            = get_config_value('REMOVE_MISSING_FILES' ,         'features',     False,  bool,   False)
REMOVE_NO_FORMAT_UPGRADE        = get_config_value('REMOVE_NO_FORMAT_UPGRADE' ,     'features',     False,  bool,   False) # OUTDATED - WILL RETURN WARNING
REMOVE_ORPHANS                  = get_config_value('REMOVE_ORPHANS' ,               'features',     False,  bool,   False)
REMOVE_SLOW                     = get_config_value('REMOVE_SLOW' ,                  'features',     False,  bool,   False)
REMOVE_STALLED                  = get_config_value('REMOVE_STALLED',                'features',     False,  bool,   False)
REMOVE_UNMONITORED              = get_config_value('REMOVE_UNMONITORED' ,           'features',     False,  bool,   False)
MIN_DOWNLOAD_SPEED              = get_config_value('MIN_DOWNLOAD_SPEED',            'features',     False,  int,    0)
PERMITTED_ATTEMPTS              = get_config_value('PERMITTED_ATTEMPTS',            'features',     False,  int,    3)
NO_STALLED_REMOVAL_QBIT_TAG     = get_config_value('NO_STALLED_REMOVAL_QBIT_TAG',   'features',     False,  str,   'Don\'t Kill')
IGNORE_PRIVATE_TRACKERS         = get_config_value('IGNORE_PRIVATE_TRACKERS',       'features',     False,  bool,   True)
FAILED_IMPORT_MESSAGE_PATTERNS  = get_config_value('FAILED_IMPORT_MESSAGE_PATTERNS','features',     False,  list,   [])

# qBittorrent   
QBITTORRENT_URL                 = get_config_value('QBITTORRENT_URL',               'qbittorrent',  False,  str,    '')
QBITTORRENT_USERNAME            = get_config_value('QBITTORRENT_USERNAME',          'qbittorrent',  False,  str,    '')
QBITTORRENT_PASSWORD            = get_config_value('QBITTORRENT_PASSWORD',          'qbittorrent',  False,  str,    '')

########### Enrich setting variables
if QBITTORRENT_URL: QBITTORRENT_URL += '/api/v2'

########### Add Variables to Dictionary
settingsDict = {}
for var_name in dir():
    if var_name.isupper():
        settingsDict[var_name] = locals()[var_name]


arr_names                       = get_config_value('ARR_NAMES',                     'general',       True,  list, [])

for arr_name in arr_names:
    settingsDict['INSTANCES'][arr_name.upper()]['TYPE'] = get_config_value(arr_name.upper() + '_TYPE', arr_name, True, str, '')
    settingsDict['INSTANCES'][arr_name.upper()]['URL']  = get_config_value(arr_name.upper() + '_URL', arr_name, True, str, '')
    settingsDict['INSTANCES'][arr_name.upper()]['KEY']  = get_config_value(arr_name.upper() + '_KEY', arr_name, True, str, '')



for instance, settings in settingsDict['INSTANCES'].items():
    match settings['TYPE']:
        case 'RADARR':
            port = '7878'
            end_point = '/api/v3'
        case 'SONAR':
            port = '8989'
            end_point = '/api/v3'
        case 'LIDARR':
            port = '8686'
            end_point = '/api/v1'
        case 'READARR':
            port = '8787'
            end_point = '/api/v1'
        case 'WHISPARR':
            port = '6969'
            end_point = '/api/v3'

    if ( not settings.haskey('URL') or len(settings['URL']) == 0 ):
        settingsDict['INSTANCES'][instance]['url'] = 'http://' + instance[arr_name] + ':' + port

    settingsDict['INSTANCES'][instance]['url'] += end_point

########################################################################################################################
########### Validate settings

if (len(settingsDict['INSTANCES']) == 0):
    print(f'[ ERROR ]: No Radarr/Sonarr/Lidarr/Readarr/Whisparr URLs specified (nothing to monitor)')
    exit()

