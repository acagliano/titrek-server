import os
import yaml
import logging
import sys
import gzip
import datetime
import traceback
import socket
import threading
import ctypes
import hashlib
import time
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from logging import Handler

from Cryptodome.PublicKey import RSA
from core.clients import Client
from core.logging import TrekLogger

from space import Space


class Server:
    def __init__(self):

        # no try/catch... if any of this fails, server should fail to start
        TrekLogger()
        self.load_config()
        self.prepare_rsa()
        self.load_metadata()
        self.map = Space()

        # configure socket and bind service
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(None)
        self.bindaddress = self.config["bindaddress"]
        self.port = self.config["port"]
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.bindaddress, self.port))

        # let's give Client access to server attributes, log handler, map, and metadata
        Client.server = self
        Client.log_handle = self.log_handle
        Client.meta = self.meta
        Client.map = self.map
        
        Module.log_handle = self.log_handle

        # start listener thread
        self.thread_listen = threading.Thread(target=self.listener)
        self.thread_listen.name = "ListenThread"
        self.thread_listen.start()
        self.online = True

        # start console thread
        self.start_console()

    def load_metadata(self):
        # load packet id specs
        with open(f'core/packets.spec', 'r') as f:
            self.meta["packets"] = yaml.safe_load(f)

    def start_console(self):
        # console parsing
        while self.online:
            try:
                line = input("")
                self.log(logging.INFO, f"Command issued from console: {line}")
                if " " in line:
                    line = line.split(" ", 1)
                else:
                    line = [line]
                self.commands.run(line)
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(traceback.format_exc(limit=None, chain=True))
        return

    def load_config(self):
        try:
            with open(f'server.properties', 'r') as f:
                self.config = yaml.safe_load(f)
        except:
           TrekLogger.log(logging.ERROR, traceback.format_exc(
                limit=None, chain=True))

    def prepare_rsa(self):
        try:
            self.rsa_privkey = RSA.generate(2048)
			self.rsa_pubkey = self.rsa_privkey.publickey().exportKey('DER')
        except:
            TrekLogger.log(logging.ERROR, traceback.format_exc(
                limit=None, chain=True))

    def listener(self):
        # listens for new connections
        self.clients = {}
        self.log(logging.INFO, "Server is up and running.")
        while self.online:
            try:
                self.sock.listen(5)
                conn, addr = self.sock.accept()
                self.clients[conn] = client = Client(conn, addr, self)
                thread = threading.Thread(target=client.listener)
                thread.name = "ListenerThread"
                thread.start()
            except:
                TrekLogger.log(logging.ERROR, traceback.format_exc(
                    limit=None, chain=True))
            time.sleep(0.025)

    def broadcast(self, msg):
        # sends a message to all connected clients
        for client in self.clients:
            client.send(msg)

    def stop(self):
        try:
            self.log(logging.INFO, "Server shutdown signal received.")
            self.broadcast(f"Server shutting down in 10s.")
            self.saveall()
            time.sleep(10)
            self.online = False
            self.sock.close()
        except:
            TrekLogger.log(logging.ERROR, traceback.format_exc(limit=None, chain=True))


