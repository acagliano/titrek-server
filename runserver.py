import os, subprocess, traceback, importlib
from core.trek_server import *

class RunServer:
	count=0
	def __init__(self):
		self.server={}
		return
		
	def start_server(self):
		self.server[RunServer.count]=Server(RunServer.count)
		self.server[RunServer.count].run()
		RunServer.count+=1
		
	def stop_server(self, number):
		self.server[number].stop()
		RunServer.count-=1
		# implement when multi-instance is a thing
		
	def console_emit(self, number):
		# function where you can attach to the server number of the server you want to look in on
        	return
		
	def reload_server(self, number):
		clients=self.server[number].clients
		importlib.reload("core.trek_server")
		self.server[number]=Server()
		self.server[number].clients=clients
		self.server[number].run()
		
		
       
    
if __name__ == '__main__':
	
	server = RunServer()
	server.start_server()
