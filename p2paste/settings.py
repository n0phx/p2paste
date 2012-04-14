# -*- coding: utf-8 -*-
'''
Settings module contains all global constants
'''

import os
import ssl


PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))
SERVER_LOG_PATH = os.path.join(os.path.dirname(PROJECT_ROOT), 'logs', 'server.log')
CLIENT_LOG_PATH = os.path.join(os.path.dirname(PROJECT_ROOT), 'logs', 'client.log')
DEFAULT_PORT = 8956

PORT_NUMBER_BOTTOM_BOUNDARY = 1024
SERVER_TIMEOUT = 15
CLIENT_TIMEOUT = 10

SSL_VERSION = ssl.PROTOCOL_TLSv1
CERTIFICATE_PATH = os.path.join(os.path.dirname(PROJECT_ROOT), 'certificates', 'cert.pem')
KEY_PATH = os.path.join(os.path.dirname(PROJECT_ROOT), 'certificates', 'cert.pem')

SERVER_IDENTIFIER = "Server"
SERVER_WELCOME_MESSAGE = "Welcome to p2paste chat"

ALLOWED_PASTE_TIME = 15
