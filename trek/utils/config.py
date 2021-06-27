import ssl,traceback,os,logging,json
from trek.utils.filter import *
SUPPORTS_SSL=False

class Config:
	def __init__(self, log, server):
		try:
			self.ssl=False
			self.firewall=False
			self.logger=log
			with open(f'config.json', 'r') as f:
				self.settings=json.load(f)
				self.settings["packet-size"]=max(4096, self.settings["packet-size"])
				self.settings["gamedata"]="data/"
				if self.settings["enable-discord-link"]:
					try:
						import discord_webhook
						self.logger.enable_discord()
					except ImportError:
						self.logger.log(logging.INFO, "Package discord-webhook not installed")
						pass
				self.firewall=TrekFilter(server)
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
