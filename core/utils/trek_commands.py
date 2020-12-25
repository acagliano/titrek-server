import logging,os,json,traceback

from core.trek_server import *

class ConsoleException(Exception):
	pass


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
				self.commands=json.load(f)
		except IOError:
			self.logger.log(logging.ERROR, "Failed to load commands file. Initializing bare command set.")
			self.commands={}
			self.init_bare()
		except:
			self.logger.log(logging.ERROR, traceback.format_exc(limit=None, chain=True)) 

	def init_bare(self):
		try:
			self.commands["help"]={"permlvl":1, "run":"help", "args":0, "description":"lists all available commands","helper":""}
			self.commands["broadcast"]={"permlvl":1, "run":"broadcast", "args":None, "description":"sends messages to all clients", "helper":"broadcast <msg>"}
			self.commands["say"]=self.commands["broadcast"]
			self.commands["stop"]={"permlvl":2, "run":"stop", "args":0, "description":"stops the server", "helper":"stop"}
			self.commands["save"]={"permlvl":2, "run":"save", "args":0, "description":"saves the map", "helper":"save"}
			self.commands["seed"]={"permlvl":2, "run":"generator.seed_string", "args":1, "description":"reseeds the generator", "helper":"seed <string>"}
			self.commands["generate"]={"permlvl":2, "run":"generator.generate_all", "args":0, "description":"reseeds the generator", "helper":"generate"}
			self.commands["kick"]={"permlvl":1, "run":"kick", "args":1, "description":"kicks the player from the server", "helper":"kick <username|ip>"}
			self.commands["ban"]={"permlvl":1, "run":"ban", "args":2, "description":"bans the player from the server", "helper":"ban <username|ip>"}
			self.commands["banlist"]={"permlvl":1, "run":"banlist", "args":0, "description":"shows the list of banned users/ips", "helper":"banlist"}
			self.commands["fwinfo"]={"permlvl":1, "run":"fw_printinfo", "args":0, "description":"shows firewall status", "helper":"fwinfo"}
			self.commands["backup"]={"permlvl":2, "run":"backup", "args":0, "description":"backs up entire server state to timestamped file","helper":"backup"}
			self.commands["restore"]={"permlvl":2, "run":"restore", "args":1, "description":"restores server state from timestamped file","helper":"backup <file>"}
			self.commands["list"]={"permlvl":0, "run":"list", "args":0, "description":"lists all connected sessions","helper":"list"}
			self.commands["debug"]={"permlvl":1, "run":"debug", "args":1, "description":"enables/disables server debug mode","helper":"debug enable|disable"}
			self.commands["discord"]={"permlvl":2, "run":"discord", "args":1, "description":"enables/disables discord error/firewall piping","helper":"discord enable|disable"}
			self.commands["except"]={"permlvl":1, "run":"trigger_exception", "args":0, "description":"causes a harmless testing exception","helper":"except"}
			with open("commands.json", "w+") as f:
				json.dump(self.commands, f)
		except:
			self.logger.log(logging.ERROR, traceback.format_exc(limit=None, chain=True)) 
			
	def run(self,commands, client=None):
		command=commands[0]
		if not command in self.commands.keys():
			self.logger.log(logging.INFO, "Invalid command. Type 'help' to view the command list")
			return
		spec=self.commands[command]
		args=len(commands)-1
		if not spec["args"]==None and not args==spec["args"]:
			self.logger.log(logging.INFO, f"Invalid command usage. {spec['helper']}")
			return
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
	
	def trigger_exception(self):
		raise ConsoleException("Now why would one possibly want to cause an error?")

