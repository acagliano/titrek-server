import ssl,traceback,logging
import trek_import

SUPPORTS_SSL=False

class DiscordMain(Handler):
	def emit(self, record):
		log_entry = self.format(record)
		# send out post request using module of choice

class DiscordError(Handler):
	def emit(self, record):
		log_entry = self.format(record)
		# send out post request using module of choice

class Config:
	textbody_controlcodes = [ControlCodes["REGISTER"],ControlCodes["LOGIN"],ControlCodes["PING"],ControlCodes["MESSAGE"],\
						ControlCodes["DEBUG"],ControlCodes["SERVINFO"]]	
	def init(self, log):
		try:
			self.logger=log
			with open(f'config.json', 'r') as f:
				self.settings=json.load(f)
				self.settings["packet-size"]=max(4096, self.settings["packet-size"])
				Config.settings["gamedata"]="data/"
				if not SUPPORTS_SSL:
					self.settings["ssl"]["enable"]=False
				if self.settings["ssl"]["enable"]:
					ssl_path=Config.settings["ssl"]["path"]
					self.ssl = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
					self.ssl.load_cert_chain(f'{ssl_path}/fullchain.pem', f'{ssl_path}/privkey.pem')
				if self.settings["enable-discord-link"]:
					if TrekImporter.__call__("discord"):
						formatter = logging.Formatter('%(levelname)s: %(asctime)s: %(message)s')
						discord_main=DiscordMain()
						discord_main.setFormatter(formatter)
						discord_main.setLevel(logging.INFO)
						self.logger.addHandler(discord_main)
						
						discord_error=DiscordError()
						discord_error.setFormatter(formatter)
						discord_error.setLevel(logging.ERROR)
						self.logger.addHandler(discord_error)
					else:
						self.logger.log(logging.ERROR, "Error initializing DiscordHandler()"
				self.logger.log(logging.INFO, "Server config loaded!")
		except:
			self.logger.log(logging.ERROR, traceback.format_exc(limit=None, chain=True))
	
	def save(self):
		try:
			with open(f"config.json", "w") as f:
				json.dump(Config.settings, f)
				self.log("Server config written!")
			return True
		except:
			self.logger.log(logging.ERROR, traceback.format_exc(limit=None, chain=True))
			return False
