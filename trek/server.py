import socket,threading,ctypes,hashlib,json,os,sys,time,math,ssl,traceback,subprocess,logging,gzip,re,ipaddress
import requests

from trek.utils.logging import *
from trek.utils.filter import *
from trek.utils.modules import *
from trek.utils.config import *
from trek.utils.commands import *
from trek.math.generate import *

from trek.codes import *
from trek.clients import *
from trek.space import *


class Server:
	def __init__(self):
		self.server_root=""
		for directory in [
			self.server_root,
			f"{self.server_root}logs",
			f"{self.server_root}cache",
			f"{self.server_root}bans"]:
			try:
				os.makedirs(directory)
			except:
				pass
		try:
			self.setup_loggers()
			self.config=Config(self.logger, self)
			self.loadbans()
#			self.init_binaries()
			self.fw=self.config.firewall
			self.generator = Generator()
			self.space = Space(self.server_root, self.logger, self.config.settings["space"])
			self.modules=TrekModules("data/modules/")
			self.fetch_required()
		
			self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)         # Create a socket object
			self.sock.settimeout(None)
			self.port = self.config.settings["port"]      # Reserve a port for your service. Default + instance num
			self.clients = {}
			self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			self.sock.bind(('', self.port))                 # Now wait for client connection.
			self.commands=TrekCommands(self)
		except:
			self.elog(traceback.format_exc(limit=None, chain=True))

	
	def fetch_required():
		try:
			target_version = self.config.settings["client-required"]
			#verify not earlier than 0.0.104
			tva = target_version.split(".")
			if not (tva[0] >= 0 and tva[1]>=0 and tva[2]>=104):
				self.elog("Indicated client version too old. Setting to minimum allowed.")
				target_version = "0.0.104"
			target_url = f"https://titrek.us/common/downloads/prgm/{target_version}/TITREK.bin"
			wget.download(target_url, '/home/services/trek/server/data/bins/TITREK.bin')
		except:
			self.elog(traceback.format_exc(limit=None, chain=True))
			
	
	def loadbans(self):
		try:
			with open("bans.txt") as f:
				self.bans=f.readlines()
		except:
			self.bans=[]
			
			
	def setup_loggers(self):
		self.logger=TrekLogging(f"{self.server_root}logs/")
						 
	def init_binaries(self):
		try:
			os.makedirs("bin/convimg")
			os.system("cd bin && git clone https://github.com/mateoconlechuga/convimg")
			os.system("cd bin/convimg && git submodule update --init --recursive && make")
			self.log("convimg sourced and built")
		except:
			self.log("convimg exists! skipping!")
		try:
			os.makedirs("bin/convbin")
			os.system("cd bin && https://github.com/mateoconlechuga/convbin")
			os.system("cd bin/convbin && git submodule update --init --recursive && make")
			self.log("convbin sourced and built")
		except:
			self.log("convbin exists! skipping!")
		try:
			if not path.exists("bin/update-bins"):
				exec_string="#!/bin/sh\n\ncd bin/convimg\ngit pull\nmake\n\ncd ../convbin\ngit pull\nmake\nexit 0"
				with open("bin/update-bins", "w+") as f:
					f.write(exec_string)
					self.log("update script generated")
				os.chmod("bin/update-bins", 0o774)
		except:
			self.log("Error creating update script")
                                       	
	def run(self):
		try:
			self.online = True
			self.writeinfo()
			self.threads = [threading.Thread(target=self.autoSaveHandler)]
			self.threads[0].start()
			self.main_thread = threading.Thread(target=self.main)
			self.main_thread.start()
			self.log(f"Server running on port {self.config.settings['port']}")
			self.console_emit()
		except:
			self.elog(traceback.format_exc(limit=None, chain=True))

			
#	def banlist(self):
#		print("[BANNED USERS]")
#		for b in Config.banned_users:
#			print(b)
#		print("[BANNED IPS]")
#		for b in Config.banned_ips:
#			print(b)

	def log(self,*args,**kwargs):
		self.logger.log(logging.INFO, *args, **kwargs)
	
	def elog(self,*args,**kwargs):
		self.logger.log(logging.ERROR, *args, **kwargs)
		
	def dlog(self,*args,**kwargs):
		self.logger.log(logging.DEBUG, *args, **kwargs)
		
	def broadcast(self,msg,sender="Server"):
		if type(msg) is list:
			msg = " ".join(msg)
		for conn in self.clients.keys():
			client = self.clients[conn]
			client.send([ControlCodes["MESSAGE"]]+list(bytes(sender+": "+msg+'\0', 'UTF-8')))
	
	def main(self):
		self.broadcast(f"Server Online!")
		while self.online:
			self.sock.listen(1)
			conn, addr = self.sock.accept()
			#if addr[0] in Config.banned_ips:
			#	self.log(f"Connection from {addr} rejected.")
			#	conn.close()
			#	continue
			self.clients[conn] = client = Client(conn,addr,self)
			try:
				thread = threading.Thread(target=client.handle_connection)
				self.threads.append(thread)
				thread.start()
				self.writeinfo()
			except:
				self.elog(traceback.format_exc(limit=None, chain=True))
			time.sleep(0.002)

	def writeinfo(self):
		versionbuild = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode(sys.stdout.encoding).strip()
		version = f"2.01.{versionbuild}"
		delim="."
		
		with open("servinfo.json","w") as f:
			servinfo={"server":{
				"version": version,
				"numclients":len(self.clients),
				"minversion":delim.join([str(item) for item in self.config.settings["min-client"]]),
				"max_clients":self.config.settings["max-players"],
				"online":self.online}}
			json.dump(servinfo, f)
			
	def autoSaveHandler(self):
		last_save_time = start_time = time.time()
		while self.online:
			cur_time = time.time()
			if (cur_time-last_save_time)>=600:
				last_save_time = time.time()
				self.log("Autosaving...")
				threading.Thread(target=self.space.save, ).start()
			time.sleep(60)


	def stop(self):
		try:
			self.log("Shutting down.")
			self.space.save()
			self.broadcast(f"server shutting down in 10s")
			time.sleep(10)
			for client in self.clients.keys():
				self.clients[client].disconnect()
				time.sleep(.05)
			self.clients.clear()
			self.online = False
			self.writeinfo()
			self.sock.close()
		except:
			self.elog(traceback.format_exc(limit=None, chain=True))

	def kick(self,arg):
		if " " in arg:
			args=arg.split()
		else:
			args=[arg]
		for a in args:
			try:
				 ipaddress.IPv4Network(a)
				 self.kick_ip(a)
			except ValueError:
				 self.kick_user(a)
				 
	def ban(self,arg):
		if " " in arg:
			args=arg.split()
		else:
			args=[arg]
		for a in args:
			try:
				 ipaddress.IPv4Network(a)
				 self.kick_ip(a)
				 if not a in self.bans:
				 	self.bans.append(a)
			except ValueError:
				 self.kick_user(a)
				 if not a in self.bans:
				 	self.bans.append(a)
				 
	def kick_ip(self,ip):
		o=[]
		self.log(f"Kicking IP {ip}")
		try:
			for conn in self.clients.keys():
				client = self.clients[conn]
				if client.ip==ip:
					client.kick()
		except: self.elog(traceback.format_exc(limit=None, chain=True))
		
	def kick_user(self,user):		 
		o=[]
		self.log(f"Kicking user {user}")
		try:
			for conn in self.clients.keys():
				client = self.clients[conn]
				if client.user==user:
					client.kick()
		except: self.elog(traceback.format_exc(limit=None, chain=True))
				 
				 
	def list(self):
		o="\n"
		if len(self.clients):
			for conn in self.clients.keys():
				client=self.clients[conn]
				o+=f"{client.ip}:{client.port}"
				if hasattr(client, 'user'):
					 o+=f" => User: {client.user}"
				o+="\n"
		else: o+="No active connections\n"
		self.log(o)
		
	def debug(self, arguments):
		if arguments[0] == "list":
			print(f"{self.config.settings['debug']}")
			return
		targetpacket = int(arguments[0])
		if not targetpacket in self.config.settings["debug"]:
				self.config.settings["debug"].append(targetpacket)
				self.log(f"debug for packet {targetpacket} enabled")
		elif targetpacket in self.config.settings["debug"]:
				self.config.settings["debug"].remove(targetpacket)
				self.log(f"debug for packet {targetpacket} disabled")
		return
				 
	def console_emit(self):
		while True:
			try:
				line = input("")
				print("[Console] "+line)
				if " " in line:
					line = line.split(" ", 1)
				else:
					line = [line]
				self.commands.run(line)
			except KeyboardInterrupt:
				break
			except Exception as e:
				print(traceback.format_exc(limit=None, chain=True))
		return
			
	def purgeclient(self, conn):
		del self.clients[conn]
		conn.close()
		

	def backupAll(self,sname):
		try:
			os.makedirs("backups/"+sname)
		except:
			pass
		try:
			os.system("cp -r space backups/"+sname)
		except:
			self.elog("WARNING: failed to backup")

	def restoreAll(self,sname):
		try:
			os.makedirs("space")
		except:
			pass
		try:
			os.system("cp -r backups/"+sname+" space")
		except:
			self.elog("WARNING: failed to restore")
