########### Import Libraries
import logging, verboselogs
logger = verboselogs.VerboseLogger(__name__)
from dateutil.relativedelta import relativedelta as rd
import requests 
from src.utils.rest import rest_get, rest_post # 
import asyncio
from packaging import version
from src.utils.downloader import *
from utils.arr import *

def setLoggingFormat(settingsDict):
    # Sets logger output to specific format
    log_level_num=logging.getLevelName(settingsDict['LOG_LEVEL'])
    logging.basicConfig(
        format=('' if settingsDict['IS_IN_DOCKER'] else '%(asctime)s ') + ('[%(levelname)-7s]' if settingsDict['LOG_LEVEL']=='VERBOSE' else '[%(levelname)s]') + ': %(message)s', 
        level=log_level_num 
    )
    return 


async def getArrInstanceName(settingsDict, arrApp):
    # Retrieves the names of the arr instances, and if not defined, sets a default (should in theory not be requried, since UI already enforces a value)
    try:

        arrType = arrApp.GetType()
        if not(arrType.uppper() == type(arrApp).__name__):
            logger.warning('Type doesn\'t match for %s: Expected %s, found %s', arrApp, type(arrApp).__name__, arrType)
            settingsDict['INSTANCES'].pop(arrApp)
    except:
            logger.debug('Could not retireve instance name for %s, using value as is: %s', arrApp, settingsDict[arrApp]['TYPE'])
    
    return settingsDict

async def getProtectedAndPrivateTorrents(settingsDict):
    # Returns two lists containing the values found in downloadId of Arrs that are either protected by tag, or are private trackers (if IGNORE_PRIVATE_TRACKERS is true)
    protectedDownloadIDs = []
    privateDowloadIDs = []
    for downloader in settingsDict['DOWNLOADERS']:
        # Fetch all torrents

        tempProtectedDownloadIDs, tempPrivateDowloadIDs = downloader.GetProtectedAndPrivate(settingsDict)

        logger.debug('main/getProtectedAndPrivateFrom%s/protectedDownloadIDs: %s', downloader.name.title(), str(protectedDownloadIDs))
        logger.debug('main/getProtectedAndPrivateFrom%s/privateDowloadIDs: %s', downloader.name.title(), str(privateDowloadIDs))   

        protectedDownloadIDs.extend(tempProtectedDownloadIDs)
        privateDowloadIDs.extend(tempPrivateDowloadIDs)




    return protectedDownloadIDs, privateDowloadIDs


       
def showWelcome():
    # Welcome Message
    logger.info('#' * 50)
    logger.info('Decluttarr - Application Started!')
    logger.info('')      
    logger.info('Like this app? Thanks for giving it a ⭐️ on GitHub!')      
    logger.info('https://github.com/ManiMatter/decluttarr/')   
    logger.info('')  
    return

def showSettings(settingsDict):
    # Settings Message
    fmt = '{0.days} days {0.hours} hours {0.minutes} minutes'     
    logger.info('*** Current Settings ***') 
    logger.info('Version: %s', settingsDict['IMAGE_TAG']) 
    logger.info('Commit: %s', settingsDict['SHORT_COMMIT_ID'])    
    logger.info('')       
    logger.info('%s | Removing failed downloads (%s)', str(settingsDict['REMOVE_FAILED']), 'REMOVE_FAILED')
    logger.info('%s | Removing failed imports (%s)', str(settingsDict['REMOVE_FAILED_IMPORTS']), 'REMOVE_FAILED_IMPORTS')
    if settingsDict['REMOVE_FAILED_IMPORTS'] and not settingsDict['FAILED_IMPORT_MESSAGE_PATTERNS']:
        logger.verbose ('> Any imports with a warning flag are considered failed, as no patterns specified (%s).', 'FAILED_IMPORT_MESSAGE_PATTERNS')
    elif settingsDict['REMOVE_FAILED_IMPORTS'] and settingsDict['FAILED_IMPORT_MESSAGE_PATTERNS']:
        logger.verbose ('> Imports with a warning flag are considered failed if the status message contains any of the following patterns:')
        for pattern in settingsDict['FAILED_IMPORT_MESSAGE_PATTERNS']: 
            logger.verbose('  - "%s"', pattern)
    logger.info('%s | Removing downloads missing metadata (%s)', str(settingsDict['REMOVE_METADATA_MISSING']), 'REMOVE_METADATA_MISSING') 
    logger.info('%s | Removing downloads missing files (%s)', str(settingsDict['REMOVE_MISSING_FILES']), 'REMOVE_MISSING_FILES')
    logger.info('%s | Removing orphan downloads (%s)', str(settingsDict['REMOVE_ORPHANS']), 'REMOVE_ORPHANS')  
    logger.info('%s | Removing slow downloads (%s)', str(settingsDict['REMOVE_SLOW']), 'REMOVE_SLOW')
    logger.info('%s | Removing stalled downloads (%s)', str(settingsDict['REMOVE_STALLED']), 'REMOVE_STALLED')
    logger.info('%s | Removing downloads belonging to unmonitored items (%s)', str(settingsDict['REMOVE_UNMONITORED']), 'REMOVE_UNMONITORED') 
    logger.info('')          
    logger.info('Running every: %s', fmt.format(rd(minutes=settingsDict['REMOVE_TIMER'])))  
    if settingsDict['REMOVE_SLOW']: 
        logger.info('Minimum speed enforced: %s KB/s', str(settingsDict['MIN_DOWNLOAD_SPEED'])) 
    logger.info('Permitted number of times before stalled/missing metadata/slow downloads are removed: %s', str(settingsDict['PERMITTED_ATTEMPTS']))      
    if settingsDict['QBITTORRENT_URL']: 
        logger.info('Downloads with this tag will be skipped: \"%s\"', settingsDict['NO_STALLED_REMOVAL_QBIT_TAG'])  
        logger.info('Private Trackers will be skipped: %s', settingsDict['IGNORE_PRIVATE_TRACKERS'])        
    
    logger.info('') 
    logger.info('*** Configured Instances ***')
    
    for name , settings in settingsDict['INSTANCES'].items():
        if settings['URL']: 
            logger.info(
                    '%s%s: %s',
                    name.title(),
                    f" ({settings['TYPE'].title()})" if settings['TYPE'].title() != name.title() else "",
                    (settings['URL']).split('/api')[0]
                )

    if settingsDict['QBITTORRENT_URL']: 
        logger.info(
            'qBittorrent: %s', 
            (settingsDict['QBITTORRENT_URL']).split('/api')[0]
        )    

    logger.info('') 
    return   

def upgradeChecks(settingsDict):
    if settingsDict['REMOVE_NO_FORMAT_UPGRADE']:
        logger.warn('❗️' * 10 + ' OUTDATED SETTINGS ' + '❗️' * 10 )
        logger.warn('')        
        logger.warn("❗️ %s was replaced with %s.", 'REMOVE_NO_FORMAT_UPGRADE', 'REMOVE_FAILED_IMPORTS')        
        logger.warn("❗️ Please check the ReadMe and update your settings.")
        logger.warn("❗️ Specifically read the section on %s.", 'FAILED_IMPORT_MESSAGE_PATTERNS')
        logger.warn('')
        logger.warn('❗️' * 29)
        logger.warn('')
    return

async def instanceChecks(settingsDict):
    # Checks if the arr and qbit instances are reachable, and returns the settings dictionary with the qbit cookie 
    logger.info('*** Check Instances ***')
    error_occured = False
    # Check ARR-apps
    for arrApp in settingsDict['INSTANCES']:
        error_occured = arrApp.InstanceCheck()
    
        if error_occured:
            logger.warning('At least one instance had a problem. Waiting for 60 seconds, then exiting Decluttarr.')      
            await asyncio.sleep(60)
            exit()

    error_occured = False
    # Check Bittorrent
    for downloader in settingsDict['DOWNLOADERS']:
        error_occured = downloader.instanceCheck(settingsDict, downloader)

        if error_occured:
            logger.warning('At least one downloader had a problem. Waiting for 60 seconds, then exiting Decluttarr.')      
            await asyncio.sleep(60)
            exit()


    logger.info('') 
    return settingsDict




def showLoggerLevel(settingsDict):
    logger.info('#' * 50)
    if settingsDict['LOG_LEVEL'] == 'INFO':
        logger.info('LOG_LEVEL = INFO: Only logging changes (switch to VERBOSE for more info)')      
    else:
        logger.info(f'')
    if settingsDict['TEST_RUN']:
        logger.info(f'*'* 50)
        logger.info(f'*'* 50)
        logger.info(f'')
        logger.info(f'!! TEST_RUN FLAG IS SET !!')       
        logger.info(f'NO UPDATES/DELETES WILL BE PERFORMED')
        logger.info(f'')
        logger.info(f'*'* 50)
        logger.info(f'*'* 50)





