import os, subprocess, traceback, importlib
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
		
for lib in EXT_LIBS_USED:
	try:
		importlib.import_module(lib)
	except ImportError:
		try:
			subprocess.check_call([sys.executable, "-m", "pip", "install", lib])
			importlib.import_module(lib)
		except:
			pass
			# we will test for this actually not working later on
			


class RunServer:
	def __init__(self):
		
		# initialize loggers
		self.logger=TrekLogging(("logs/server.log", "logs/error.log"))
		# attempt to import/install any non-system libraries
		
		# move imports of addon modules to TrekImporter. We'll invoke installations as needed
					
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
		self.config=Config(self.logger)
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
