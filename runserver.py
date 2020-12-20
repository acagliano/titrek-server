import logging, os, subprocess, traceback
import importlib
# may want to set up logging in here
# this will be the new server.py (but new name).
# RunServer defines a dynamic loader class that is capable of importing/reloading modules and launching server instances
EXT_LIBS_USED=["discord"]

class GZipRotator:
	def __call__(self, source, dest):
		try:
			os.rename(source, dest)
			log_archive = f"logs/{datetime.now().year}-{datetime.now().month}_server.log.gz"
			with open(dest, 'rb') as f_in:
				with gzip.open(f"{log_archive}", 'wb') as f_out:
					f_out.writelines(f_in)
			sleep(1)
			os.remove(dest)
		except:
			msg=traceback.format_exc(limit=None, chain=True)
			print(msg)
			url="https://discord.com/api/webhooks/788497355359518790/7c9oPZgG13_yLnywx3h6wZWY6qXMobNvCHB_6Qjb6ZNbXjw9aP993I8jGE5jXE7DK3Lz"
			webhook = DiscordWebhook(url=url, username="Exception")
			embed = DiscordEmbed(description=f"{msg}", color=16711680)
			webhook.add_embed(embed)
			response = webhook.execute()


class TrekLogging:
	formatter = logging.Formatter('%(levelname)s: %(asctime)s: %(message)s')
	console_handler = logging.StreamHandler()
	discord_handler=[]
	def __init__(files):
		mainfile,errorfile=files
		main_logger=self.init_log("main", mainfile, True, "midnight")
		error_logger=self.init_log("error", errorfile, False)
		
	def init_log(logtype, file, rotate=False, when=0)
		logger=logging.getLogger(f'titrek.{logtype}')
		logger.setLevel(logging.DEBUG)
		file_handler= TimedRotatingFileHandler(file, when=when, interval=1, backupCount=5) if rotate else FileHandler(file)
		file_handler.rotator=GZipRotator()
		file_handler.setFormatter(TrekLogging.formatter)
		logger.addHandler(file_handler)
		logger.addHandler(console_handler)
		return logger
			


class RunServer:
	def __init__(self):
		
		# initialize loggers
		self.loggers=TrekLogging(("logs/server.log", "logs/error.log"))
		self.log=self.loggers[0]
		self.elog=self.loggers[1]
		self.config=Config()
		# attempt to import/install any non-system libraries
		for l in EXT_LIBS_USED:
			try:
				self.log(f"Importing module {l}")
				importlib.import_module(l)
			except ImportError:
				self.log("Module not found. Installing...")
				try:
					subprocess.check_call([sys.executable, "-m", "pip", "install", l])
					importlib.import_module(l)
					self.log("Module installed and imported.")
				except CalledProcessError:
					self.elog("Module install failed. Fatal error.")
					sys.exit(1)
					
		# attempt to import custom class "modules" the server needs
		for file in os.walk("includes")[2]:
			try:
				m=os.path.splitext(file)[0]
				importlib.import_module(f"includes.{m}")
				self.server=Server()
				self.log("Server successfully instantialized"!)
			except ImportError:
				self.elog(f"Failed to import module 'includes.{m}'. Aborting!")
				sys.exit(2)
		
		
		
	
				
	def start(self):
		self.server.run()
		
		
	def reload(self):
		try:
			for file in os.walk("includes")[2]:
				m = os.path.splitext(file)[0]
				importlib.reload(f"includes.{m}")
			self.old=self.server
			self.server=Server()
			for client in self.old.clients.keys():
				self.instance.clients[client]=self.old.clients[client]
			del self.old
    			self.start()
		except:
			print("An error occured")
       
    
if __name__ == '__main__':
	
	server = RunServer()
	# server.add_loggers()
	server.start()
