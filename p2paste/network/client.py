# -*- coding: utf-8 -*-
'''
Networking client module
'''

from network.base import NetworkBase, EventHandler, ConnectionBroken
from Queue import Queue
import threading
import select
import socket
import ssl


class Client(NetworkBase):

    data_handler = EventHandler()
    
    def __init__(self, logger, max_timeout, ssl_version, certificate_path):
        super(Client, self).__init__(logger)
        self.max_timeout = max_timeout
        self.ssl_version = ssl_version
        self.certificate_path = certificate_path
        
        self.connected = threading.Event()
        self.listener_stopped = threading.Event()        
        self.received_queue = Queue()

    def __call__(self):
        return self.client_socket

    def send(self, outgoing_data):
        self.nb_send(self.client_socket, outgoing_data)
        self.logger.debug('Data sent to {0} with: {1}'.format(self.client_socket.getpeername(), str(outgoing_data)))
    
    def receive(self, receiver_socket):
        return self.nb_receive(receiver_socket)

    def _listener(self):
        while self.connected.is_set():
            try:
                sread, _swrite, _sexc = select.select([self.client_socket], [], [], 1)
            except (select.error, socket.error, socket.timeout) as exc:
                self.logger.error('{0}: {1}'.format(exc.__class__.__name__, str(exc)))
                self.connected.clear()
                break

            for active_socket in sread:
                try:
                    incoming_data = self.receive(active_socket)
                    self.data_handler(incoming_data)
                except ConnectionBroken:
                    self.connected.clear()
                    break

        self.listener_stopped.set()

    def connect(self, address):
        try:
            unsecured_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_socket = ssl.wrap_socket(
                unsecured_client_socket,
                ca_certs=self.certificate_path,
                cert_reqs=ssl.CERT_REQUIRED,
                ssl_version=self.ssl_version
            )
            self.client_socket.settimeout(self.max_timeout)
            self.client_socket.connect(address)

            self.logger.debug('Connected to: {0}'.format(self.client_socket.getpeername()))
            self.logger.debug('Cipher: {0}'.format(self.client_socket.cipher()))
            
            self.connected.set()
            self.listener_thread = threading.Thread(target=self._listener)
            self.listener_thread.start()
            self.logger.info('Connection routine successful.')
        except (socket.error, socket.timeout) as se:
            self.logger.error('{0}: {1}'.format(se.__class__.__name__, str(se)))
            raise ConnectionBroken 

    def disconnect(self):
        self.listener_stopped.clear()
        self.connected.clear()
        self.listener_stopped.wait()
        
        self.nb_close_socket(self.client_socket)
        self.logger.info('Successfully disconnected.')
                
