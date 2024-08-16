from src.utils.shared import (errorDetails, formattedQueueInfo, execute_checks)
import sys, os, traceback
import logging, verboselogs
logger = verboselogs.VerboseLogger(__name__)

async def remove_orphans(settingsDict, arr, deleted_downloads, defective_tracker, protectedDownloadIDs, privateDowloadIDs):
    # Removes downloads belonging to movies/tv shows that have been deleted in the meantime. Does not add to blocklist
    try:
        failType = 'orphan'
        full_queue = await arr.get_queue(True)
        queue = await arr.get_queue() 
        logger.debug('remove_orphans/full queue IN: %s', formattedQueueInfo(full_queue)) 
        if not full_queue: return 0 # By now the queue may be empty 
        logger.debug('remove_orphans/queue IN: %s', formattedQueueInfo(queue))

        # Find items affected
        # 1. create a list of the "known" queue items
        queueIDs = [queueItem['id'] for queueItem in queue['records']] if queue else []
        affectedItems = []
        # 2. compare all queue items against the known ones, and those that are not found are the "unknown" or "orphan" ones
        for queueItem in full_queue['records']: 
            if queueItem['id'] not in queueIDs:
                affectedItems.append(queueItem)

        affectedItems = await execute_checks(settingsDict, affectedItems, failType, arr, deleted_downloads, defective_tracker, privateDowloadIDs, protectedDownloadIDs, 
                                            addToBlocklist = False, 
                                            doPrivateTrackerCheck = True, 
                                            doProtectedDownloadCheck = True, 
                                            doPermittedAttemptsCheck = False)
        logger.debug('remove_orphans/full queue OUT: %s', formattedQueueInfo(await arr.get_queue(True)))
        return len(affectedItems)
    except Exception as error:
        errorDetails(arr.name, error)
        return 0        