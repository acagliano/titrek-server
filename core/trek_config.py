import ssl,traceback,logging

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
	settings={}
	logger=False
	textbody_controlcodes = [ControlCodes["REGISTER"],ControlCodes["LOGIN"],ControlCodes["PING"],ControlCodes["MESSAGE"],\
						ControlCodes["DEBUG"],ControlCodes["SERVINFO"]]	
	def init(self, log):
		try:
			Config.logger=log
			with open(f'config.json', 'r') as f:
				Config.settings=json.load(f)
				Config.settings["packet-size"]=max(4096, Config.settings["packet-size"])
				Config.settings["gamedata"]="data/"
				if not SUPPORTS_SSL:
					Config.settings["ssl"]["enable"]=False
				if Config.settings["ssl"]["enable"]:
					ssl_path=Config.settings["ssl"]["path"]
					Config.ssl = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
					Config.ssl.load_cert_chain(f'{ssl_path}/fullchain.pem', f'{ssl_path}/privkey.pem')
				if Config.settings["enable-discord-link"]:
					if TrekImporter.__call__("discord"):
						formatter = logging.Formatter('%(levelname)s: %(asctime)s: %(message)s')
						discord_main=DiscordMain()
						discord_main.setFormatter(formatter)
						discord_main.setLevel(logging.INFO)
						Config.logger.addHandler(discord_main)
						
						discord_error=DiscordError()
						discord_main.setFormatter(formatter)
						discord_main.setLevel(logging.ERROR)
						Config.logger.addHandler(discord_error)
					else:
						Config.logger.log(logging.ERROR, "Error initializing DiscordHandler()"
				Config.logger.log(logging.INFO, "Server config loaded!")
		except:
			self.elog(traceback.format_exc(limit=None, chain=True))
	
	def save(self):
		try:
			with open(f"config.json", "w") as f:
				json.dump(Config.settings, f)
				self.log("Server config written!")
			return True
		except:
			self.elog(traceback.format_exc(limit=None, chain=True))
			return False
