# Shared Functions
import asyncio
import logging, verboselogs
from packaging import version
import requests 
from utils.shared import filterOutDelayedQueueItems
logger = verboselogs.VerboseLogger(__name__)
from src.utils.rest import (rest_get, rest_delete, rest_post)

class arr:
    def __init__(self, name, url, port, end_point, key, minVersion, fullQueueKey, recordType):
        
        self.name = name

        if ( len(url) == 0 ):
            url = 'http://' + name.lower() + ':' + port + end_point
        else:
            url.rstrip('/') + end_point

        self.url = url
        self.key = key
        self.minVersion = minVersion
        self.fullQueueKey = fullQueueKey
        self.recordType = recordType

    async def get_queue(self, fullQueue = False):
    # Retrieves the current queue
        params = {self.fullQueueKey,fullQueue}
        await rest_post(url=self.url+'/command', json={'name': 'RefreshMonitoredDownloads'}, headers={'X-Api-Key': self.key})
        totalRecords = (await rest_get(f'{self.url}/queue', self.key, params))['totalRecords']
        if totalRecords == 0:
            return None
        queue = await rest_get(f'{self.url}/queue', self.key, {'page': '1', 'pageSize': totalRecords}|params) 
        queue = filterOutDelayedQueueItems(queue)
        return queue

    async def remove_download(self, affectedItem, addToBlocklist, removeFromClient):
        await rest_delete(f'{self.url}/queue/{affectedItem["id"]}', self.key, {'removeFromClient': removeFromClient, 'blocklist': addToBlocklist}) 

    async def GetType(self):
        return (await rest_get(self.url+'/system/status', self.key))['instanceName']
    
    async def InstanceCheck(self, sslVerification):
        try: 
            response = await asyncio.get_event_loop().run_in_executor(None, lambda: requests.get(self.url+'/system/status', params=None, headers={'X-Api-Key': self.key}, verify=sslVerification))
            response.raise_for_status()
            response = response.json()
        except Exception as error:
            error_occured = True
            logger.error('!! %s Error: !!', self.name.title())
            logger.error('> %s', error)
            if isinstance(error, requests.exceptions.HTTPError) and error.response.status_code == 401:
                logger.error ('> Have you configured %s correctly?', self.key)

        if not error_occured:  
            # Check if network settings are pointing to the right Arr-apps
            current_app = response['appName']
            if current_app.upper() != type(self).__name__.upper():
                error_occured = True
                logger.error('!! %s Error: !!', self.name.title())                    
                logger.error('> Your %s points to a %s instance, rather than %s. Did you specify the wrong IP?', self.url, current_app, type(self).__name__)

        if not error_occured:
            # Check minimum version requirements are met
            current_version = response['version']
            if self.minVersion:
                if version.parse(current_version) < version.parse(self.minVersion):
                    error_occured = True
                    logger.error('!! %s Error: !!', self.name.title())
                    logger.error('> Please update %s to at least version %s. Current version: %s', self.name.title(), self.minVersion, current_version)
        if not error_occured:
            logger.info('OK | %s', self.name.title())     
            logger.debug('Current version of %s: %s',self. name.title(), current_version)  

    async def IsMonitored(self, queueItem):
        idString = self.recordType + 'Id'
        return(await rest_get(f'{self.url}/{self.recordType}/{str(queueItem[idString])}', self.key))['monitored'] 


#configur the specifics for reach ARR type. Due to teh type of content, there are slight variances in the names 
class sonarr:
    def __init__(self, name, url, key, minVersion):
        super().__init__(name, url, '8989', '/api/v3', key, minVersion, 'includeUnknownSeriesItems', 'episode')

class radarr:
    def __init__(self, name, url, key, minVersion):
        super().__init__(name, url, '7878', '/api/v3', key, minVersion, 'includeUnknownMovieItems', 'movie')

class lidarr:
    def __init__(self, name, url, key, minVersion):
        super().__init__(name, url, '8686', '/api/v1', key, minVersion, 'includeUnknownArtistItems', 'album')
    
class readarr:
    def __init__(self, name, url, key, minVersion):
        super().__init__(name, url, '8787', '/api/v1', key, minVersion, 'includeUnknownAuthorItems', 'book')
    
class whisparr:
    def __init__(self, name, url, key, minVersion):
        super().__init__(name, url, '6969', '/api/v3', key, minVersion, 'includeUnknownSeriesItems', 'episode')

