# -*- coding: utf-8 -*-
'''
p2paste chat server
'''

from p2paste.network.server import Server, ConnectionBroken
from p2paste.packager import (ClientIdentificationFailed, PackageVerificationFailed,
                              DataPackager, PKG_PASTE_REQUEST, PKG_PASTE)
from Queue import Queue, Empty as QueueEmpty
import threading


class ChatServer(object):
    
    def __init__(self, logger, identifier, welcome_message, max_paste_time, *args):
        self.logger = logger
        self.identifier = identifier
        self.welcome_message = welcome_message
        self.max_paste_time = max_paste_time
        
        self.server = Server(logger, *args)
        self.server.connect_handler.bind(self.client_connected)
        self.server.disconnect_handler.bind(self.client_disconnected)
        self.server.data_handler.bind(self.identify_package)
        
        self.packager = DataPackager(logger)
        self.paste_requests = Queue()
        self.paste_request_processor_running = threading.Event()
        self.paste_request_received = threading.Event()
        self.paste_received = threading.Event()
        self.paste_permission_holder = None

        self.client_list = dict()
    
    @property
    def running(self):
        return self.server.server_running.is_set()
    
    def _get_client_address(self, client):
        return self.server.all_clients[client]

    def _get_client_nickname(self, client):
        return self.client_list[client]

    def _get_client_list(self):
        return filter(lambda x: x != self.identifier, self.client_list.values())
    
    def _broadcast_package(self, package, sender):
        nickname = self._get_client_nickname(sender)
        outgoing_package = self.packager.add_sender_to_package(package, nickname)
        for client in self.server.all_clients:
            if client not in [self.server(), sender]:
                try:
                    self.server.send_to(client, outgoing_package)
                except ConnectionBroken:
                    self.client_disconnected(client)
                    self.logger.error('Broadcasting to {0} failed.'.format(nickname))

    def _broadcast_client_list(self):
        client_list_package = self.packager.make_client_list_package(self._get_client_list())
        self._broadcast_package(client_list_package, self.server())
        self.logger.debug('Client list broadcasted: {0}'.format(str(client_list_package)))

    def _receive_identification(self, new_client):
        try:
            self.logger.info('Identification started.')
            id_package = self.server.receive_from(new_client)
            self.logger.debug('Identification package received: {0}'.format(str(id_package)))
            return self.packager.identify_client(id_package)
        except ConnectionBroken:
            raise ClientIdentificationFailed

    def client_connected(self, new_client):
        try:
            nickname = self._receive_identification(new_client)
            self.client_list[new_client] = nickname
        except ClientIdentificationFailed:
            self.logger.info('Client identification failed.')
            self.server.disconnect_client(new_client)
            return

        welcome_package = self.packager.make_message_package(self.welcome_message)
        welcome_package = self.packager.add_sender_to_package(welcome_package, self.identifier)
        try:
            self.server.send_to(new_client, welcome_package)
            self.logger.debug('Welcome message sent: {0}'.format(str(welcome_package)))
        except ConnectionBroken:
            self.logger.info('Welcome message sending failed, connection broken.')
            self.server.disconnect_client(new_client)
            self.client_list.pop(new_client, None)
            return

        self._broadcast_client_list()
        address = self._get_client_address(new_client)
        message = '{0} joined from {1}:{2}'.format(nickname, address[0], address[1])
        inform_package = self.packager.make_message_package(message)
        self._broadcast_package(inform_package, self.server())
        self.logger.debug(message)
        
    def client_disconnected(self, disconnected_client):
        nickname = self._get_client_nickname(disconnected_client)
        self.server.disconnect_client(disconnected_client)
        self.client_list.pop(disconnected_client, None)
        self._broadcast_client_list()

        message = '{0} left.'.format(nickname)
        inform_package = self.packager.make_message_package(message)
        self._broadcast_package(inform_package, self.server())
        self.logger.debug(message)

    def _broadcast_paste_permission(self, nickname):
        paste_permission_package = self.packager.make_paste_notification_package(nickname)
        self._broadcast_package(paste_permission_package, self.server())
        self.logger.debug('Paste permission broadcasted: {0}'.format(str(paste_permission_package)))

    def _paste_request_processor(self):
        self.logger.info('Paste request processor started.')
        while self.running:
            try:
                requester_client = self.paste_requests.get(False)
                package = self.packager.make_paste_granted_package()
                package = self.packager.add_sender_to_package(package, self.identifier)
                nickname = self._get_client_nickname(requester_client)
                try:
                    self.paste_received.clear()
                    self.paste_permission_holder = requester_client
                    self.server.send_to(requester_client, package)
                    self.logger.debug('Paste request granted to: {0} for {1}s'.format(nickname, self.max_paste_time))
                    self._broadcast_paste_permission(nickname)
                    self.paste_received.wait(self.max_paste_time)
                except ConnectionBroken:
                    self.logger.debug('Paste request permission sending failed to: {0}'.format(nickname))
            except QueueEmpty:
                self.paste_permission_holder = None
                self.paste_request_received.clear()
                self.paste_request_received.wait()

        self.paste_request_processor_running.set()

    def identify_package(self, sender_client, package):
        try:
            package_type, _package_data = self.packager.process_package(package, False)
        except PackageVerificationFailed:
            self.logger.error('Package verification failed: {0}'.format(str(package)))
            return
        
        if package_type == PKG_PASTE_REQUEST:
            self.paste_requests.put(sender_client)
            self.paste_request_received.set()
            return
        elif package_type == PKG_PASTE:
            if sender_client != self.paste_permission_holder:
                self.logger.info('This paste has timed out, and will be ignored.')
                return
            self.paste_received.set()

        self._broadcast_package(package, sender_client)

    def host(self, port):
        server_address = self.server.host(port)
        self.client_list[self.server()] = self.identifier
        paste_request_thread = threading.Thread(target=self._paste_request_processor)
        paste_request_thread.start()
        return server_address
        
    def close_server(self):
        self.paste_request_processor_running.clear()
        self.server.close_server()
        self.paste_request_received.set()
        self.paste_request_processor_running.wait()
