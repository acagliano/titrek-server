import os, sys, traceback, logging, gzip, socket, threading, ctypes
import hashlib, hmac, asn1, secrets, sched, yaml, time, requests
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from core.loghelpers import GZipRotator, DiscordHandler
from Cryptodome.PublicKey import RSA
from Cryptodome.Cipher import AES
from Cryptodome.Cipher import PKCS1_OAEP
from Cryptodome.Hash import SHA256

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
        self.load_config()
        
        # initialize logging
        file_handler = TimedRotatingFileHandler(server_log, when="midnight", interval=1, backupCount=5)
        file_handler.rotator = GZipRotator()
        console_handler = logging.StreamHandler()
        handlers = [file_handler, console_handler]
        loglevel = logging.INFO
        
        if self.config["discord-logging"]["enabled"] == True:
			try:
		        from discord_webhook import DiscordWebhook, DiscordEmbed
			    logging.addLevelName(logging.IDS_WARN, "IDS Warning")
			    discord_handler = DiscordHandler()
			    discord_handler.setLevel(logging.IDS_WARN)
			    handlers.append(discord_handler)
			sexcept:
				print("Error loading discord webhook. Proceeding with this disabled.\nTo use this functionality run `python3 -m pip install discord-webhook` on your server.")
				
		if self.config["debug-mode"]: loglevel = logging.DEBUG
				
		logging.basicConfig(
			format='%(asctime)s: %(levelname)s: %(message)s',
			level=loglevel,
			handlers=handlers
		)
						
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
                logging.log(traceback.format_exc(limit=None, chain=True))

		def load_config(self):
			try:
				with open(f"server.properties", "r") as f:
					self.config = yaml.safe_load(f)
			except:
				print(traceback.format_exc(limit=None, chain=True))
				

    def prepare_rsa(self):
        rsa_key = RSA.generate(2048)
        self.rsa_privkey = rsa_key.export_key()  # export to PEM format
        self.rsa_pubkey = rsa_key.publickey().export_key()  # public key in PEM format
        

    def listener(self):
        self.clients = {}
        logging.log(logging.INFO, "Server load complete, waiting for users...")
        while self.online:
            try:
                self.sock.listen(1)
                conn, addr = self.sock.accept()
                self.clients[conn] = client = Client(conn, addr)
                thread = threading.Thread(client.listener)
                thread.start()
            except:
                logging.log(logging.ERROR, traceback.format_exc(
                    limit=None, chain=True))
            time.sleep(0.05)



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
            logging.log(
                logging.DEBUG, f"Packet ID {data[0]}: {written} bytes sent successfully.")
            return written
# return bytes_sent

        except (BrokenPipeError, OSError):
            logging.log(logging.ERROR,
                     "Send error, Packet ID {data[0]}: Connection invalid.")
        except Exception as e:
            logging.log(logging.ERROR, e)

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
            logging.log(logging.INFO, f"{self.ip}:{self.port} has disconnected.")
            del Client.server.clients[self.conn]
            return
        except:
            logging.log(logging.ERROR, traceback.format_exc(
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
                cipher = PKCS1_OAEP.new(Client.server.rsa_privkey, hashAlgo=SHA256)
				try:
					self.aes_key = cipher.decrypt(bytes(data[1:]))
					self.send_bytes(ctl + b"\x00")
				except ValueError:
					msg = f"Invalid session secret packet from {self.addr}""
					self.send_bytes(ctl + b"\x01" + msg)
									
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
            logging.log(logging.ERROR, traceback.format_exc(
                limit=None, chain=True))

    def login(self, data):
        try:
			iv = data[0:16]
			ct = data[16:-16]
			gcm_tag = data[-16:]

            # prepare CTL code
            ctl = PacketIds["LOGIN"].to_bytes(1, 'little')

            # authenticate message BEFORE decrypting. Reject immediately if fails.
            try:
				cipher = AES.new(self.aes_key, AES.MODE_GCM, nonce=iv)
				userinfo = cipher.decrypt_and_verify(ct, gcm_tag)
				credentials = userinfo.split("\0", maxsplit=2)
			except (ValueError, KeyError):
				# invalid decryption
				msg = f"Invalid login packet from {self.addr}"
				logging.log(logging.ERROR, msg)
				raise LoginError(msg)
				return

            uri = "https://tinyauth.cagstech.com/authenticate.php"
			response = requests.get(
				uri,
				params={'user':credentials[0], 'token':credentials[1]},
			)

			if response.json["success"] == True:
				# login successful
				del self.aes_key
				self.user = credentials[0]
				self.logged_in = True
				logging.log(logging.DEBUG, f"Key match for user {self.user}!")
				self.broadcast(f"{self.user} logged in!")
				self.send(ctl + b"\00")
				self.playerdir = f"data/players/{self.user}"
				self.load_player()
				return
			elif response.json["error"] == False:
				# invalid credentials
				msg = f"User:{credentials[0]}, invalid login."
				raise LoginError(msg)
			else:
				raise LoginError(response.json[["error"]])
							
		except LoginError as e:
			logging.log(logging.INFO, e)
			self.send_bytes(ctl + b"\x01" + e)   	# ctl + login resp error + msg
			self.connected = False
			return
		except: logging.log(logging.ERROR, traceback.format_exc(limit=None, chain=True))

	def load_player(self):
		try:
			with open(f"{self.playerdir}/ships.save") as f:
				self.ships = json.load(f)
		except IOError:
			self.create_player()


Server()
