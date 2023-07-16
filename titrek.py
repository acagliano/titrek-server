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
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from logging import Handler
from Cryptodome.PublicKey import RSA
from Cryptodome.Cipher import AES
from Cryptodome.Cipher import PKCS1_OAEP
from Cryptodome.Hash import SHA256
import hmac
import asn1
import time
from discord_webhook import DiscordWebhook, DiscordEmbed
import sched
import secrets

from space import *

logging.IDS_WARN = 60

PacketIds = {
    "RSA_SETUP": 0x03,
    "AES_SECRET_ACK": 0x04,
    "LOGIN": 0x05,
    "LOAD_SHIP": 0x10,
    "GFXCACHE_INIT": 0xe0,
    "GFXCACHE_LOAD": 0xe1,
    "GFXCACHE_DONE": 0xe2,
    "PING_SERVER": 0xfc,
    "MESSAGE": 0xfd
}


# Server class for main functionality
######################################
class Server:
    ######################################
    def __init__(self):
        # initiate core stuff
        # ! no try/catch... if any of this fails, server should fail to start
        random.seed()
        self.load_config()
        self.start_logging()
        self.prepare_rsa()
        self.space = Space()
        self.load_graphics()

        # configure scheduler
        self.scheduled = sched.scheduler(time.time, time.sleep)

        # configure socket and bind service
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.settimeout(None)
        self.sock.bind(self.config["bindaddress"], self.config["port"])

        # lets give Client global access to server attributes so i don't have to
        # pass it to each dang client
        Client.server = self
        Client.log_handle = self.log_handle
        Client.meta = self.meta
        Client.packets = Client.meta["packets"]
        Client.config = Client.server.config
        Client.map = self.map

        # start listener thread
        self.thread_listen = threading.Thread(target=self.listener)
        self.thread_listen.start()
        self.online = True

        # start autosave handler
        threading.Thread(target=self.autosave_handler).start()

        # start console thread
        self.start_console()

    def load_graphics(self):
        return

    def autosave(self):
        while self.online:
            threading.Thread(target=self.space.save).start()
            time.sleep(600)

    def start_console(self):
        # parse console
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
                self.log(traceback.format_exc(limit=None, chain=True))

    def start_logging(self):
        os.makedirs("logs", exist_ok=True)
        server_log = f"logs/server-{round(time.time())}.log"
        log_name = os.path.basename(os.path.normpath(server_log))
        self.log_handle = logging.getLogger(f"titrek.{log_name}")
        formatter = logging.Formatter(
            '%(asctime)s: %(levelname)s: %(message)s')

        # set handler for output to logfile
        file_handler = TimedRotatingFileHandler(
            server_log, when="midnight", interval=1, backupCount=5)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        file_handler.rotator = GZipRotator()
        self.log_handle.addHandler(file_handler)

        # set handler for stream to console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.log_handle.addHandler(console_handler)

        if self.config["debug-mode"] == True:
            self.log_handle.setLevel(logging.DEBUG)
        else:
            self.log_handle.setLevel(logging.INFO)

        # enable Discord output for IDS warnings
        if self.config["security"]["discord-alerts"]["enable"] == True:
            try:
                logging.addLevelName(logging.IDS_WARN, "IDS Warning")
                discord_handler = DiscordHandler()
                discord_handler.setFormatter(formatter)
                discord_handler.setLevel(logging.IDS_WARN)
                self.log_handle.addHandler(discord_handler)
            except:
                print("Error loading discord webhook. Proceeding with this disabled.")

    def log(self, lvl, msg):
        self.log_handle.log(lvl, msg)

    def load_config(self):
        with open(f"server.properties", "r") as f:
            self.config = yaml.safe_load(f)
            if self.config["security"]["rsa-keylen"] not in [1024, 2048]:
                raise Exception(
                    "RSA key length invalid. Must be in range 1024-2048.")
            if self.config["security"]["aes-keylen"] not in [64, 128, 256]:
                raise Exception(
                    f"AES key length invalid. Must be 128, 192, or 256, not {self.config['security']['aes-keylen']}")

    def prepare_rsa(self):
        keylen = self.config["security"]["rsa-keylen"]
        self.rsa_privkey = RSA.generate(keylen)
        print("RSA PRIVKEY: " + self.rsa_privkey) # ! DEBUG NOT FOR PRODUCTION
        self.rsa_pubkey = self.rsa_privkey.publickey(
        ).exportKey('DER')[-5 - keylen:-5]
        print("RSA PRIVKEY: " + self.rsa_privkey) # ! DEBUG NOT FOR PRODUCTION
        if not len(self.rsa_pubkey) == keylen:
            raise Exception("Critical RSA error. Server dev is an ID10T.")

    def listener(self):
        self.clients = {}
        self.log(logging.INFO, "Server is up.")
        while self.online:
            try:
                self.sock.listen(1)
                conn, addr = self.sock.accept()
                self.clients[conn] = client = Client(conn, addr)
                thread = threading.Thread(client.listener)
                thread.start()
            except:
                self.log(logging.ERROR, traceback.format_exc(
                    limit=None, chain=True))
            time.sleep(0.01)

# supporting class for logging module
######################################


class GZipRotator:
    ######################################
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
######################################


class DiscordHandler(Handler):
    ######################################
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


class ClientDisconnect(Exception):
    pass


class PacketFilter(Exception):
    pass


class LoginError(Exception):
    pass

# Client class for user-specific fns
#####################################


class Client:
    #####################################
    count = 0
    server = None
    config = None
    log_handle = None
    meta = None
    map = None
    packets = None
    path = "data/players"

    def __init__(self, conn, addr):
        Client.count += 1
        self.conn = conn
        self.addr = addr
        self.ip = addr[0]
        self.port = addr[1]
        os.makedirs(Client.path, exist_ok=True)

    def log(self, lvl, msg):
        Client.log_handle.log(lvl, msg)

    def send_bytes(self, data):
        try:
            # catch buffer overflow
            if len(data)+3 > Client.config["packet-max"]:
                raise Exception(
                    f"Send error, Packet ID {data[0]}: Packet + size header exceeds packet max spec.")

            out = len(data).to_bytes(3, 'little')
            out += data
            written = self.conn.send(out)

            # error if written does not match input; it should
            if not written == len(data)+3:
                raise Exception(
                    f"Send error, Packet ID {data[0]}: Bytes written did not match input.")

            # if we make it this far, print debug msg
            self.log(
                logging.DEBUG, f"Packet ID {data[0]}: {written} bytes sent successfully.")
            return written
# return bytes_sent

        except (BrokenPipeError, OSError):
            self.log(logging.ERROR,
                     "Send error, Packet ID {data[0]}: Connection invalid.")
        except Exception as e:
            self.log(logging.ERROR, e)

    def listener(self):
        self.data_size = 0
        self.connected = True
        self.logged_in = False
        try:
            self.conn.settimeout(Client.config["conn-timeo"])
            while Client.server.online and self.connected:

                # read at most packet-max bytes from socket
                data = self.conn.recv(self.config["packet-max"])
                if not data:
                    break		# conn.recv returning nothing means conn closed?

                self.in_buf += data

                # if no size set, read a size from in_buf
                # then advance in_buf by 3 bytes
                if not self.data_size:
                    if len(self.in_buf) < 3:
                        continue  # if no size word, just skip back to recv()
                    self.data_size = int.from_bytes(self.in_buf[0:3], 'little')
                    self.in_buf = self.in_buf[3:]

                # if not enough bytes to read packet, then skip back to recv
                if len(self.in_buf) < self.data_size:
                    continue

                # parse packet
                self.parse_packet(self.in_buf)

                # strip packet from in_buf, set data_size back to 0
                self.in_buf = self.in_buf[self.data_size:]
                self.data_size = 0

            # if server.online False or self.connected False
            self.conn.close()
            Client.count -= 1
            raise ClientDisconnect()

        except (socket.timeout, ClientDisconnect):
            self.log(logging.INFO, f"{self.ip}:{self.port} has disconnected.")
            del Client.server.clients[self.conn]
            return
        except:
            self.log(logging.ERROR, traceback.format_exc(
                limit=None, chain=True))

    def parse_packet(self, data):
        try:
            if data[0] == PacketIds["RSA_SETUP"]:
                # send calculator the server instance RSA public key
                ctl = PacketIds["RSA_SETUP"].to_bytes(1, 'little')
                self.send_bytes(ctl + Client.server.rsa_pubkey)
            elif data[0] == PacketIds["AES_SECRET_ACK"]:
                # decrypt the secrets for AES and HMAC, then tell calc ready for login
                ctl = PacketIds["AES_SECRET_ACK"].to_bytes(1, 'little')
                cipher = PKCS1_OAEP.new(
                    Client.server.rsa_privkey, hashAlgo=SHA256)
                data_decrypted = cipher.decrypt(bytes(data[1:]))
                self.aes_key = data_decrypted[0:32]
                self.hmac_key = data_decrypted[32:]
                self.send_bytes(ctl)
            elif data[0] == PacketIds["LOGIN"]:
                self.login(data)
            elif self.logged_in == True:
                if data[0] == PacketIds["GFXCACHE_INIT"]:
                    print("Put something here")
                elif data[0] == PacketIds["GFXCACHE_LOAD"]:
                    print("put something here")
                elif data[0] == PacketIds["GFXCACHE_DONE"]:
                    print("put something here")
        except:
            self.log(logging.ERROR, traceback.format_exc(
                limit=None, chain=True))

    def login(self, data):
        try:
            # decrypt login token, authenticate hmac
            iv = data[0:16]
            ct = data[16:-32]
            auth = data[-32:]

            # prepare CTL code
            ctl = PacketIds["LOGIN"].to_bytes(1, 'little')

            # authenticate message BEFORE decrypting. Reject immediately if fails.
            hmac_verify = hmac.HMAC(self.hmac_key, iv +
                                   ct, hashlib.sha256).digest()
            hmac_key = secrets.token_hex(16)
            hmac_digest = hmac.digest(key=hmac_key.encode(), msg=data.encode(), digest="sha3_256")

            if not hmac.compare_digest(hmac_digest, hmac_verify):
                raise LoginError("HMAC validation error")

            cipher = AES.new(self.aes_key, AES.MODE_CTR,
                             nonce=iv[:8], initial_value=iv[8:])
            credentials = cipher.decrypt(ct)
            token = credentials[:64]
            username = credentials[64:]

            target_dir = f"{Client.path}/{username}"
            pem_file = f"{target_dir}/privkey.pem"
            with open(pem_file, "rb") as f:
                privkey = f.read()
            token_verify = hashlib.pbkdf2_hmac(
                'sha256', token, privkey[-16], 1000, dklen=64)
            if not hmac_compare_digest(token_verify, privkey[:-16]):
                raise LoginError("Pubkey invalid.")

            self.user = username
            self.logged_in = True
            self.log(logging.DEBUG, f"Key match for user {self.user}!")
            self.broadcast(f"{self.user} logged in!")
            self.send(ctl + b"\00")
            self.playerdir = f"{Client.path}/{self.user}"
            self.playerfile = f"{self.playerdir}/player.json"
            self.shipfile = f"{self.playerdir}/ships.json"
            self.load_player()
            return

        except LoginError as e:
            self.send_bytes(ctl + b"\x01" + e)
            self.log(logging.ERROR, "Host " + str(self.ip) + ":" +
                     str(self.port) + " failed to login, " + str(e) + ".")
            return
        except IOError:
            self.send_bytes(ctl + b"\x01Unable to read private key.")
            self.log(logging.ERROR, "Unable to read private key.")
            return


Server()
