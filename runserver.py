import logging, os
import importlib
# may want to set up logging in here

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
		
	def reload(self):
		for file in os.walk("includes")[2]:
			try:
				m = os.path.splitext(file)[0]
				importlib.reload(f"includes.{m}")
				self.old=self.instance
				self.instance=Server()
				for client in self.old.clients.keys():
					self.instance.clients[client]=self.old.clients[client]
    				del self.old
    				self.start()
       
    
if __name__ == '__main__':
	
	server = RunServer()
	# server.add_loggers()
	server.start()
