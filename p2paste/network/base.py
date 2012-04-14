# -*- coding: utf-8 -*-
'''
Networking base module
'''

import socket
import struct
import errno
import json


class ConnectionBroken(Exception):
    pass


class EventHandler(object):
    def __init__(self):
        self.handler = None

    def bind(self, handler):
        self.handler = handler

    def is_binded(self):
        return self.handler is None
    
    def __call__(self, *args, **kargs):
        self.handler(*args, **kargs)


class NetworkBase(object):

    def __init__(self, logger):
        self.logger = logger

    def nb_send(self, target_socket, outgoing_data):
        try:
            json_data = json.dumps(outgoing_data)
            value = socket.htonl(len(json_data))
            size = struct.pack('!L', value)
            target_socket.write(size)
            target_socket.write(json_data)
        except (socket.error, socket.timeout, struct.error, ValueError) as exc:
            self.logger.error('{0}: {1}'.format(exc.__class__.__name__, str(exc)))
            raise ConnectionBroken
        
    def nb_receive(self, receiver_socket):
        try:
            size = struct.calcsize('!L')
            size = receiver_socket.read(size)
            size = socket.ntohl(struct.unpack('!L', size)[0])
            self.logger.debug('Unpacked size: {0}'.format(str(size)))
            in_data = ''
            while len(in_data) < size:
                in_data += receiver_socket.read(size - len(in_data))
                
            if not in_data:
                raise ConnectionBroken
            
            self.logger.debug('Received buffer: {0}'.format(str(in_data)))
            return json.loads(in_data)
        except (socket.error, socket.timeout, struct.error, ValueError) as exc:
            self.logger.error('{0}: {1}'.format(exc.__class__.__name__, str(exc)))
            raise ConnectionBroken

    def nb_close_socket(self, target_socket):
        try:
            try:
                target_socket.shutdown(socket.SHUT_RDWR)
                self.logger.info('Socket shutdown completed.')
            except socket.error as se:
                # Connection was possibly closed by the other side, if not raise 
                if se.errno != errno.ENOTCONN:
                    raise
                self.logger.info('Unable to shutdown socket, already closed.')

            target_socket.close()
            self.logger.info('Socket closed.')
        except socket.error as se:
            self.logger.error('{0}: {1}'.format(se.__class__.__name__, str(se)))
    
