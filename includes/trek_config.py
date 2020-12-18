SSL_SUPPORT=False

import traceback,json,ssl

class Config:
  def __init__(self, loggers):
    self.log=loggers[0]
    self.elog=loggers[1]
    self.dlog=loggers[2]
    self.log_archive = f"logs/{datetime.now().year}-{datetime.now().month}_server.log.gz"
    self.log(f"Log archive set to {self.log_archive}")
    self.log("Loading configuration file...")
    try:
      with open("config.json", "r") as f:
        self.settings=json.load(f)
        self.settings["packet-size"]=max(4096, Config.settings["packet-size"])
        self.settings["gamedata"]="data/"
        if SSL_SUPPORT and self.settings["ssl"]["enable"]:
          self.ssl_context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
          self.ssl_context.load_cert_chain(f"{self.settings['ssl']['path']}fullchain.pem", f"{self.settings['ssl']['path']}privkey.pem")
        self.log("Config successfully loaded!")
    except:
          self.elog(traceback.format_exc(limit=None, chain=True))

  def write(self):
    
        

	
	def save(self):
		try:
			with open(f"config.json", "w") as f:
				json.dump(Config.settings, f)
			return True
		except:
			return False
