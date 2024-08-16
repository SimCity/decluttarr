from src.utils.shared import (errorDetails, formattedQueueInfo, get_queue, privateTrackerCheck, protectedDownloadCheck, execute_checks, permittedAttemptsCheck, remove_download, DownloaderOffline)
import sys, os, traceback
import logging, verboselogs
logger = verboselogs.VerboseLogger(__name__)
from src.utils.downloader import *

async def remove_failed(settingsDict, arr, deleted_downloads, defective_tracker, protectedDownloadIDs, privateDowloadIDs):
    # Detects failed and triggers delete. Does not add to blocklist
    try:
        failType = 'failed'
        queue = await arr.get_queue()
        logger.debug('remove_failed/queue IN: %s', formattedQueueInfo(queue))
        if not queue: return 0
        offlineClients =  await DownloaderOffline(settingsDict)
        # Find items affected
        affectedItems = []
        for queueItem in queue['records']: 
            downloadClient = queueItem['downloadClient'] 
            if downloadClient in offlineClients or downloadClient.upper() not in settingsDict['DOWNLOADERS']:
                continue

            if 'errorMessage' in queueItem and 'status' in queueItem:
                if  settingsDict['DOWNLOADERS'][downloadClient.upper()].CheckFailed(queueItem):
                    affectedItems.append(queueItem)
                            
        affectedItems = await execute_checks(settingsDict, affectedItems, failType, arr, deleted_downloads, defective_tracker, privateDowloadIDs, protectedDownloadIDs, 
                                            addToBlocklist = False, 
                                            doPrivateTrackerCheck = True, 
                                            doProtectedDownloadCheck = True, 
                                            doPermittedAttemptsCheck = False)
        return len(affectedItems)
    except Exception as error:
        errorDetails(arr.name, error)
        return 0

