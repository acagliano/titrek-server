import os, subprocess, traceback
import importlib
# may want to set up logging in here
# this will be the new server.py (but new name).
# RunServer defines a dynamic loader class that is capable of importing/reloading modules and launching server instances
EXT_LIBS_USED=["discord"]

for lib in os.walk("core")[2]:
	try:
		m=os.path.splitext(lib)[0]
		importlib.import_module(f"core.{m}")
	except ImportError:
		sys.exit("Error loading core server component. Aborting!")
			


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
		self.config=Config(self.loggers)
		self.server.run(self.config)
		
		
	def reload(self):
		try:
			for file in os.walk("includes")[2]:
				m = os.path.splitext(file)[0]
				importlib.reload(f"includes.{m}")
			self.old=self.server
			self.server=Server()
			for client in self.old.clients.keys():
				self.server.clients[client]=self.old.clients[client]
			del self.old
    			self.start()
		except:
			print("An error occured")
       
    
if __name__ == '__main__':
	
	server = RunServer()
	# server.add_loggers()
	server.start()
