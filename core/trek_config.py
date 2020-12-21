import ssl,traceback

SUPPORTS_SSL=False

class Config:
	settings={}
	textbody_controlcodes = [ControlCodes["REGISTER"],ControlCodes["LOGIN"],ControlCodes["PING"],ControlCodes["MESSAGE"],\
						ControlCodes["DEBUG"],ControlCodes["SERVINFO"]]	
	def init(self, log):
		try:
			self.logger=log
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
				self.log("Server config loaded!")
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
