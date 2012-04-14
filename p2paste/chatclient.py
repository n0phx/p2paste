# -*- coding: utf-8 -*-
'''
p2paste chat client
'''

from p2paste.network.client import Client, EventHandler, ConnectionBroken
from p2paste.packager import (DataPackager, PackageVerificationFailed, PKG_MESSAGE, 
                              PKG_PASTE, PKG_CLIENT_LIST, PKG_PASTE_GRANTED, PKG_PASTE_NOTIFICATION)


class ChatClient(object):

    message_handler = EventHandler()
    paste_handler = EventHandler()
    client_list_handler = EventHandler()
    paste_granted_handler = EventHandler()
    paste_notification_handler = EventHandler()
    
    def __init__(self, logger, *args):
        self.logger = logger
        self.client = Client(logger, *args)
        self.client.data_handler.bind(self.identify_package)
        self.packager = DataPackager(logger)
    
    @property
    def connected(self):
        return self.client.connected.is_set()
    
    def connect(self, address, nickname):
        self.client.connect(address)
            
        try:
            id_package = self.packager.make_id_package(nickname)
            self.client.send(id_package)
            self.logger.debug('Sent identification: {0}'.format(str(id_package)))
        except ConnectionBroken:
            self.client.disconnect()
            self.logger.info('Server rejected client identification.')
            raise
    
    def disconnect(self):
        self.client.disconnect()

    def identify_package(self, package):
        package_handlers = {
            PKG_MESSAGE: self.message_handler,
            PKG_PASTE: self.paste_handler,
            PKG_CLIENT_LIST: self.client_list_handler,
            PKG_PASTE_GRANTED: self.paste_granted_handler,
            PKG_PASTE_NOTIFICATION: self.paste_notification_handler
        }
        try:
            package_type, package_sender, package_data = self.packager.process_package(package)
            self.logger.debug('Package processed as: {0} from {1} - {2}'.format(package_type, package_sender, str(package_data)))
            handler = package_handlers[package_type]
            handler(package_sender, package_data)
            self.logger.info('Package handled successfully.')
        except PackageVerificationFailed:
            self.logger.error('Package verification failed: {0}'.format(str(package)))
                
    def send_package(self, package):
        if not self.connected:
            raise ConnectionBroken
            
        self.client.send(package)
        self.logger.debug('Package sent to {0} with: {1}'.format(self.client().getpeername(), str(package)))
        
    def send_message(self, message):    
        package = self.packager.make_message_package(message)
        self.send_package(package)
    
    def send_paste(self, paste_data):
        package = self.packager.make_paste_package(paste_data)
        self.send_package(package)

    def send_paste_request(self):
        package = self.packager.make_paste_request_package()
        self.send_package(package)
        