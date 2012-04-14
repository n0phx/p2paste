# -*- coding: utf-8 -*-
'''
Gui module
'''

from Tkinter import (Frame, PanedWindow, Button, Label, Entry, Text, Listbox, Scrollbar,
                     TclError,
                     NONE, BOTH, HORIZONTAL, VERTICAL, LEFT, RIGHT, TOP, BOTTOM, X, Y,
                     WORD, INSERT, END, NORMAL, DISABLED)
from ttk import Style

import re


class InvalidIPAddress(Exception):
    pass

class InvalidPortNumber(Exception):
    pass

class InvalidAddress(Exception):
    pass
    
class InvalidNickName(Exception):
    pass


class UIFrame(Frame):

    def __init__(self, min_port_number, parent):
        Frame.__init__(self, parent, background='white')  
        self.parent = parent
        self.min_port_number = min_port_number
        self._setup_ui()
    
    def _setup_ui(self):
        self.parent.title('p2paste')
        self.style = Style()
        self.style.theme_use('default')
        self.pack(fill=BOTH, expand=True)
        
        '''Fixed top-frame with connection controls'''
        frame_top = Frame(self)
        frame_top.pack(fill=X, side=TOP)
        label_nick = Label(frame_top, text="nickname:")
        label_nick.pack(side=LEFT, padx=2, pady=2)
        self.entry_nick = Entry(frame_top)
        self.entry_nick.pack(side=LEFT, padx=2)
        label_ip = Label(frame_top, text="ip:port")
        label_ip.pack(side=LEFT, padx=2, pady=2)
        self.entry_ip = Entry(frame_top)
        self.entry_ip.pack(side=LEFT, padx=2)
        self.button_connect = Button(frame_top, text="connect")
        self.button_connect.pack(side=LEFT, padx=2)
        self.button_disconnect = Button(frame_top, text="disconnect")
        self.button_disconnect.pack(side=LEFT, padx=2)
        label_port = Label(frame_top, text="port:")
        label_port.pack(side=LEFT, padx=2, pady=2)
        self.entry_port = Entry(frame_top, width=10)
        self.entry_port.pack(side=LEFT, padx=2, pady=2)
        self.button_host = Button(frame_top, text="host")
        self.button_host.pack(side=LEFT, padx=2, pady=2)
        self.button_close_server = Button(frame_top, text="close server")
        self.button_close_server.pack(side=LEFT, padx=2)
        
        '''Bottom frame with a PanedWindow, the main screen part'''
        frame_bottom = Frame(self)
        frame_bottom.pack(fill=BOTH, expand=True, side=TOP)
        pw_main = PanedWindow(frame_bottom)
        pw_main.pack(fill=BOTH, expand=True)
        
        '''Left part of screen, contains paste-text, chat-text and chat-entry'''
        frame_left = Frame(pw_main)
        pw_main.add(frame_left)
        
        '''Left-Bottom chat entry Frame with input controls'''        
        frame_chat_entry = Frame(frame_left)
        frame_chat_entry.pack(fill=X, expand=True, side=BOTTOM)
        self.entry_chat = Entry(frame_chat_entry)
        self.entry_chat.pack(fill=X, expand=True, side=LEFT, padx=2, pady=2)
        self.button_send_message = Button(frame_chat_entry, text="send")
        self.button_send_message.pack(side=LEFT, padx=2, pady=2)
        self.button_copy_chat = Button(frame_chat_entry, text="copy")
        self.button_copy_chat.pack(side=LEFT, padx=2, pady=2)
        '''Paste and chat box on the left side wrapped in a PanedWindow for resizability'''
        pw_center = PanedWindow(frame_left, orient=VERTICAL)
        pw_center.pack(fill=BOTH, expand=True, side=TOP)
        
        '''Pastebox container'''
        frame_paste = Frame(pw_center)
        '''Input controls for Pastebox'''
        frame_paste_controls = Frame(frame_paste)
        frame_paste_controls.pack(fill=X, side=BOTTOM)
        label_has_paste = Label(frame_paste_controls, text="paste permission:")
        label_has_paste.pack(side=LEFT, padx=2, pady=2)
        self.entry_has_paste = Entry(frame_paste_controls, width=8, state=DISABLED)
        self.entry_has_paste.pack(side=LEFT, padx=2, pady=2)
        self.button_request_paste = Button(frame_paste_controls, text="request")
        self.button_request_paste.pack(side=LEFT, padx=2, pady=2)
        self.button_clear_pastebox = Button(frame_paste_controls, text="clear")
        self.button_clear_pastebox.pack(side=LEFT, padx=2, pady=2)
        self.button_selectall_pastebox = Button(frame_paste_controls, text="select all")
        self.button_selectall_pastebox.pack(side=LEFT, padx=2, pady=2)
        self.button_copy_pastebox = Button(frame_paste_controls, text="copy")
        self.button_copy_pastebox.pack(side=LEFT, padx=2, pady=2)
        self.button_paste_pastebox = Button(frame_paste_controls, text="paste")
        self.button_paste_pastebox.pack(side=LEFT, padx=2, pady=2)
        self.button_send_pastebox = Button(frame_paste_controls, text="send")
        self.button_send_pastebox.pack(side=LEFT, padx=2, pady=2)
        '''Pastebox with scrollbars'''
        sbx_text_paste = Scrollbar(frame_paste, orient=HORIZONTAL)
        sbx_text_paste.pack(side=BOTTOM, fill=X, padx=2)
        sby_text_paste = Scrollbar(frame_paste)
        sby_text_paste.pack(side=RIGHT, fill=Y, pady=2)
        self.text_paste = Text(
            frame_paste,
            wrap=NONE,
            xscrollcommand=sbx_text_paste.set,
            yscrollcommand=sby_text_paste.set
        )
        self.text_paste.pack(fill=BOTH, expand=True, padx=2, pady=2)
        sbx_text_paste.config(command=self.text_paste.xview)
        sby_text_paste.config(command=self.text_paste.yview)
        pw_center.add(frame_paste)
        self.pastebox_disabled()
        
        '''Chatbox container'''
        frame_chat = Frame(pw_center)
        sby_text_chat = Scrollbar(frame_chat)
        sby_text_chat.pack(side=RIGHT, fill=Y, pady=2)
        self.text_chat = Text(
            frame_chat,
            wrap=WORD,
            state=DISABLED,
            yscrollcommand=sby_text_chat.set)
        self.text_chat.pack(fill=BOTH, expand=True, padx=2, pady=2)
        sby_text_chat.config(command=self.text_chat.yview)
        pw_center.add(frame_chat)
        
        '''Chat list on the right side'''
        frame_chatlist = Frame(pw_main)
        sby_chatlist = Scrollbar(frame_chatlist)
        sby_chatlist.pack(side=RIGHT, fill=Y, pady=2)
        self.listbox_clients = Listbox(frame_chatlist, yscrollcommand=sby_chatlist.set)
        self.listbox_clients.pack(fill=BOTH, expand=True, padx=2, pady=2)
        sby_chatlist.config(command=self.listbox_clients.yview)
        pw_main.add(frame_chatlist)

    def _message_to_chatbox(self, message):
        self.text_chat.config(state=NORMAL)
        self.text_chat.insert(END, '{0}\n'.format(message))
        self.text_chat.yview(END)                    
        self.text_chat.config(state=DISABLED)
        
    def log_error(self, message):
        message = '^ERROR: {0}'.format(message)
        self._message_to_chatbox(message)

    def log_info(self, message):
        message = '^INFO: {0}'.format(message)
        self._message_to_chatbox(message)
            
    def _validate_port(self, port):
        try:
            port = int(port)
            if not port > self.min_port_number:
                raise ValueError
            
            return port
        except ValueError:
            raise InvalidPortNumber
    
    def _validate_ip(self, ip):
        try:
            parts = ip.split('.')
            if not len(parts) == 4:
                raise ValueError
            if not all(0 <= int(item) <= 255 for item in parts):
                raise ValueError
            
            return ip
        except ValueError:
            raise InvalidIPAddress
    
    def _validate_nickname(self, nickname):
        try:
            if not re.match(r'^[A-Za-z0-9\._-]{3,}$', nickname):
                raise ValueError
            
            return nickname
        except ValueError:
            raise InvalidNickName('Nickname contains invalid characters or is less than 3 characters in length.')
        
    def get_connect_address(self):
        try:
            address_string = self.entry_ip.get()
            ip, port = address_string.split(':')
            ip = self._validate_ip(ip)
            port = self._validate_port(port)
            return (ip, port)
        except InvalidIPAddress:
            error_message = 'Invalid ip address entered.'
        except InvalidPortNumber:
            error_message = 'Invalid port number entered.'
        except ValueError:
            error_message = 'Invalid address entered.'
        raise InvalidAddress(error_message)

    def get_nickname(self):
        nickname = self.entry_nick.get()
        return self._validate_nickname(nickname)
            
    def get_host_port(self):
        port_entered = self.entry_port.get()
        return self._validate_port(port_entered)

    def get_chat_message(self):
        message = self.entry_chat.get()
        self.entry_chat.delete(0, END)
        return message
                
    def add_chat_message(self, sender, message):
        self._message_to_chatbox('{0}: {1}'.format(sender, message))
    
    def clear_client_list(self):
        self.listbox_clients.delete(0, END)
    
    def set_client_list(self, sender, client_list):
        self.clear_client_list()
        for nickname in client_list:
            self.listbox_clients.insert(END, nickname)
    
    def get_paste_data(self):
        return self.text_paste.get(1.0, END)
    
    def set_paste_data(self, sender, paste_data):
        self.text_paste.config(state=NORMAL)
        self.text_paste.delete(1.0, END)
        self.text_paste.insert(END, paste_data)
        self.text_paste.config(state=DISABLED)
        self.clear_paste_notification()

    def clear_pastebox(self, event):
        self.text_paste.delete(1.0, END)

    def selectall_pastebox(self, event):
        self.text_paste.tag_add('sel', 1.0, END)
        
    def _copy_from(self, text_element):
        text_element.config(state=NORMAL)
        try:
            text = text_element.selection_get()
        except TclError:
            return

        self.clipboard_clear()
        self.clipboard_append(text)
        text_element.config(state=DISABLED)

    def copy_chat(self, event):
        self._copy_from(self.text_chat)

    def copy_pastebox(self, event):
        self._copy_from(self.text_paste)
    
    def paste_pastebox(self, event):
        clipboard_data = self.clipboard_get()
        self.text_paste.insert(INSERT, clipboard_data)
        
    def _pastebox_permission(self, state):
        self.button_clear_pastebox.config(state=state)
        self.button_paste_pastebox.config(state=state)
        self.button_send_pastebox.config(state=state)
        self.text_paste.config(state=state)
        request_state = NORMAL if state == DISABLED else DISABLED
        self.button_request_paste.config(state=request_state)
    
    def pastebox_enabled(self, *args):
        self._pastebox_permission(NORMAL)

    def pastebox_disabled(self):
        self._pastebox_permission(DISABLED)
    
    def clear_paste_notification(self):
        self.entry_has_paste.config(state=NORMAL)
        self.entry_has_paste.delete(0, END)
        self.entry_has_paste.config(state=DISABLED)

    def set_paste_notification(self, sender, nickname):
        message = 'Paste permission granted to: {0}'.format(nickname)
        self.log_info(message)
        self.entry_has_paste.config(state=NORMAL)
        self.entry_has_paste.delete(0, END)
        self.entry_has_paste.insert(END, nickname)
        self.entry_has_paste.config(state=DISABLED)
        