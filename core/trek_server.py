import socket,threading,ctypes,hashlib,json,os,sys,time,math,ssl,traceback,subprocess,logging,gzip,re

from core.utils import trek_logging
from core.utils import trek_filter
from core.utils import trek_modules
from core.utils import trek_config
from core.math import trek_generate

from core.trek_codes import *
from core import trek_clients
from core import trek_space


class Server:
	def __init__(self, serv_num):
		self.instance_num=serv_num
		self.server_root=f"servers/server.{self.instance_num}/"
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
			self.config=trek_config.Config(self.logger)
			self.ssl=self.config.ssl
#			self.loadbans()
#			self.load_whitelist()
#			self.init_binaries()
			self.fw=self.config.firewall

			self.generator = trek_generate.Generator()
			self.space = trek_space.Space(self.server_root, self.logger, self.config.settings["space"])
			self.modules=trek_modules.TrekModules("data/modules/")
		
			self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)         # Create a socket object
			self.sock.settimeout(None)
			self.port = self.config.settings["port"]      # Reserve a port for your service. Default + instance num
			self.clients = {}
			self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			self.sock.bind(('', self.port))                 # Now wait for client connection.
		except:
			self.elog(traceback.format_exc(limit=None, chain=True))

						 
	def setup_loggers(self):
		self.logger=trek_logging.TrekLogging(f"{self.server_root}logs/")
						 
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
			self.console()
			self.stop()
			self.sock.close()
		#	self.flush_log_to_archive()
		except:
			self.elog(traceback.format_exc(limit=None, chain=True))

	#def flush_log_to_archive(self):
	#	try:
	#		with gzip.open(Config.log_archive, 'ab') as gf:
	#			with open(Config.log_file, 'rb') as lf:
	#				gf.write(lf.read())
	#		sleep(2)
     #       open(f'{Config.log_file}', 'w+').close()
		#	self.log("Instance logfile flushed to archive.")
	#	except:
	#		self.elog(traceback.print_exc(limit=None, file=None, chain=True))
			
#	def banlist(self):
#		print("[BANNED USERS]")
#		for b in Config.banned_users:
#			print(b)
#		print("[BANNED IPS]")
#		for b in Config.banned_ips:
#			print(b)
#
#	def print_whitelist(self):
#		print("[WHITELISTED IPS]")
#		for w in Config.whitelist:
#			print(w)
#	
#	def load_whitelist(self):
#		try:
#			with open("whitelist.txt","r") as f:
#				Config.whitelist = f.read().splitlines()
#		except IOError:
#			pass
#		except:
#			self.elog(traceback.format_exc(limit=None, chain=True))
#			
#	def whitelist_add(self,ip):
#		try:
#			if not ip in Config.whitelist:
#				Config.whitelist.append(ip)
#				self.log(f"{ip} added to whitelist.")
#				self.save_whitelist()
#			else:
#				self.log(f"{ip} already whitelisted.")
#		except:
#			self.elog(traceback.format_exc(limit=None, chain=True))
#	
#	def whitelist_remove(self,ip):
#		try:
#			Config.whitelist.remove(ip)
#			self.log(f"{ip} removed from whitelist.")
#			self.save_whitelist()
#		except:
#			self.elog(traceback.format_exc(limit=None, chain=True))
#	
#	def save_whitelist(self):
#		try:
#			with open("whitelist.txt","w+") as f:
#				for w in Config.whitelist:
#					f.write(str(w)+"\n")
#			self.log(f"Whitelist written successfully.")
#		except:
#			self.elog(traceback.format_exc(limit=None, chain=True))
#			
#	def loadbans(self):
#		try:
#			with open("bans/userban.txt","r") as f:
#				Config.banned_users = f.read().splitlines()
#			with open("bans/ipban.txt","r") as f:
#				Config.banned_ips = f.read().splitlines()
#		except IOError:
#			pass
#		except:
#			self.elog(traceback.format_exc(limit=None, chain=True))

	def log(self,*args,**kwargs):
		self.logger.log(logging.INFO, *args, **kwargs)
	
	def elog(self,*args,**kwargs):
		self.logger.log(logging.ERROR, *args, **kwargs)
#		for e in args:
#			self.discord_out("Server",e,1)
		
	def dlog(self,*args,**kwargs):
		if self.config.settings["debug"]:
			self.logger.log(logging.DEBUG, *args, **kwargs)
		
	def broadcast(self,msg,sender="Server"):
#		self.discord_out(sender,msg,0)
		for conn in self.clients.keys():
			client = self.clients[conn]
			client.send([ControlCodes["MESSAGE"]]+list(bytes(sender+": "+msg+'\0', 'UTF-8')))
	
#	def discord_out(self,sender,msg,msgtype):
#		if not self.config.settings["enable-discord-link"]:
#			return
#		try:
#			if msgtype==0:
#				author = "Server Message" if sender=="Server" else sender
#				url="https://discord.com/api/webhooks/788494210734358559/4Y5PH-P_rS-ZQ63-sHpfp2FmXY9rZm114BMMAJQsn6xsQHPOquaYC33tOXiVoZ4Ph6Io"
#				webhook = DiscordWebhook(url=url, username=author, content=f"{msg}")
#			if msgtype==1:
#				author="Exception"
#				url="https://discord.com/api/webhooks/788497355359518790/7c9oPZgG13_yLnywx3h6wZWY6qXMobNvCHB_6Qjb6ZNbXjw9aP993I8jGE5jXE7DK3Lz"
#				webhook = DiscordWebhook(url=url, username=author)
#				embed = DiscordEmbed(description=f"{msg}", color=16711680)
#				webhook.add_embed(embed)
#			if msgtype==2:
#				author="TrekFilter"
#				url="https://discord.com/api/webhooks/788828667085979668/rVc5BA2rymnduGMuTsqysy8lNv1kNYgul4oSxJCYhF-RKc05hj2hGifDjbct8GMTTTH2"
#				webhook = DiscordWebhook(url=url, username=author)
#				embed = DiscordEmbed(description=f"{msg}", color=131724)
#				webhook.add_embed(embed)
#			response = webhook.execute()
#		except:
#			print(traceback.format_exc(limit=None, chain=True))
	
	def main(self):
		self.broadcast(f"Server Online!")
		ssock = self.ssl.wrap_socket(self.sock, server_side=True) if self.ssl else self.sock
		while self.online:
			ssock.listen(1)
			conn, addr = ssock.accept()
			#if addr[0] in Config.banned_ips:
			#	self.log(f"Connection from {addr} rejected.")
			#	conn.close()
			#	continue
			self.clients[conn] = client = trek_clients.Client(conn,addr,self)
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
			if self.config.save():
				 self.log("Successfully wrote config")
			self.broadcast(f"server shutting down in 10s")
			time.sleep(10)
			for client in self.clients.keys():
				self.clients[client].disconnect()
				time.sleep(.05)
			self.clients.clear()
			self.online = False
			self.writeinfo()
		except:
			self.elog(traceback.format_exc(limit=None, chain=True))

	def kick(self,username):
		for conn in self.clients.keys():
			client = self.clients[conn]
			if client.user==username:
				client.disconnect()

	def kickip(self,ip):
		o=[]
		for conn in self.clients.keys():
			client = self.clients[conn]
			if client.ip==ip:
				o.append(conn)
		for conn in o:
			client = self.clients[conn]
			client.disconnect()
			self.purgeclient(conn)

	def ban(self,username):
		self.kick(username)
		if not username in Config.banned_users:
			Config.banned_users.append(username)
			self.save_bans()

	def ipban(self,ip):
		self.kickip(ip)
		if not ip in Config.banned_ips:
			Config.banned_ips.append(ip)
			self.save_bans()
		
	def save_bans(self):
		try:
			with open("bans/ipban.txt","w+") as f:
				for w in Config.banned_ips:
					f.write(str(w)+"\n")
				self.log(f"IP bans written successfully.")
			with open("bans/userban.txt","w+") as f:
				for w in Config.banned_users:
					f.write(str(w)+"\n")
				self.log(f"User bans written successfully.")
		except:
			self.elog(traceback.format_exc(limit=None, chain=True))
			
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

	def console(self):
		while True:
			try:
				line = input("")
				self.log("[Console] "+line)
				if " " in line:
					line = line.split()
				else:
					line = [line]
				if line[0]=="help":
					try:
						with open("helpfile.txt") as f:
							print(f.read())
					except:
						print("No help document availible.")
				elif line[0]=="broadcast" or line[0]=="say":
					ostring=""
					for l in line[1:]:
						ostring+=l
						ostring+=" "
					ostring=ostring[:-1]
					self.log("[Server] "+ostring)
					self.broadcast(ostring)	# broadcast to all clients
				elif line[0]=="stop":
					self.log("Received stop command.")
					break
				elif line[0]=="save":
					self.log("Saving...")
					threading.Thread(target=self.space.save, ).start()
					self.log("Saved.")
				elif line[0]=="seed":
					self.generator.seed(hash(line[1]))
				elif line[0]=="generate":
					self.log("Generating space...")
					threading.Thread(target=self.generator.generate_all,args=(self.space.space, )).start()
					self.log("Finished generating.")
				elif line[0]=="kick":
					self.kick(line[1])
				elif line[0]=="ban":
					self.ban(line[1])
				elif line[0]=="ipban":
					self.ipban(line[1])
				elif line[0]=="banlist":
					self.banlist()
				elif line[0]=="fw":
					if line[1]=="info":
						self.fw.printinfo()
					else:
						self.log("Valid arguments: fw info")
				elif line[0]=="whitelist":
					self.print_whitelist()
				elif line[0]=="backup":
					self.log("Saving...")
					self.backupAll(line[1])
					self.log("Saved.")
				elif line[0]=="restore":
					self.log("Restoring from backup...")
					self.restoreAll(line[1])
					self.log("Restored.")
				elif line[0]=="list":
					self.log("Connected clients:")
					if len(self.clients):
						for client in self.clients.values():
							self.log(str(client))
					else:
						self.log("No clients connected")
				elif line[0]=="debug":
					if line[1]=="on":
						Config.packet_debug=True
					elif line[1]=="off":
						Config.packet_debug=False
					else:
						self.log(f'Debug status: {Config.settings["debug"]}')
				elif line[0]=="discord":
					if line[1]=="enable":
						self.log("Discord link enabled!")
						Config.settings["enable-discord-link"]=True
					elif line[1]=="disable":
						self.log("Discord link disabled!")
						Config.settings["enable-discord-link"]=False
					else:
						self.log("discord enable|disable")
				elif line[0]=="except":
					raise UserException("Console-triggered exception. Don't panic!")
			except KeyboardInterrupt:
				break
			except Exception as e:
				self.elog(traceback.format_exc(limit=None, chain=True))
