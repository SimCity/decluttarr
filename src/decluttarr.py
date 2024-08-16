# Cleans the download queue
import logging, verboselogs
logger = verboselogs.VerboseLogger(__name__)
from src.utils.shared import errorDetails
from src.jobs.remove_failed import remove_failed
from src.jobs.remove_failed_imports import remove_failed_imports
from src.jobs.remove_metadata_missing import remove_metadata_missing
from src.jobs.remove_missing_files import remove_missing_files
from src.jobs.remove_orphans import remove_orphans
from src.jobs.remove_slow import remove_slow
from src.jobs.remove_stalled import remove_stalled
from src.jobs.remove_unmonitored import remove_unmonitored
from src.utils.trackers import Deleted_Downloads
from utils.arr import *

async def queueCleaner(settingsDict, arr, defective_tracker, download_sizes_tracker, protectedDownloadIDs, privateDowloadIDs):


     # Cleans up the downloads queue
    logger.verbose('Cleaning queue on %s:', arr.name.title())

    full_queue = await arr.get_queue()
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
            items_detected += await remove_failed(            settingsDict, arr, deleted_downloads, defective_tracker, protectedDownloadIDs, privateDowloadIDs)

        if settingsDict['REMOVE_FAILED_IMPORTS']: 
            items_detected += await remove_failed_imports(    settingsDict, arr, deleted_downloads, defective_tracker, protectedDownloadIDs, privateDowloadIDs)

        if settingsDict['REMOVE_METADATA_MISSING']: 
            items_detected += await remove_metadata_missing(  settingsDict, arr, deleted_downloads, defective_tracker, protectedDownloadIDs, privateDowloadIDs)

        if settingsDict['REMOVE_MISSING_FILES']: 
            items_detected += await remove_missing_files(     settingsDict, arr, deleted_downloads, defective_tracker, protectedDownloadIDs, privateDowloadIDs)

        if settingsDict['REMOVE_ORPHANS']: 
            items_detected += await remove_orphans(           settingsDict, arr, deleted_downloads, defective_tracker, protectedDownloadIDs, privateDowloadIDs)

        if settingsDict['REMOVE_SLOW']:
            items_detected += await remove_slow(              settingsDict, arr, deleted_downloads, defective_tracker, protectedDownloadIDs, privateDowloadIDs, download_sizes_tracker)

        if settingsDict['REMOVE_STALLED']: 
            items_detected += await remove_stalled(           settingsDict, arr, deleted_downloads, defective_tracker, protectedDownloadIDs, privateDowloadIDs)

        if settingsDict['REMOVE_UNMONITORED']: 
            items_detected += await remove_unmonitored(       settingsDict, arr, deleted_downloads, defective_tracker, protectedDownloadIDs, privateDowloadIDs)

        if items_detected == 0:
            logger.verbose('>>> Queue is clean.')
    except Exception as error:
        errorDetails(arr.name, error)
    return
