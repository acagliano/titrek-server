import os, subprocess, traceback, importlib
# may want to set up logging in here
# this will be the new server.py (but new name).
# RunServer defines a dynamic loader class that is capable of importing/reloading modules and launching server instances
EXT_LIBS_USED=["discord"]			


class RunServer:
	def __init__(self):
		
		self.import_from_dir("core")		# Import core components of server
		self.import_helpers()			# Import (or install/import) helpers for server
		self.import_from_dir("plugins", False)	# Import plugins
		
	def setup_loggers(self):
		self.logger=TrekLogging(("logs/server.log", "logs/error.log"))
		# import plugins
		
	def import_from_dir(self, path, reqd=True):
		for file in os.walk(path)[2]:
			try:
				lib=os.path.splitext(file)[0]
				importlib.import_module(f"{path}.{lib}")
			except ImportError:
				if reqd:
					sys.exit("Error loading core server component. Aborting!")
				else:
					pass
				
	def import_helpers(self, arr=EXT_LIBS_USED):
		for lib in arr:
			try:
				importlib.import_module(lib)
			except ImportError:
				try:
					subprocess.check_call([sys.executable, "-m", "pip", "install", lib])
					importlib.import_module(lib)
				except:
					if reqd:
						sys.exit("Error loading core server component. Aborting!")
					else:
						pass
		
		
	
				
	def start(self):
		self.config=Config(self.logger)
		self.server.run(self.config)
		
       
    
if __name__ == '__main__':
	
	server = RunServer()
	# server.add_loggers()
	server.start()
