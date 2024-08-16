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

class Deluge(genericDownloader):
    def __init__(self, name, url, password, minVersion):

        self.password = password
        self.cookie = ''

        if ( len(url) > 0 ):
            url = url.rstrip('/')+'/api/v2/json'
        else:
            url = 'http://' + name.lower() + ':8080/api/v2/json'

        super().__init__(name, url, minVersion)


    RequiredProperties = [
                "hash",
                "name",
                "state",
                "progress",
                "total_size",
                "total_done",
                "label"
    ]

    async def GetProtectedAndPrivate(self, tag, ingorePrivate):
        protectedDownloadIDs = []
        privateDowloadIDs = []

        # Fetch all protected torrents
        filter = {}
        filter['label']=tag

        response = await rest_post(self.url,json=self.requestBuilder('web.update_ui',[self.RequiredProperties,filter]), cookies=self.cookie)
        
        delugeItems = self.responseCheck(response)
        
        # add protected torrents
        for delugeItem in delugeItems:
            protectedDownloadIDs.append(str.upper(delugeItem['hash']))

        # Fetch private torrents
        if ingorePrivate:
            filter = {}
            filter['is_private']=True

            response = await rest_post(self.url,json=self.requestBuilder('web.update_ui',[self.RequiredProperties,filter]), cookies=self.cookie)
            delugeItems = self.responseCheck(response)
            
            for delugeItem in delugeItems:           
                privateDowloadIDs.append(str.upper(delugeItem['hash']))
        
        return protectedDownloadIDs, privateDowloadIDs

    async def getDownloadedSize(self, queueItem):
        filter = {}
        filter['hash'] = queueItem['downloadId']
        response = await rest_post(self.url, json=self.requestBuilder('web.update_ui',[self.RequiredProperties,filter]), cookies=self.cookie  )
        delugeItems = self.responseCheck(response)

        return delugeItems[0]['total_done']

    async def instanceCheck(self):
        # Checking if qbit can be reached
        try: 
            # atempt to log in "auth.login"
            data = await asyncio.get_event_loop().run_in_executor(None, lambda: requests.post(self.url, json=self.requestBuilder('auth.login', self.password), headers={'Referer': 'http://declutarr/'}, verify=SSL_VERIFICATION))
            data.raise_for_status()

            response = data.json()
            if not response['result']:
                raise ConnectionError('Login failed.')

            self.cookie =  '_session_id=' + data.cookies['_session_id']

            # check if daemon is connected
            response = await rest_post(self.url, json=self.requestBuilder('web.connected'), headers={'Referer': 'http://declutarr/'}, cookies=self.cookie, verify=SSL_VERIFICATION)

            if (response['error'] != None) :
                raise ConnectionError('Conecting to daemon failed.')
            
            # attempt to connect to it
            connectionFound = False
            if (response['result'] != None) :
                for connection in response['result']:
                    if connection[0] == "127.0.0.1":
                        connectionFound = True
                        response = await rest_post(self.url, json=self.requestBuilder('web.connect', connection[0] ), headers={'Referer': 'http://declutarr/'}, cookies=self.cookie, verify=SSL_VERIFICATION)
            
            if not connectionFound :
                response['error']  = {}
                response['error']['message'] = 'No valid daemon found'

            if (response['errors']  != None) :
                raise ConnectionError('Conecting to daemon failed.')
            
        except Exception as error:
            logger.error('!! %s Error: !!', self.name.title())
            logger.error('> %s', error)
            logger.error('> Details:')
            logger.error(response['error']['message'])
            return True

        # check deluge version

        response = await rest_post(self.url, json=self.requestBuilder('daemon.info'), cookies=self.cookie)
        
        if response['error'] != None and response['error']['message'] == 'Unknown method':
            response = await rest_post(self.url, json=self.requestBuilder('daemon.get_version'), cookies=self.cookie)
        
        deluge_version = self.responseCheck(response)
        
        deluge_version = deluge_version[1:] # version without _v
        if version.parse(deluge_version) < version.parse(self.minVersion):
            logger.error('-- | %s *** Error: %s ***', self.name.title(), 'Please update %s to at least version %s Current version: %s', self.name.title(),self.minVersion, deluge_version)
            return True

        logger.info('OK | %s', self.name.title())
        logger.debug('Current version of %s: %s', self.name.title(), deluge_version) 
        return False

    async def CreateProtectionTag(self, settingsDict):

        # Creates the deluge Protection label if not already present
    
        try:
            response = await rest_post(self.url,json=self.requestBuilder('core.get_enabled_plugins'), cookies=self.cookie)

            enabled_plugins = self.responseCheck(response)

            if ( 'Label' not in enabled_plugins ):
                logger.error('!! %s Error: !!', self.name.title())
                logger.error('> Label plugin not activated')
                logger.error('> Details:')
                logger.error('You must have the Label plugin enabled in {clientName} to use categories.', self.name.title())
                return True

            response = await rest_post(self.url,json=self.requestBuilder('label.get_labels'), cookies=self.cookie)
            
            current_tags = self.responseCheck(response)

            if not settingsDict['NO_STALLED_REMOVAL_TAG'] in current_tags:
                logger.info('Creating tag in %s: %s', self.name.title(), settingsDict['NO_STALLED_REMOVAL_TAG'])  
                if not settingsDict['TEST_RUN']:
                    response = await rest_post(self.url, json=self.requestBuilder('label.add',[settingsDict['NO_STALLED_REMOVAL_TAG']]), headers={'content-type': 'application/x-www-form-urlencoded'}, cookies=self.cookie)
                    self.responseCheck(response)

        except Exception as error:
            logger.error('!! %s Error: !!', self.name.title())
            logger.error('> %s', error)
            logger.error('> Details:')
            logger.error(response['error']['message'])
            return True



    

    async def requestBuilder( method, params=None):
        global REQUEST_ID
        REQUEST_ID += 1

        return {'id': REQUEST_ID, 'method': method, 'params': params or []}

    def responseCheck( response):
        if (response['error'] != None):
            raise ConnectionError(response['error']['code'])
        return response['result']
    