########### Import Libraries
import logging, verboselogs

from config.definitions import SSL_VERIFICATION, TEST_RUN
from utils.downloader import genericDownloader
logger = verboselogs.VerboseLogger(__name__)
import requests 
from src.utils.rest import rest_get, rest_post # 
import asyncio
from packaging import version

class qBittorrent(genericDownloader):
    def __init__(self, name, minVersion, url, username, password):
        
        self.username = username
        self.password = password
        self.cookie = ''

        if ( len(url) > 0 ):
            url = url.rstrip('/')+'/api/v2'
        else:
            url = 'http://' + name.lower() + ':8080/api/v2'

        super().__init__(name, url, None, username, password, minVersion)

        self.MissingFileErrorMessage = 'DownloadClientQbittorrentTorrentStateMissingFiles'
        

    async def GetProtectedAndPrivate(self, tag, ingorePrivate):
        protectedDownloadIDs = []
        privateDowloadIDs = []

        # Fetch all torrents
        qbitItems = await rest_get(self.url +'/torrents/info',params={}, cookies=self.cookie)
        # Fetch protected torrents (by tag)
        for qbitItem in qbitItems:
            if tag in qbitItem.get('tags'):
                protectedDownloadIDs.append(str.upper(qbitItem['hash']))

        # Fetch private torrents
        if ingorePrivate:
            for qbitItem in qbitItems:           
                qbitItemProperties = await rest_get(self['URL']+'/torrents/properties',params={'hash': qbitItem['hash']}, cookies=self.cookie)
                qbitItem['is_private'] = qbitItemProperties.get('is_private', None) # Adds the is_private flag to qbitItem info for simplified logging
                if qbitItemProperties.get('is_private', False):
                    privateDowloadIDs.append(str.upper(qbitItem['hash']))
        logger.debug('main/getProtectedAndPrivateFromQbit/qbitItems: %s', str([{"hash": str.upper(item["hash"]), "name": item["name"], "category": item["category"], "tags": item["tags"], "is_private": item.get("is_private", None)} for item in qbitItems]))

        return protectedDownloadIDs, privateDowloadIDs

    async def InstanceCheck(self):
        
        # Checking if qbit can be reached
        try: 
            # atempt to log in
            response = await asyncio.get_event_loop().run_in_executor(None, lambda: requests.post(self.url+'/auth/login', data={'username': self.username, 'password': self.password}, headers={'content-type': 'application/x-www-form-urlencoded'}, verify=SSL_VERIFICATION))
            if response.text == 'Fails.':
                raise ConnectionError('Login failed.')
            response.raise_for_status()
            self.cookie = {'SID': response.cookies['SID']} 

        except Exception as error:
            logger.error('!! %s Error: !!', 'qBittorrent')
            logger.error('> %s', error)
            logger.error('> Details:')
            logger.error(response.text)
            return True

        # check qBittorrent version
        qbit_version = await rest_get(self.url+'/app/version',cookies=self.cookie)
        qbit_version = qbit_version[1:] # version without _v
        if version.parse(qbit_version) < version.parse(self.minVersion):
            logger.error('-- | %s *** Error: %s ***', 'qBittorrent', 'Please update qBittorrent to at least version %s Current version: %s',self.minVersion, qbit_version)
            return True

        logger.info('OK | %s', 'qBittorrent')
        logger.debug('Current version of %s: %s', 'qBittorrent', qbit_version) 
        return False

    async def CreateProtectionTag(self, tag):
        # Creates the qBit Protection tag if not already present

        current_tags = await rest_get(self.url+'/torrents/tags',cookies=self.cookie)
        if not tag in current_tags:
            logger.info('Creating tag in qBittorrent: %s', tag)  
            if not TEST_RUN:
                await rest_post(url=self.url+'/torrents/createTags', data={'tags': tag}, headers={'content-type': 'application/x-www-form-urlencoded'}, cookies=self.cookie)

    async def GetDownloadedSize(self, queueItem):
        
        qbitInfo = await rest_get(self.url+'/torrents/info',params={'hashes': queueItem['downloadId']}, cookies=self.cookie  )

        if qbitInfo[0]['completed'] == None:
            return super().getDownloadedSize(queueItem) 
    
        return qbitInfo[0]['completed']
    


    async def IsOffline(self):
        qBitConnectionStatus = (await rest_get(self.url +'/sync/maindata', cookies=self.cookie))['server_state']['connection_status']
        return qBitConnectionStatus == 'disconnected'
    
    def IsStalled(self, queueItem):
        return queueItem['status'] == 'warning' and queueItem['errorMessage'] == 'The download is stalled with no connections'
    
    def IsMetaMissing(self, queueItem):
        return queueItem['status'] == 'queued' and queueItem['errorMessage'] == 'qBittorrent is downloading metadata'
                   