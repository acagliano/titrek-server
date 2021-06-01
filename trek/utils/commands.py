import logging,os,json,traceback

from trek.server import *

class ConsoleException(Exception):
	pass


class TrekCommands:
		
	def __init__(self,server):
		self.server=server
		self.logger=server.logger
		try:
			self.stop=server.stop
			self.broadcast=server.broadcast
			self.list=server.list
			self.ban=server.ban
			self.kick=server.kick
#			self.reload=server.reload
#			self.save=server.save
#			self.backup=server.backup
#			self.restore=server.restore
			self.init_bare()
		except: self.logger.log(logging.ERROR, traceback.format_exc(limit=None, chain=True))
		

	def init_bare(self):
		try:
			self.commands={}
			self.commands["help"]={"permlvl":1, "run":"help", "args":None, "description":"lists all available commands","helper":""}
			self.commands["reload"]={"permlvl":2, "run":"reload", "args":False, "description":"fully reloads the selected server","helper":"reload"}
			self.commands["broadcast"]={"permlvl":1, "run":"broadcast", "args":None, "description":"sends messages to all clients", "helper":"broadcast <msg>"}
			self.commands["say"]=self.commands["broadcast"]
			self.commands["stop"]={"permlvl":2, "run":"stop", "args":False, "description":"stops the server", "helper":"stop"}
			self.commands["save"]={"permlvl":2, "run":"save", "args":False, "description":"saves the map", "helper":"save"}
			self.commands["seed"]={"permlvl":2, "run":"generator.seed_string", "args":True, "description":"reseeds the generator", "helper":"seed <string>"}
			self.commands["generate"]={"permlvl":2, "run":"generator.generate_all", "args":False, "description":"reseeds the generator", "helper":"generate"}
			self.commands["kick"]={"permlvl":1, "run":"kick", "args":True, "description":"kicks the player from the server", "helper":"kick <username|ip>"}
			self.commands["ban"]={"permlvl":1, "run":"ban", "args":True, "description":"bans the player from the server", "helper":"ban <username|ip>"}
			self.commands["banlist"]={"permlvl":1, "run":"banlist", "args":False, "description":"shows the list of banned users/ips", "helper":"banlist"}
			self.commands["backup"]={"permlvl":2, "run":"backup", "args":False, "description":"backs up entire server state to timestamped file","helper":"backup"}
			self.commands["restore"]={"permlvl":2, "run":"restore", "args":True, "description":"restores server state from timestamped file","helper":"backup <file>"}
			self.commands["list"]={"permlvl":0, "run":"list", "args":False, "description":"lists all connected sessions","helper":"list"}
			self.commands["debug"]={"permlvl":1, "run":"debug", "args":True, "description":"enables/disables server debug mode","helper":"debug enable|disable"}
			self.commands["discord"]={"permlvl":2, "run":"discord", "args":True, "description":"enables/disables discord error/firewall piping","helper":"discord enable|disable"}
			self.commands["except"]={"permlvl":1, "run":"trigger_exception", "args":False, "description":"causes a harmless testing exception","helper":"except"}
 
		except: print(traceback.format_exc(limit=None, chain=True))
				
#	def merge_command_list(self, commands):
#		try:
#			with open("commands.json", "w+") as f:
#				file_commands=json.load(f)
#				for c in commands.keys():
#					file_commands[c]=commands[c]
			
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
			if args:
				getattr(self,spec["run"])(commands[1])
			else:
				getattr(self,spec["run"])()
		except AttributeError: 
			try:
				self.logger.log(logging.ERROR, f"{command} registered, but unimplemented.")   
			except: print(traceback.format_exc(limit=None, chain=True))
		except: 
			try:
				self.logger.log(logging.ERROR, traceback.print_exc(limit=None, file=None, chain=True))
			except: self.logger.log(logging.ERROR, traceback.format_exc(limit=None, chain=True))

	def help(self, args=""):
		ostring="\n"
		if not args=="":
			if " " in args:
				args=args.split()
			else: args = [args]
			for a in args:
				if not a in self.commands:
					ostring+=f"command {a} invalid\n\n"
					continue
				cmd=self.commands[a]
				ostring+=f"[{a}]    {cmd['helper']}\n    {cmd['description']}\n\n"
		
		else:
			ostring+="######## TI-Trek Active Commands ########\n"
			ostring+="type 'help <command(s)>' for more info\n\n"
			max_len = len(max(self.commands.keys(), key=len))
			for c in self.commands.keys():
				cmd=self.commands[c]
				ostring+=f"[{c}]".ljust(max_len+4)
				ostring+=f"{cmd['helper']}\n"
		self.logger.log(logging.INFO, ostring)
	
	def trigger_exception(self):
		raise ConsoleException("Now why would one possibly want to cause an error?")

