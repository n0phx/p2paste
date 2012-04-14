# -*- coding: utf-8 -*-
'''
Main module which connects the gui with the networking module
'''

from Tkinter import Tk
from p2paste.chatserver import ChatServer
from p2paste.chatclient import ChatClient, ConnectionBroken
from p2paste.gui import UIFrame, InvalidAddress, InvalidPortNumber, InvalidNickName
from p2paste import settings

import logging
import os


class MainFrame(object):
    
    def __init__(self, client_logger, server_logger, *args, **kwargs):
        self.ui_frame = UIFrame(settings.PORT_NUMBER_BOTTOM_BOUNDARY, *args, **kwargs)
        self.bind_ui_events()
        self.logger = client_logger
        self._setup_chat_client(client_logger)
        self._setup_chat_server(server_logger)
        
    def _setup_chat_client(self, logger):
        self.chat_client = ChatClient(
            logger,
            settings.CLIENT_TIMEOUT,
            settings.SSL_VERSION,
            settings.CERTIFICATE_PATH
        )
        self.chat_client.message_handler.bind(self.ui_frame.add_chat_message)
        self.chat_client.paste_handler.bind(self.ui_frame.set_paste_data)
        self.chat_client.client_list_handler.bind(self.ui_frame.set_client_list)
        self.chat_client.paste_granted_handler.bind(self.ui_frame.pastebox_enabled)
        self.chat_client.paste_notification_handler.bind(self.ui_frame.set_paste_notification)
        
    def _setup_chat_server(self, logger):
        self.chat_server = ChatServer(
            logger,
            settings.SERVER_IDENTIFIER,
            settings.SERVER_WELCOME_MESSAGE,
            settings.ALLOWED_PASTE_TIME,
            settings.SERVER_TIMEOUT,
            settings.SSL_VERSION,
            settings.CERTIFICATE_PATH,
            settings.KEY_PATH
        )

    def bind_ui_events(self):
        self.ui_frame.button_connect.bind('<Button-1>', self.click_connect)
        self.ui_frame.button_disconnect.bind('<Button-1>', self.click_disconnect)
        self.ui_frame.button_send_message.bind('<Button-1>', self.click_chat_send)
        self.ui_frame.entry_chat.bind('<Return>', self.click_chat_send)
        self.ui_frame.button_copy_chat.bind('<Button-1>', self.ui_frame.copy_chat)
        self.ui_frame.button_request_paste.bind('<Button-1>', self.click_paste_request)
        self.ui_frame.button_send_pastebox.bind('<Button-1>', self.click_paste_send)
        self.ui_frame.button_clear_pastebox.bind('<Button-1>', self.ui_frame.clear_pastebox)
        self.ui_frame.button_selectall_pastebox.bind('<Button-1>', self.ui_frame.selectall_pastebox)
        self.ui_frame.button_paste_pastebox.bind('<Button-1>', self.ui_frame.paste_pastebox)
        self.ui_frame.button_copy_pastebox.bind('<Button-1>', self.ui_frame.copy_pastebox)
        self.ui_frame.button_host.bind('<Button-1>', self.click_host)
        self.ui_frame.button_close_server.bind('<Button-1>', self.click_close_server)

    def click_connect(self, event):
        if self.chat_client.connected:
            self.ui_frame.log_info('You are already connected.')
            return
        try:
            address = self.ui_frame.get_connect_address()
            nickname = self.ui_frame.get_nickname()
            self.chat_client.connect(address, nickname)
            self.ui_frame.log_info('Connected to {0}:{1}'.format(address[0], address[1]))
        except (InvalidAddress, InvalidNickName) as exc:
            self.ui_frame.log_error(str(exc))
        except ConnectionBroken:
            self.logger.error('Connection failed to {0}:{1}'.format(address[0], address[1]))
            self.ui_frame.log_error('Connection failed to {0}:{1}'.format(address[0], address[1]))
                     
    def click_disconnect(self, event):
        if self.chat_client.connected:
            self.chat_client.disconnect()
            self.ui_frame.clear_client_list()
        self.ui_frame.log_info('Disconnected.')
    
    def click_chat_send(self, event):
        try:
            message = self.ui_frame.get_chat_message()
            if message:
                self.chat_client.send_message(message)
                self.ui_frame.add_chat_message(self.ui_frame.get_nickname(), message)
        except ConnectionBroken:
            self.ui_frame.log_error('You are disconnected.')

    def click_paste_send(self, event):
        try:
            paste_data = self.ui_frame.get_paste_data()
            self.chat_client.send_paste(paste_data)
            self.ui_frame.clear_paste_notification()
            self.ui_frame.log_info('Paste data sent successfully.')
        except ConnectionBroken:
            self.ui_frame.log_error('You are disconnected.')
        finally:
            self.ui_frame.pastebox_disabled()

    def click_paste_request(self, event):
        try:
            self.chat_client.send_paste_request()
            self.ui_frame.log_info('Paste request sent successfully.')
        except ConnectionBroken:
            self.ui_frame.log_error('You are disconnected.')
        
    def click_host(self, event):
        if self.chat_server.running:
            self.ui_frame.log_info('Server already running.')
            return
        try:
            port = self.ui_frame.get_host_port()
        except InvalidPortNumber:
            self.ui_frame.log_info('Invalid port number specified, using default port: {0}'.format(settings.DEFAULT_PORT))
            port = settings.DEFAULT_PORT

        try:
            address = self.chat_server.host(port)
            self.ui_frame.log_info('Server running at {0}:{1}'.format(address[0], address[1]))
        except ConnectionBroken:
            self.logger.error('Hosting failed on port: {0}'.format(port))
            self.ui_frame.log_error('Hosting failed on port: {0}'.format(port))
    
    def click_close_server(self, event):
        if self.chat_server.running:
            self.chat_server.close_server()
            self.ui_frame.log_info('Server shutted down.')
        else:
            self.ui_frame.log_info('Server not running.')

    def on_close_application(self):
        self.click_disconnect(None)
        self.click_close_server(None)
        self.ui_frame.quit()


def setup_loggers():
    
    def make_log_handler(log_path, default_filename):
        try:
            log_handler = logging.FileHandler(log_path)
        except IOError:
            log_handler = logging.FileHandler(os.path.join(settings.PROJECT_ROOT, default_filename))
        log_handler.setLevel(logging.DEBUG)
        log_handler.setFormatter(
            logging.Formatter('%(asctime)-15s: by: %(threadName)s[%(thread)d] from: %(module)s/%(funcName)s/%(lineno)d %(levelname)s: %(message)s')
        )
        return log_handler

    logging.getLogger('').setLevel(logging.DEBUG)
    client_log_handler = make_log_handler(settings.CLIENT_LOG_PATH, 'client.log')
    client_logger = logging.getLogger('client_logger')
    client_logger.addHandler(client_log_handler)
    server_log_handler = make_log_handler(settings.SERVER_LOG_PATH, 'server.log')
    server_logger = logging.getLogger('server_logger')
    server_logger.addHandler(server_log_handler)
    return client_logger, server_logger


def main():
    client_logger, server_logger = setup_loggers()
    window = Tk()
    app = MainFrame(client_logger, server_logger, window)
    window.protocol('WM_DELETE_WINDOW', app.on_close_application)
    window.mainloop()  

