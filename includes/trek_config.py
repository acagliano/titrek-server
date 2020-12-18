SSL_SUPPORT=False

import traceback,json,ssl

class Config:
	def __init__(self, loggers):
		self.log=loggers[0]
		self.elog=loggers[1]
		self.dlog=loggers[2]
		self.log_archive = f"logs/{datetime.now().year}-{datetime.now().month}_server.log.gz"
		self.log(f"Log archive set to {self.log_archive}")
		self.load()
		
	def load(self)
		self.log("Loading configuration file...")
		try:
			with open("config.json", "r") as f:
				self.settings=json.load(f)
				self.settings["packet-size"]=max(4096, Config.settings["packet-size"])
				self.settings["gamedata"]="data/"
				if not SSL_SUPPORT:
					self.settings["ssl"]["enable"]=False
				self.log("Config successfully loaded!")
		except:
			self.elog(traceback.format_exc(limit=None, chain=True))
			
	def write(self):
		self.log("Writing config changes...")
		try:
			with open("config.json", "w") as f:
				json.dump(self.settings, f)
				self.log("Config write complete!"
