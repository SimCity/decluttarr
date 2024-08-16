from src.utils.shared import (errorDetails, formattedQueueInfo, get_queue, privateTrackerCheck, protectedDownloadCheck, execute_checks, permittedAttemptsCheck, remove_download, DownloaderOffline)
import sys, os, traceback
import logging, verboselogs
logger = verboselogs.VerboseLogger(__name__)

async def remove_stalled(settingsDict, arr, deleted_downloads, defective_tracker, protectedDownloadIDs, privateDowloadIDs):
    # Detects stalled and triggers repeat check and subsequent delete. Adds to blocklist   
    try:
        failType = 'stalled'
        queue = await arr.get_queue()
        logger.debug('remove_stalled/queue IN: %s', formattedQueueInfo(queue))
        if not queue: return 0
        offlineClients =  await DownloaderOffline(settingsDict)
        # Find items affected
        affectedItems = []
        for queueItem in queue['records']: 
            downloadClient = queueItem['downloadClient'] 
            if (downloadClient in offlineClients or downloadClient.upper() not in settingsDict['DOWNLOADERS']) and queueItem['protocol'] == 'torrent':
                logger.warning('>>> %s is disconnected. Skipping %s queue cleaning on %s.',downloadClient.title() ,failType, arr.name)
                continue
            if 'errorMessage' in queueItem and 'status' in queueItem:
                if  settingsDict['DOWNLOADERS'][downloadClient.upper()].IsStalled(queueItem):
                    affectedItems.append(queueItem)

        affectedItems = await execute_checks(settingsDict, affectedItems, failType, arr, deleted_downloads, defective_tracker, privateDowloadIDs, protectedDownloadIDs, 
                                            addToBlocklist = True, 
                                            doPrivateTrackerCheck = True, 
                                            doProtectedDownloadCheck = True, 
                                            doPermittedAttemptsCheck = True)
        return len(affectedItems)
    except Exception as error:
        errorDetails(arr.name, error)
        return 0
