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

from space import Space

logging.IDS_WARN = 60


class Server:
    def __init__(self):

        # no try/catch... if any of this fails, server should fail to start
        self.start_logging()
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

    def start_logging(self):
        try:
            os.makedirs("logs", exist_ok=True)
            server_log = f"logs/server.log"
            log_name = os.path.basename(os.path.normpath(logpath))
            self.log_handle = logging.getLogger(f"titrek.{log_name}")
            formatter = logging.Formatter(
                '%(asctime)s: %(levelname)s: %(message)s')

            # set handler for default messages (debug/info)
            file_handler = TimedRotatingFileHandler(
                server_log, when="midnight", interval=1, backupCount=5)
            file_handler.setFormatter(formatter)
            file_handler.setLevel(logging.DEBUG)
            file_handler_default.rotator = GZipRotator()
            self.log_handle.addHandler(file_handler)

            # set handler for stream to console
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            self.log_handle.addHandler(console_handler)

            if self.config["debug-mode"] == True:
                self.log_handle.setLevel(logging.DEBUG)
            else:
                self.log_handle.setLevel(logging.INFO)

            # enable Discord output
            if self.config["security"]["discord-alerts"]["enable"]:
                from discord_webhook import DiscordWebhook, DiscordEmbed
                logging.addLevelName(logging.IDS_WARN, "IDS WARN")
                discord_handler = DiscordHandler()
                discord_handler.setFormatter(formatter)
                discord_handler.setLevel(logging.IDS_WARN)
                self.log_handle.addHandler(discord_handler)
        except:
            print(traceback.format_exc(limit=None, chain=True))

    def log(self, lvl, msg):
        self.log_handle.log(lvl, msg)

    def load_config(self):
        try:
            with open(f'server.properties', 'r') as f:
                self.config = yaml.safe_load(f)
                if self.config["security"]["rsa_keylen"] not in range(1024, 2048):
                    self.logger.log(
                        logging.ERROR, "RSA key length invalid. Must be in range 1024-2048.")
                    sys.exit(1)
                if self.config["security"]["aes_keylen"] not in range(128, 256, 64):
                    self.logger.log(
                        logging.ERROR, "AES key length invalid. Must be 128, 192, or 256.")
                    sys.exit(1)
        except:
            self.log(logging.ERROR, traceback.format_exc(
                limit=None, chain=True))

    def prepare_rsa(self):
        try:
            keylen = self.config["security"]["rsa_keylen"]
            self.rsa_privkey = RSA.generate(keylen)
            self.rsa_pubkey = self.rsa_privkey.publickey(
            ).exportKey('DER')[-5 - keylen:-5]
            if not len(self.rsa_pubkey) == keylen:
                raise Exception(
                    "Critical RSA error. Server dev is an ID10T. Shutting down server.")
                sys.exit(1)
        except:
            self.log(logging.ERROR, traceback.format_exc(
                limit=None, chain=True))

    def listener(self):
        # listens for new connections
        self.clients = {}
        self.log(logging.INFO, "Server is up and running.")
        while self.online:
            try:
                self.sock.listen(3)
                conn, addr = self.sock.accept()
                self.clients[conn] = client = Client(conn, addr, self)
                thread = threading.Thread(target=client.listener)
                thread.name = "ListenerThread"
                thread.start()
            except:
                self.log(logging.ERROR, traceback.format_exc(
                    limit=None, chain=True))
            time.sleep(0.002)

    def broadcast(self):
        # sends a message to all connected clients
        for client in self.clients:
            client.send

    def stop(self):
        try:
            self.log(logging.INFO, "Server shutdown signal received.")
            self.broadcast(f"Server shutting down in 10s.")
            self.saveall()
            time.sleep(10)
            self.online = False
            self.sock.close()
        except:
            self.elog(traceback.format_exc(limit=None, chain=True))


# supporting class for logging module
class GZipRotator:
    def __call__(self, source, dest):
        try:
            os.rename(source, dest)
            log_archive = f"logs/{datetime.now().year}-{datetime.now().month}_server.log.gz"
            with open(dest, 'rb') as f_in:
                with gzip.open(f"{log_archive}", 'ab') as f_out:
                    f_out.writelines(f_in)
            os.remove(dest)
        except:
            pass

# supporting class for discord output


class DiscordHandler(Handler):
    def __init__(self):
        self.channel_url = f"https://discord.com/api/webhooks/{self.config['security']['discord-alerts']['channel-id']}"
        self.level = logging.IDS_WARN
        self.username = "TI-Trek IDS Warning"
        self.color = 131724
        Handler.__init__(self)

    def emit(self, record):
        if not record.levelno == self.level:
            return False
        msg = self.format(record)
        webhook = DiscordWebhook(url=self.channel_url, username=self.username)
        embed = DiscordEmbed(description=msg, color=self.color)
        webhook.add_embed(embed)
        return webhook.execute()
