
class Config:
	settings={}
	ssl=False
	log_archive = f"logs/{datetime.now().year}-{datetime.now().month}_server.log.gz"
	textbody_controlcodes = [ControlCodes["REGISTER"],ControlCodes["LOGIN"],ControlCodes["PING"],ControlCodes["MESSAGE"],\
						ControlCodes["DEBUG"],ControlCodes["SERVINFO"]]	
	def loadconfig(self):
		try:
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
		except:
			print(traceback.format_exc(limit=None, chain=True))
	
	def save(self):
		try:
			with open(f"config.json", "w") as f:
				json.dump(Config.settings, f)
			return True
		except:
			return False
