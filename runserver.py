import os, subprocess, traceback, importlib
# may want to set up logging in here
# this will be the new server.py (but new name).
# RunServer defines a dynamic loader class that is capable of importing/reloading modules and launching server instances
EXT_LIBS_USED=["discord"]

class RunServer:
	count=0
	def __init__(self):
		
		self.import_from_dir("core")		# Import core components of server
		self.import_helpers()			# Import (or install/import) helpers for server
		self.import_from_dir("plugins", False)	# Import plugins
		
	def start_server(self):
		self.server=Server()
		self.server.run(self.config)
		
	def stop_server(self, number):
		# implement when multi-instance is a thing
		
	def console_emit(self, number):
		# function where you can attach to the server number of the server you want to look in on
		
	def reload_server(self):
		self.import_from_dir("core", True, True)
		self.import_from_dir("plugins", False, True)
		clients=self.server.clients
		self.server=Server()
		self.server.clients=clients
		self.server.run(self.config)
		
	def import_from_dir(self, path, reqd=True, reload=False):
		for file in os.walk(path)[2]:
			try:
				lib=os.path.splitext(file)[0]
				if reload==True:
					importlib.reload(f"{path}.{lib}")
				elif reload==False:
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
					pass
				
		
       
    
if __name__ == '__main__':
	
	server = RunServer()
	server.start()
