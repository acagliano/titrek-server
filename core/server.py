import os,yaml,logging,sys,gzip,datetime,traceback,socket,threading,ctypes,hashlib
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from logging import Handler
from Crypto.Cipher import AES
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
from core.clients import Client
import hmac

logging.IDS_WARN=60

class Server:
	def __init__(self):
		self.start_logging()
		self.load_config()
		self.prepare_rsa()
		
		# configure socket and bind service
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.settimeout(None)
		self.port = self.config["port"]
		self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.sock.bind(('', self.port))
		
		# start listener thread
		self.thread_listen = threading.Thread(target=self.listener)
		self.thread_listen.start()
		
	
	
	def start_logging(self):
		try:
			os.makedirs("logs", exist_ok=True)
			server_log = f"logs/server.log"
			log_name= os.path.basename(os.path.normpath(logpath))
			self.log_handle = logging.getLogger(f"titrek.{log_name}")
			formatter = logging.Formatter('%(asctime)s: %(levelname)s: %(message)s')
			
			# set handler for default messages (debug/info)
			file_handler = TimedRotatingFileHandler(server_log, when="midnight", interval=1, backupCount=5)
			file_handler.setFormatter(formatter)
			file_handler.setLevel(logging.DEBUG)
			file_handler_default.rotator = GZipRotator()
			self.log_handle.addHandler(file_handler)
		
			# set handler for stream to console
			console_handler = logging.StreamHandler()
			console_handler.setFormatter(formatter)
			self.log_handle.addHandler(console_handler)
			
			self.log_handle.setLevel(logging.DEBUG)
			
			# enable Discord output
			if self.config["security"]["discord-alerts"]["enable"]:
				try:
					from discord_webhook import DiscordWebhook,DiscordEmbed
					logging.addLevelName(logging.IDS_WARN, "IDS WARN")
					discord_handler=DiscordHandler()
					discord_handler.setFormatter(formatter)
					discord_handler.setLevel(logging.IDS_WARN)
					self.log_handle.addHandler(discord_handler)
				except:
					self.log(logging.ERROR, "Error initializing Discord support. Proceeding with feature disabled.")
		
			# set defaults
		except:
			print(traceback.format_exc(limit=None, chain=True))


	def log(self, lvl, msg):
		self.log_handle.log(lvl, msg)

	
	def load_config(self):
		try:
			with open(f'server.properties', 'r') as f:
				self.config = yaml.safe_load(f)
				if self.config["security"]["rsa_keylen"] not in range (1024, 2048):
					self.logger.log(logging.ERROR, "RSA key length invalid. Must be in range 1024-2048.")
					exit(1)
				if self.config["security"]["aes_keylen"] not in range (128, 256, 64):
					self.logger.log(logging.ERROR, "AES key length invalid. Must be 128, 192, or 256.")
					exit(1)
		except:
			self.log(logging.ERROR, traceback.format_exc(limit=None, chain=True))
		
		
	def prepare_rsa(self):
		try:
			keylen = self.config["security"]["rsa_keylen"]
			self.rsa_privkey = RSA.generate(keylen)
			self.rsa_pubkey = self.rsa_privkey.publickey().exportKey('DER')[-5 - keylen:-5]
			if not len(self.rsa_pubkey)==keylen:
				raise Exception("Critical RSA error. Server dev is an ID10T. Shutting down server.")
				exit(1)
		except:
			self.log(logging.ERROR, traceback.format_exc(limit=None, chain=True))
	
	
	def listener(self):
		self.online = True
		self.clients = {}
		Client.server = self
		Client.log_handle = self.log_handle
		self.log(logging.INFO, "Server is up and running.")
		while self.online:
			self.sock.listen(3)
			conn, addr = self.sock.accept()
			self.clients[conn] = client = Client(conn,addr,self)
			try:
				thread = threading.Thread(target=client.listener)
				thread.start()
			except:
				self.elog(traceback.format_exc(limit=None, chain=True))
			time.sleep(0.002)




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
		self.channel_url=f"https://discord.com/api/webhooks/{self.config['security']['discord-alerts']['channel-id']}"
		self.level=logging.IDS_WARN
		self.username="TI-Trek IDS Warning"
		self.color=131724
		Handler.__init__(self)

	def emit(self, record):
		if not record.levelno==self.level:
			return False
		msg=self.format(record)
		webhook=DiscordWebhook(url=self.channel_url,username=self.username)
		embed=DiscordEmbed(description=msg,color=self.color)
		webhook.add_embed(embed)
		return webhook.execute()
