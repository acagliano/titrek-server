import os, subprocess, traceback, importlib
import core.trek_server
# may want to set up logging in here
# this will be the new server.py (but new name).
# RunServer defines a dynamic loader class that is capable of importing/reloading modules and launching server instances

class RunServer:
	count=0
	def __init__(self):
		return
		
	def start_server(self):
		self.server=Server()
		self.server.run(self.config)
		
	def stop_server(self, number):
		# implement when multi-instance is a thing
		
	def console_emit(self, number):
		# function where you can attach to the server number of the server you want to look in on
		
	def reload_server(self):
		clients=self.server.clients
		importlib.reload("core.trek_server")
		self.server=Server()
		self.server.clients=clients
		self.server.run(self.config)
		
		
       
    
if __name__ == '__main__':
	
	server = RunServer()
	server.start_server()
