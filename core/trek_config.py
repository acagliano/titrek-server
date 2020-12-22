import ssl
SUPPORTS_SSL=False

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
						# do stuff that we have yet to figure out
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
