from src.utils.shared import (errorDetails, formattedQueueInfo, get_queue, privateTrackerCheck, protectedDownloadCheck, execute_checks, permittedAttemptsCheck, remove_download, DownloaderOffline)
import sys, os, traceback
import logging, verboselogs
logger = verboselogs.VerboseLogger(__name__)

async def remove_missing_files(settingsDict, arr, deleted_downloads, defective_tracker, protectedDownloadIDs, privateDowloadIDs):
    # Detects downloads broken because of missing files. Does not add to blocklist
    try:
        failType = 'missing files'
        queue = await arr.get_queue()
        logger.debug('remove_missing_files/queue IN: %s', formattedQueueInfo(queue))
        if not queue: return 0
        offlineClients =  await DownloaderOffline(settingsDict)
        # Find items affected
        affectedItems = []
        for queueItem in queue['records']: 
            downloadClient = queueItem['downloadClient'] 
            if (downloadClient in offlineClients or downloadClient.upper() not in settingsDict['DOWNLOADERS']) and queueItem['protocol'] == 'torrent':
                continue

            if 'status' in queueItem:
                errorMessage = settingsDict['DOWNLOADERS'][downloadClient.upper()].MissingFileErrorMessage

                # case to check for failed torrents
                if (queueItem['status'] == 'warning' and 'errorMessage' in queueItem and 
                    (queueItem['errorMessage'] == errorMessage or
                    queueItem['errorMessage'] == 'The download is missing files')):
                    affectedItems.append(queueItem)
                # case to check for failed nzb's/bad files/empty directory
                if queueItem['status'] == 'completed' and 'statusMessages' in queueItem:
                    for statusMessage in queueItem['statusMessages']:
                        if 'messages' in statusMessage:
                            for message in statusMessage['messages']:
                                if message.startswith("No files found are eligible for import in"):
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
