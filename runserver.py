import os, subprocess, traceback, importlib
from core.trek_server import *

class RunServer:
	count=0
	def __init__(self):
		return
		
	def start_server(self):
		self.server=Server(self)
		self.server.run()
		
	def stop_server(self):
		self.server.stop()
	
	def reload(self):
		try:
			clients=self.server.clients
			for module in sys.modules.values():
    				importlib.reload(module)
			self.server=Server()
			self.server.clients=clients
			self.server.run()
		except: print(traceback.format_exc(limit=None, chain=True))
		
	def attach(self, number):
		if isinstance(number, list):
			number=number[0]
		number=int(number)
		print(f"Attaching console to server {number}")
		if number>(len(self.server)-1):
			print("Error: server number undefined...")
			return
		self.commands.load_server_commands(self.server[number])
		
	def serverlist(self):
		ostring=""
		count=0
		for s in self.server.values():
			if self.commands.server==s:
				ostring+="==> "
			else: ostring+= "    "
			ostring+=f"Server #{count}, Port: {s.port}"
			count+=1
		print(ostring)
		
		
       
    
if __name__ == '__main__':
	
	server = RunServer()
	server.start_server()
