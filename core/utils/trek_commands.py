import logging,os,json,traceback

from core.trek_server import *

class TrekCommands:
	def __init__(self, server, log):
		self.logger=log
		self.server=server
		self.stop=server.stop
		self.broadcast=server.broadcast
#		self.save=server.save
		self.fw_printinfo=server.fw.printinfo
#		self.backup=server.backup
#		self.restore=server.restore
		try:
			with open("commands.json") as f:
				j=json.load(f)
			self.commands=j["commands"]
		except IOError:
			self.logger.log(logging.ERROR, "Failed to load commands file")
		except:
			self.logger.log(logging.ERROR, traceback.format_exc(limit=None, chain=True)) 

	def run(self,commands, client=None):
		command=commands[0]
		if not command in self.commands.keys():
			self.logger.log(logging.INFO, "Invalid command. Type 'help' to view the command list")
			return
		spec=self.commands[command]
		args=len(commands)-1
		print(spec)
		if not args==spec["args"]:
			self.logger.log(logging.INFO, f"Invalid command usage. {spec['helper']}")
		try:
			if args>0:
				getattr(self,spec["run"])(commands[1:])
			else:
				getattr(self,spec["run"])()
		except AttributeError: self.logger.log(logging.ERROR, f"{command} registered, but unimplemented.")                    
		except: self.logger.log(logging.ERROR, traceback.print_exc(limit=None, file=None, chain=True))

	def help(self):
		ostring="\n"
		for c in self.commands.keys():
			cmd=self.commands[c]
			ostring+=f"[{c}] "
			ostring+=f"[{cmd['helper']}], "
			ostring+=f"[{cmd['description']}]\n"
		self.logger.log(logging.INFO, ostring)

	def stop(self):
		self.server.stop()
