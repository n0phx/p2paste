# -*- coding: utf-8 -*-
'''
Networking server module
'''

from network.base import NetworkBase, EventHandler, ConnectionBroken
import threading
import select
import socket
import ssl


class Server(NetworkBase):
    
    connect_handler = EventHandler()
    disconnect_handler = EventHandler()
    data_handler = EventHandler()
    
    def __init__(self, logger, max_timeout, ssl_version, certificate_path, key_path):
        super(Server, self).__init__(logger)
        self.max_timeout = max_timeout
        self.ssl_version = ssl_version
        self.certificate_path = certificate_path
        self.key_path = key_path
        
        self.open_connections = dict()
        self.server_running = threading.Event()
        self.listener_stopped = threading.Event()
    
    def __call__(self):
        return self.server_socket
    
    @property
    def all_clients(self):
        return self.open_connections
    
    def send_to(self, target_socket, outgoing_data):
        self.nb_send(target_socket, outgoing_data)
        self.logger.debug('Data sent to {0} with: {1}'.format(target_socket.getpeername(), str(outgoing_data)))
    
    def receive_from(self, target_socket):
        return self.nb_receive(target_socket)
    
    def _close_socket(self, target_socket):
        self.open_connections.pop(target_socket, None)
        self.nb_close_socket(target_socket)
    
    def disconnect_client(self, target_socket):
        self._close_socket(target_socket)
        
    def _accept_new_connection(self):
        try:
            new_client_socket, address = self.server_socket.accept()
            secured_client_socket = ssl.wrap_socket(
                new_client_socket,
                server_side=True,
                certfile=self.certificate_path,
                keyfile=self.key_path,
                ssl_version=self.ssl_version
            )
            secured_client_socket.settimeout(self.max_timeout)
            self.open_connections[secured_client_socket] = address
            self.connect_handler(secured_client_socket)
        except (socket.error, socket.timeout) as se:
            self.logger.error('{0}: {1} - {2}'.format(address, se.__class__.__name__, str(se)))
            self._close_socket(secured_client_socket)

    def _process_active_sockets(self, all_active_sockets):
        for active_socket in all_active_sockets:
            if active_socket == self.server_socket:
                self._accept_new_connection()
                continue
            try:
                active_socket.settimeout(self.max_timeout)
                received_data = self.receive_from(active_socket)
                self.data_handler(active_socket, received_data)
            except ConnectionBroken as exc:
                self.logger.error('{0}: {1}'.format(exc.__class__.__name__, str(exc)))
                self.disconnect_handler(active_socket)
    
    def _listener(self):
        self.logger.info('Server listener started.')
  
        while self.server_running.is_set():
            try:
                sread, _swrite, _sexc = select.select(self.open_connections, [], [], 1)
            except (select.error, socket.error) as se:
                self.logger.error('{0}: {1}'.format(se.__class__.__name__, str(se)))
                self.server_running.clear()
                self._close_socket(self.server_socket)
                break
            except socket.timeout as st:
                self.logger.error('{0}: {1}'.format(st.__class__.__name__, str(st)))
                continue
            
            self._process_active_sockets(sread)
            
        self.logger.info('Listener stopped.')
        self.listener_stopped.set()

    def host(self, port):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.settimeout(self.max_timeout)
            self.server_socket.bind((socket.gethostbyname(socket.gethostname()), port))
            self.server_socket.listen(5)
            self.logger.debug('Server socket opened on: {0}'.format(self.server_socket.getsockname()))
        except socket.error as se:
            self.logger.error('{0}: {1}'.format(se.__class__.__name__, str(se)))
            raise ConnectionBroken
        
        self.open_connections[self.server_socket] = self.server_socket.getsockname()
        self.server_running.set()
        self.listener_thread = threading.Thread(target=self._listener)
        self.listener_thread.start()
        
        self.logger.info('Server started.')
        return self.server_socket.getsockname()

    def close_server(self):
        self.listener_stopped.clear()
        self.server_running.clear()
        self.listener_stopped.wait()

        self._close_socket(self.server_socket)
        self.logger.info('Server closed.')
