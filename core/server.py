import os,yaml,logging,sys,gzip,datetime,traceback,socket,threading,ctypes,hashlib
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from logging import Handler
from Crypto.Cipher import AES
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
import hmac
try:
	import discord_webhook
	from discord_webhook import DiscordWebhook,DiscordEmbed
except:
	pass

class Server:
	def __init__(self):
		self.start_logging()
		self.load_config()
	
	
	def start_logging(self):
		try:
			server_log = f"log/server.log"
			log_name= os.path.basename(os.path.normpath(logpath))
			self.log_handle = logging.getLogger(f"titrek.{log_name}")
			formatter = logging.Formatter('%(levelname)s: %(asctime)s: %(message)s')
			
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
		
			# set defaults
			self.log_handle.setLevel(logging.DEBUG)
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
		
	
	
# class to handle incoming client connections
class Connection:
	def __init__(self):
		return




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
