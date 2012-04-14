# -*- coding: utf-8 -*-
'''
Packaging module
'''

import re


VALID_PACKAGES = (PKG_IDENTIFY, PKG_CLIENT_LIST, PKG_MESSAGE, PKG_PASTE, 
                  PKG_PASTE_REQUEST, PKG_PASTE_GRANTED, PKG_PASTE_NOTIFICATION) = range(7)


class ClientIdentificationFailed(Exception):
    pass

class PackageVerificationFailed(Exception):
    pass


class DataPackager(object):
    
    def __init__(self, logger):
        self.logger = logger
    
    def _pack(self, package_type, package_data):
        return dict(
            type=package_type,
            data=package_data
        )
    
    def identify_client(self, package):
        try:
            if package['type'] == PKG_IDENTIFY:
                if re.match("^[A-Za-z0-9\._-]{3,}$", package['data']):
                    return package['data']
            raise KeyError
        except KeyError:
            raise ClientIdentificationFailed
        
    def add_sender_to_package(self, package, nickname):
        package.update(sender=nickname)
        return package
        
    def process_package(self, package, sender_needed=True):
        try:
            if package['type'] in VALID_PACKAGES:
                if not sender_needed:
                    return package['type'], package['data']
                
                return package['type'], package['sender'], package['data']
            
            raise KeyError 
        except KeyError:
            raise PackageVerificationFailed
    
    def make_id_package(self, nickname):
        return self._pack(PKG_IDENTIFY, nickname)
    
    def make_message_package(self, message):
        return self._pack(PKG_MESSAGE, message)
    
    def make_paste_package(self, paste_data):
        return self._pack(PKG_PASTE, paste_data)
    
    def make_paste_request_package(self):
        return self._pack(PKG_PASTE_REQUEST, None)

    def make_paste_granted_package(self):
        return self._pack(PKG_PASTE_GRANTED, None)
    
    def make_paste_notification_package(self, nickname):
        return self._pack(PKG_PASTE_NOTIFICATION, nickname)
    
    def make_client_list_package(self, client_list):
        return self._pack(PKG_CLIENT_LIST, client_list)
    