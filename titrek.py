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
from core.logging import TrekLogger

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
        #! no try/catch... if any of this fails, server should fail to start
        random.seed()
        TrekLogger()
        self.load_config()
        self.prepare_rsa()
        self.space = Space()
        self.space.load()
        self.load_graphics()

        # configure scheduler
        self.scheduled = sched.scheduler(time.time, time.sleep)

        # configure socket and bind service
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.settimeout(None)
        self.sock.bind((self.config["bindaddress"], self.config["port"]))

        # Configure server vars
        self.meta = None
        self.map = None

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
        self.thread_listen.name = "ListenThread"
        self.thread_listen.start()
        self.online = True

        # start autosave handler
        self.thread_autosave = threading.Thread(target=self.autosave_handler)
        self.thread_autosave.name = "AutoSaveHandlerThread"
        self.thread_autosave.start()

        # start console thread
        self.start_console()

    def load_graphics(self):
        return

    def autosave_handler(self):
        while self.online:
            thread = threading.Thread(target=self.space.save)
            thread.name = "SpaceSaveThread"
            thread.start()
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
                TrekLogger.log(traceback.format_exc(limit=None, chain=True))

		def load_config(self):
			try:
				with open(f"server.properties", "r") as f:
					self.config = yaml.safe_load(f)
			except:
				TrekLogger.log(logging.ERROR, traceback.format_exc(limit=None, chain=True))
				

    def prepare_rsa(self):
        rsa_key = RSA.generate(2048)
        self.rsa_privkey = rsa_key.export_key()  # export to PEM format
        self.rsa_pubkey = rsa_key.publickey().export_key()  # public key in PEM format
        

    def listener(self):
        self.clients = {}
        self.log(logging.INFO, "Server load complete, waiting for users...")
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
            time.sleep(0.05)

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
        self.channel_url = self.config["security"]["discord-alerts"]["webhook-url"]
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
                    print("put something here too")
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
            hmac_digest = hmac.digest(
                key=hmac_key.encode(), msg=data.encode(), digest="sha3_256")

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
            if not hmac.compare_digest(token_verify, privkey[:-16]):
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
