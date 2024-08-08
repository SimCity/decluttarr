# Cleans the download queue
import logging, verboselogs
logger = verboselogs.VerboseLogger(__name__)
from src.utils.shared import (errorDetails, get_queue)
from src.jobs.remove_failed import remove_failed
from src.jobs.remove_failed_imports import remove_failed_imports
from src.jobs.remove_metadata_missing import remove_metadata_missing
from src.jobs.remove_missing_files import remove_missing_files
from src.jobs.remove_orphans import remove_orphans
from src.jobs.remove_slow import remove_slow
from src.jobs.remove_stalled import remove_stalled
from src.jobs.remove_unmonitored import remove_unmonitored

class Deleted_Downloads:
    # Keeps track of which downloads have already been deleted (to not double-delete)
    def __init__(self, dict):
        self.dict = dict


async def queueCleaner(settingsDict, name, settings, defective_tracker, download_sizes_tracker, protectedDownloadIDs, privateDowloadIDs):
    # Read out correct instance depending on radarr/sonarr flag
    arr_type     = settings['TYPE']

    match arr_type:
        case 'RADARR':
            full_queue_param = 'includeUnknownMovieItems'
        case 'SONARR':
            full_queue_param = 'includeUnknownSeriesItems'
        case 'LIDARR':
            full_queue_param = 'includeUnknownArtistItems'
        case 'READARR':
            full_queue_param = 'includeUnknownAuthorItems'   
        case 'WHISPARR':
            full_queue_param = 'includeUnknownSeriesItems'      
        case _:
            logger.error('Unknown arr type specified, exiting: %s', str(arr_type))
            sys.exit()

    # Get Details for given *Arr Instance
    BASE_URL    = settings['URL']
    API_KEY     = settings['KEY']

    # Cleans up the downloads queue
    logger.verbose('Cleaning queue on %s:', name)

    full_queue = await get_queue(BASE_URL, API_KEY, params = {full_queue_param: True})
    if not full_queue: 
        logger.verbose('>>> Queue is empty.')
        return
    else:
        logger.debug('queueCleaner/full_queue at start:')
        logger.debug(full_queue)        
        
    deleted_downloads = Deleted_Downloads([])
    items_detected = 0
    try:    
        if settingsDict['REMOVE_FAILED']:
            items_detected += await remove_failed(            settingsDict, BASE_URL, API_KEY, name, deleted_downloads, defective_tracker, protectedDownloadIDs, privateDowloadIDs)

        if settingsDict['REMOVE_FAILED_IMPORTS']: 
            items_detected += await remove_failed_imports(    settingsDict, BASE_URL, API_KEY, name, deleted_downloads, defective_tracker, protectedDownloadIDs, privateDowloadIDs)

        if settingsDict['REMOVE_METADATA_MISSING']: 
            items_detected += await remove_metadata_missing(  settingsDict, BASE_URL, API_KEY, name, deleted_downloads, defective_tracker, protectedDownloadIDs, privateDowloadIDs)

        if settingsDict['REMOVE_MISSING_FILES']: 
            items_detected += await remove_missing_files(     settingsDict, BASE_URL, API_KEY, name, deleted_downloads, defective_tracker, protectedDownloadIDs, privateDowloadIDs)

        if settingsDict['REMOVE_ORPHANS']: 
            items_detected += await remove_orphans(           settingsDict, BASE_URL, API_KEY, name, deleted_downloads, defective_tracker, protectedDownloadIDs, privateDowloadIDs, full_queue_param)

        if settingsDict['REMOVE_SLOW']:
            items_detected += await remove_slow(              settingsDict, BASE_URL, API_KEY, name, deleted_downloads, defective_tracker, protectedDownloadIDs, privateDowloadIDs, download_sizes_tracker)

        if settingsDict['REMOVE_STALLED']: 
            items_detected += await remove_stalled(           settingsDict, BASE_URL, API_KEY, name, deleted_downloads, defective_tracker, protectedDownloadIDs, privateDowloadIDs)

        if settingsDict['REMOVE_UNMONITORED']: 
            items_detected += await remove_unmonitored(       settingsDict, BASE_URL, API_KEY, name, deleted_downloads, defective_tracker, protectedDownloadIDs, privateDowloadIDs, arr_type)

        if items_detected == 0:
            logger.verbose('>>> Queue is clean.')
    except Exception as error:
        errorDetails(name, error)
    return
