from src.utils.shared import (errorDetails, formattedQueueInfo, get_queue, privateTrackerCheck, protectedDownloadCheck, execute_checks, permittedAttemptsCheck, remove_download)
import sys, os, traceback
import logging, verboselogs
logger = verboselogs.VerboseLogger(__name__)
from src.utils.rest import rest_get

async def remove_unmonitored(settingsDict, arr, deleted_downloads, defective_tracker, protectedDownloadIDs, privateDowloadIDs):
    # Removes downloads belonging to movies/tv shows that are not monitored. Does not add to blocklist   
    try:
        failType = 'unmonitored'
        queue = await arr.get_queue()
        logger.debug('remove_unmonitored/queue IN: %s', formattedQueueInfo(queue))
        if not queue: return 0
        # Find items affected
        monitoredDownloadIDs = []
        for queueItem in queue['records']: 
            isMonitored = arr.IsMonitored(queueItem)
                       
            if isMonitored:
                monitoredDownloadIDs.append(queueItem['downloadId'])

        affectedItems = []
        for queueItem in queue['records']: 
            if queueItem['downloadId'] not in monitoredDownloadIDs:
                affectedItems.append(queueItem) # One downloadID may be shared by multiple queueItems. Only removes it if ALL queueitems are unmonitored

        affectedItems = await execute_checks(settingsDict, affectedItems, failType, arr, deleted_downloads, defective_tracker, privateDowloadIDs, protectedDownloadIDs, 
                                            addToBlocklist = False, 
                                            doPrivateTrackerCheck = True, 
                                            doProtectedDownloadCheck = True, 
                                            doPermittedAttemptsCheck = False)
        return len(affectedItems)
    except Exception as error:
        errorDetails(arr.name, error)
        return 0        