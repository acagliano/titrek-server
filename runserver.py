import logging, os
import importlib
# may want to set up logging in here
# this will be the new server.py (but new name).
# RunServer defines a dynamic loader class that is capable of importing/reloading modules and launching server instances

class RunServer:
	def __init__(self):
		for file in os.walk("includes")[2]:
			try:
				m = os.path.splitext(file)[0]
				importlib.import_module(f"includes.{m}")
				self.instance=Server()
			except:
				print(f"Failed to import module includes.{m}.\n Aborting!")
				
	def start(self):
		self.instance.run()
		
	def add_loggers(self):
		# init logging here, instead of in server
		
	def reload(self):
		try:
			for file in os.walk("includes")[2]:
				m = os.path.splitext(file)[0]
				importlib.reload(f"includes.{m}")
			self.old=self.instance
			self.instance=Server()
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
