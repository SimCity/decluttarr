########### Import Libraries
import logging, verboselogs

########### Import Libraries
import logging, verboselogs

from config.definitions import SSL_VERIFICATION
logger = verboselogs.VerboseLogger(__name__)
import requests 

from src.utils.rest import rest_get, rest_post # 
import asyncio
from packaging import version
from utils.downloader import genericDownloader

REQUEST_ID = 0

class transmission(genericDownloader):
    def __init__(self, name, url, password, minVersion):

        self.password = password
        self.cookie = ''

        if ( len(url) > 0 ):
            url = url.rstrip('/')+'/api/v2/json'
        else:
            url = 'http://' + name.lower() + ':8080/api/v2/json'

        super().__init__(name, url, minVersion)


    RequiredFields = {
                "id",
                "hashString", 
                "name",
                "isPrivate",
                "sizeWhenDone",
                "leftUntilDone",
                "isFinished",
                "eta",
                "status",
                "isStalled",
                "errorString",
                "downloadedEver", 
                "labels",
                "metadataPercentComplete"
            }
    

    async def GetProtectedAndPrivate(self, tag, ingorePrivate):
        protectedDownloadIDs = []
        privateDowloadIDs = []

        # Fetch all torrents
        response = await rest_post(self.url,json=self.requestBuilder('torrent-get',[self.RequiredProperties]), headers={'X-Transmission-Session-Id': self.sessionId}, auth=(self.username, self.password))
        
        transmissionItemts = self.responseCheck(response)['torrents']
        
        # add protected torrents
        for transmissionItem in transmissionItemts:
            if tag in transmissionItem['labels']:
                protectedDownloadIDs.append(str.upper(transmissionItem['id']))

            # Add private torrents
            if not ingorePrivate and transmissionItem['isPrivate']:
                privateDowloadIDs.append(str.upper(transmissionItem['id']))
        
        return protectedDownloadIDs, privateDowloadIDs

    async def getDownloadedSize(self, queueItem):
        filter = {}
        filter['ids'] = queueItem['downloadId']
        filter['fields'] = self.RequiredFields

        response = await rest_post(self.url, json=self.requestBuilder('torrent-get',filter), headers={'X-Transmission-Session-Id': self.sessionId}, auth=(self.username, self.password) )
        transmissionItems = self.responseCheck(response)

        return transmissionItems['torrents'][0]['sizeWhenDone'] - transmissionItems['torrents'][0]['leftUntilDone'] 
    
    async def instanceCheck(self):
        # Checking if qbit can be reached
        try: 
            # atempt to log in
            fields = {'version'}
            response = await asyncio.get_event_loop().run_in_executor(None, lambda: requests.post(self.url, json=self.requestBuilder('session-get', [fields]), verify=SSL_VERIFICATION, auth=(self.username, self.password)))
            

            if response.status_code == 409:
                self.sessionId = response.Headers.GetSingleValue("X-Transmission-Session-Id")
            else:
                response.raise_for_status()


            if self.sessionId == None:
                raise ConnectionError('Did not receive a Session Id.')
          
            # verify connection by retieving version
            response = await rest_post(self.url, json=self.requestBuilder('session-get',[fields]), headers={'X-Transmission-Session-Id': self.sessionId}, auth=(self.username, self.password))
     
            if (response == None or response['Result'] != 'success'):
                raise ConnectionError('Conecting to daemon failed.')
            
        except Exception as error:
            logger.error('!! %s Error: !!', self.name.title())
            logger.error('> %s', error)
            logger.error('> Details:')
            logger.error(response['Result'])
            return True

        # check transmission version
       
        transmission_version = self.responseCheck(response)['version']
        
        transmission_version = transmission_version[1:] # version without _v
        if version.parse(transmission_version) < version.parse(self.minVersion):
            logger.error('-- | %s *** Error: %s ***', self.name.title(), 'Please update %s to at least version %s Current version: %s', self.name.title(),self.minVersion, transmission_version)
            return True

        logger.info('OK | %s', self.name.title())
        logger.debug('Current version of %s: %s', self.name.title(), transmission_version) 
        return False

    async def CreateProtectionTag(self, settingsDict):

        # Creates the transmission Protection label if not already present
    

        # transmisison currently has no documentation on how to create a label from api.
        logger.info('%s: Transmission currently has no documented process to create labels from API. Please manually create label %s', self.name.title(), settingsDict['NO_STALLED_REMOVAL_TAG']) 
        print('%s: Transmission currently has no documented process to create labels from API. Please manually create label %s', self.name.title(), settingsDict['NO_STALLED_REMOVAL_TAG']) 
        return False

        try:
            response = await rest_post(self.url,json=self.requestBuilder('label.get_labels'), headers={'X-Transmission-Session-Id': self.sessionId}, auth=(self.username, self.password))
            
            current_tags = self.responseCheck(response)

            if not settingsDict['NO_STALLED_REMOVAL_TAG'] in current_tags:
                logger.info('Creating tag in %s: %s', self.name.title(), settingsDict['NO_STALLED_REMOVAL_TAG'])  
                if not settingsDict['TEST_RUN']:
                    response = await rest_post(self.url, json=self.requestBuilder('label.add',[settingsDict['NO_STALLED_REMOVAL_TAG']]), headers={'content-type': 'application/x-www-form-urlencoded'}, headers={'X-Transmission-Session-Id': self.sessionId}, auth=(self.username, self.password))
                    self.responseCheck(response)

        except Exception as error:
            logger.error('!! %s Error: !!', self.name.title())
            logger.error('> %s', error)
            logger.error('> Details:')
            logger.error(response['error']['message'])
            return True



    

    async def requestBuilder( method, arguments=None):
        global REQUEST_ID
        REQUEST_ID += 1

        return {'tag': REQUEST_ID, 'method': method, 'arguments': arguments or []}

    def responseCheck( response):
        if ( response == None ):
            raise ConnectionError('Unexpected response')
        if (response['Result'] != 'success'):
            raise ConnectionError(response['Result'])
        return response['arguments']
    

