from src.utils.shared import (errorDetails, formattedQueueInfo, get_queue, privateTrackerCheck, protectedDownloadCheck, execute_checks, permittedAttemptsCheck, remove_download, DownloaderOffline)
import sys, os, traceback
import logging, verboselogs
from src.utils.rest import (rest_get)
logger = verboselogs.VerboseLogger(__name__)
from src.utils.downloader import qbittorrent

async def remove_slow(settingsDict, arr, deleted_downloads, defective_tracker, protectedDownloadIDs, privateDowloadIDs, download_sizes_tracker):
    # Detects slow downloads and triggers delete. Adds to blocklist
    try:
        failType = 'slow'
        queue = await arr.get_queue()
        logger.debug('remove_slow/queue IN: %s', formattedQueueInfo(queue))
        if not queue: return 0
        offlineClients =  await DownloaderOffline(settingsDict)
        # Find items affected
        affectedItems = []
        alreadyCheckedDownloadIDs = []
        for queueItem in queue['records']:
            if 'downloadId' in queueItem and 'size' in queueItem and 'sizeleft' in queueItem and 'status' in queueItem:
                if queueItem['downloadId'] not in alreadyCheckedDownloadIDs:
                    alreadyCheckedDownloadIDs.append(queueItem['downloadId']) # One downloadId may occur in multiple queueItems - only check once for all of them per iteration
                    if queueItem['protocol'] == 'usenet': # No need to check for speed for usenet, since there users pay for speed
                        continue

                    downloadClient = queueItem['downloadClient']  #skip unknown download client as cannot determine if disocnnected and skip if offline
                    if (downloadClient in offlineClients):
                        continue

                    if queueItem['status'] == 'downloading':
                        if queueItem['sizeleft'] == 0: # Skip items that are finished downloading but are still marked as downloading. May be the case when files are moving
                            logger.info('>>> Detected %s download that has completed downloading - skipping check (torrent files likely in process of being moved): %s',failType, queueItem['title'])    
                            continue
                        # determine if the downloaded bit on average between this and the last iteration is greater than the min threshold
                        downloadedSize, previousSize, increment, speed = await getDownloadedSize(settingsDict, queueItem, download_sizes_tracker, arr.name)
                        if queueItem['downloadId'] in download_sizes_tracker.dict and speed is not None:
                            if speed < settingsDict['MIN_DOWNLOAD_SPEED']:
                                affectedItems.append(queueItem)
                                logger.debug('remove_slow/slow speed detected: %s (Speed: %d KB/s, KB now: %s, KB previous: %s, Diff: %s, In Minutes: %s', \
                                    queueItem['title'], speed, downloadedSize, previousSize, increment, settingsDict['REMOVE_TIMER'])


        affectedItems = await execute_checks(settingsDict, affectedItems, failType, arr, deleted_downloads, defective_tracker, privateDowloadIDs, protectedDownloadIDs, 
                                            addToBlocklist = True, 
                                            doPrivateTrackerCheck = True, 
                                            doProtectedDownloadCheck = True, 
                                            doPermittedAttemptsCheck = True)
        return len(affectedItems)
    except Exception as error:
        errorDetails(arr.name, error)
        return 0

async def getDownloadedSize(settingsDict, queueItem, download_sizes_tracker, NAME):
    try:
        # Determines the speed of download
        downloadedSize = None

        downloadClient = queueItem['downloadClient']

        if( queueItem['downloadClient'] not in settingsDict['DOWNLOADERS'] ):
            downloadClient = 'GENERIC'

        # Since Sonarr/Radarr do not update the downlodedSize on realtime, if possible, fetch it directly from qBit
        downloadedSize = settingsDict['DOWNLOADERS'][downloadClient].getDownloadedSize(settingsDict, queueItem)

        if downloadedSize == None:
            logger.debug('getDownloadedSize/WARN: Using imprecise method to determine download increments because no direct Downloader query is possible')
            downloadedSize = queueItem['size'] - queueItem['sizeleft']

        if queueItem['downloadId'] in download_sizes_tracker.dict:
            previousSize = download_sizes_tracker.dict.get(queueItem['downloadId'])
            increment = downloadedSize - previousSize
            speed = round(increment / 1000 / (settingsDict['REMOVE_TIMER'] * 60),1)
        else:
            previousSize = None
            increment = None
            speed = None

        download_sizes_tracker.dict[queueItem['downloadId']] = downloadedSize     
        return downloadedSize, previousSize, increment, speed
    except Exception as error:
        errorDetails(NAME, error)
        return 
