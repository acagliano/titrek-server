import ssl,traceback,os,logging,json
from trek.utils.filter import *
SUPPORTS_SSL=False

class Config:
	def __init__(self, log):
		try:
			self.ssl=False
			self.firewall=False
			self.logger=log
			with open(f'config.json', 'r') as f:
				self.settings=json.load(f)
				self.settings["packet-size"]=max(4096, self.settings["packet-size"])
				self.settings["gamedata"]="data/"
				if not SUPPORTS_SSL:
					self.settings["ssl"]["enable"]=False
				if self.settings["ssl"]["enable"]:
					ssl_path=Config.settings["ssl"]["path"]
					self.ssl = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
					self.ssl.load_cert_chain(f'{ssl_path}/fullchain.pem', f'{ssl_path}/privkey.pem')
				if self.settings["enable-discord-link"]:
					try:
						import discord_webhook
						self.logger.enable_discord()
					except ImportError:
						self.logger.log(logging.INFO, "Package discord-webhook not installed")
						pass
				self.firewall=TrekFilter()
				self.firewall.set_logger(log)
				self.firewall.config(self.settings["firewall"])
				self.logger.log(logging.INFO, "Server config loaded!")
		except:
			self.logger.log(logging.ERROR, traceback.format_exc(limit=None, chain=True))
	
	def save(self):
		try:
			with open(f"config.json", "w") as f:
				json.dump(self.settings, f)
				self.logger.log(logging.INFO, "Server config written!")
			return True
		except:
			self.logger.log(logging.ERROR, traceback.format_exc(limit=None, chain=True))
			return False
