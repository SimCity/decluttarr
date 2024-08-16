#!/usr/bin/env python
from config.parser import get_config_value
from config.parser import get_instances
from config.env_vars import *
from src.utils.downloader import deluge, genericDownloader, qBittorrent
from utils.arr import *

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
NO_STALLED_REMOVAL_TAG          = get_config_value('NO_STALLED_REMOVAL_TAG',   'features',     False,  str,   'Don\'t Kill')
IGNORE_PRIVATE_TRACKERS         = get_config_value('IGNORE_PRIVATE_TRACKERS',       'features',     False,  bool,   True)
FAILED_IMPORT_MESSAGE_PATTERNS  = get_config_value('FAILED_IMPORT_MESSAGE_PATTERNS','features',     False,  list,   [])

########################################################################################################################


########### Enrich setting variables

RADARR_MIN_VERSION          = '5.3.6.8608'
SONARR_MIN_VERSION          = '4.0.1.1131'
LIDARR_MIN_VERSION          = None
READARR_MIN_VERSION         = None
WHISPARR_MIN_VERSION        = '2.0.0.548'
QBITTORRENT_MIN_VERSION     = '4.3.0'
DELUGE_MIN_VERSION          = '4.3.0'
TRANSMISSION_MIN_VERSION    = '4.1.0'

SUPPORTED_ARR_APPS  = ['RADARR', 'SONARR', 'LIDARR', 'READARR', 'WHISPARR']

SUPPORTED_TORRENT_APPS  = ['QBITTORRENT', 'DELUGE']

########### Add Variables to Dictionary
settingsDict = {}
for var_name in dir():
    if var_name.isupper():
        settingsDict[var_name] = locals()[var_name]


########################################################################################################################
########### Get Arr Clients

arr_names                       = get_config_value('ARR_NAMES',                     'general',       False,  list, SUPPORTED_ARR_APPS)


settingsDict['INSTANCES'] = {}
for arr_name in arr_names:
    settingsDict['INSTANCES'][arr_name] = {}

    arrType = get_config_value(arr_name.upper() + '_TYPE', arr_name, False, str, arr_name)
    url = get_config_value(arr_name.upper() + '_URL', arr_name, False, str )
    key = get_config_value(arr_name.upper() + '_KEY', arr_name, True, str, '')

    match arrType:
        case 'SONARR':
            settingsDict['INSTANCES'][arr_name.upper()] = sonarr(
                arr_name,
                url,
                key,
                SONARR_MIN_VERSION
            )
        case 'RADARR':
            settingsDict['INSTANCES'][arr_name.upper()] = radarr(
                arr_name,
                url,
                key,
                RADARR_MIN_VERSION
            )
        case 'LIDARR':
            settingsDict['INSTANCES'][arr_name.upper()] = lidarr(
                arr_name,
                url,
                key,
                LIDARR_MIN_VERSION
            )
        case 'READARR':
            settingsDict['INSTANCES'][arr_name.upper()] = readarr(
                arr_name,
                url,
                key,
                READARR_MIN_VERSION
            )
        case 'WHISARR':
            settingsDict['INSTANCES'][arr_name.upper()] = whisparr(
                arr_name,
                url,
                key,
                WHISPARR_MIN_VERSION
            )


########################################################################################################################
########### Get Download Clients

downloader_names                       = get_config_value('DOWNLOADER_NAMES',                     'general',       False,  list, SUPPORTED_TORRENT_APPS)

settingsDict['DOWNLOADERS'] = {}
for downloader in downloader_names:

    downloaderType = get_config_value(downloader.upper() + '_TYPE', downloader, False, str, downloader).upper()

    match downloaderType:
        case 'QBITORRENT':
            settingsDict['DOWNLOADERS'][downloader.upper()] = qBittorrent(
                downloader,
                get_config_value(downloader.upper() + '_URL', downloader, False, str),
                get_config_value(downloader.upper() + '_USERNAME', downloader, False, str),
                get_config_value(downloader.upper() + '_PASSWORD', downloader, False, str),
                QBITTORRENT_MIN_VERSION
            )
        case 'DELUGE':
            settingsDict['DOWNLOADERS'][downloader.upper()] = deluge(
                downloader,
                get_config_value(downloader.upper() + '_URL', downloader, False, str),
                get_config_value(downloader.upper() + '_PASSWORD', downloader, False, str),
                DELUGE_MIN_VERSION
            )


########################################################################################################################
########### Validate settings

instances = "/".join(list(map(str.title(), settingsDict['INSTANCES'])))
if len(instances) == 0:
    instances = 'Arr'

if not (IS_IN_PYTEST or len(settingsDict['INSTANCES']) > 0):
    print(f'[ ERROR ]: No {instances} URLs specified (nothing to monitor)')
    exit()

instances = "/".join(list(map(str.title(), settingsDict['DOWNLOADERS'])))
if len(instances) == 0:
    instances = 'Downloader'

if not (IS_IN_PYTEST or len(settingsDict['DOWNLOADERS']) > 0):
    print(f'[ ERROR ]: No {instances} URLs specified (nothing to check torrents from). Using generic downlaod calcualtions which are not accurate and no means to track protected or private torrents.')
    settingsDict['DOWNLOADERS']['GENERIC'] = genericDownloader('Generic', None, None) 
    