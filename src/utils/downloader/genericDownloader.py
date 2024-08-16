import logging, verboselogs
logger = verboselogs.VerboseLogger(__name__)

class genericDownloader:
    def __init__(self, name, url, minVersion):
        self.name = name.upper()
        self.url = url
        self.minVersion = minVersion
        self.MissingFileErrorMessage = 'The download is missing files'
  

    async def GetProtectedAndPrivate(self, tag, ingorePrivate):
        return [],[]

    async def InstanceCheck(self):
        logger.info('OK | %s', 'Generic Downloader')
        logger.debug('Current version of %s: %s', 'Generic Downloader', 'There is no spoon') 
        return False
    
    async def CreateProtectionTag(self, tag):
        logger.info('Creating tag in Generic Downloader: %s', 'This downloader is a lie') 

    async def getDownloadedSize(self, queueItem): 

        # Determines the speed of download
        downloadedSize = None

        logger.debug('getDownloadedSize/WARN: Using imprecise method to determine download increments because no direct Downloader query is possible')
        downloadedSize = queueItem['size'] - queueItem['sizeleft']


        return downloadedSize
    
    def CheckFailed(queueItem):
        return queueItem['status'] == 'failed'
    
    async def IsOffline(self):
        return False
