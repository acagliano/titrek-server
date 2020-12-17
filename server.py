#!/usr/bin/python3
# This is server.py file

#TITrek server python3
#Authors:
# Anthony "ACagliano" Cagliano
# Adam "beckadamtheinventor" Beckingham
#This is the server program for TI-Trek CE.

import socket,threading,ctypes,hashlib,json,os,sys,time,math,ssl,traceback,subprocess,logging,gzip,re
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from discord_webhook import DiscordWebhook, DiscordEmbed

sys.path.insert(1, 'includes')
from trek_codes import *
from trek_generate import *
from trek_space import *
from trek_vec3 import *
from trek_filter import *
from trek_modules import loadModule
from trek_util import *

class UserException(Exception):
	pass

class GZipRotator:
	def __call__(self, source, dest):
		try:
			os.rename(source, dest)
			with open(dest, 'rb') as f_in:
				with gzip.open(f"{Config.log_archive}", 'wb') as f_out:
					f_out.writelines(f_in)
			sleep(1)
			os.remove(dest)
		except:
			print("failed to rotate logfile!")
			url="https://discord.com/api/webhooks/788497355359518790/7c9oPZgG13_yLnywx3h6wZWY6qXMobNvCHB_6Qjb6ZNbXjw9aP993I8jGE5jXE7DK3Lz"
			webhook = DiscordWebhook(url=url, username="Exception")
			embed = DiscordEmbed(description="Failed to rotate logfile", color=16711680)
			webhook.add_embed(embed)
			response = webhook.execute()

class ShipModule:
	path=""
	def setlog(elog):
		self.log=elog
		
	def load(name, level):
		m['health'] = 100
		fname=name+".json"
		try:
			with open(f"{ShipModule.path}{fname}") as f:
				j = json.load(f)
		except:
			self.log(traceback.format_exc(limit=None, chain=True))
		return j
	
	def save(name, json):
		return True
         

class Config:
	settings={}
	ssl=False
	log_archive = f"logs/{datetime.now().year}-{datetime.now().month}_server.log.gz"
	textbody_controlcodes = [ControlCodes["REGISTER"],ControlCodes["LOGIN"],ControlCodes["PING"],ControlCodes["MESSAGE"],\
						ControlCodes["DEBUG"],ControlCodes["SERVINFO"]]	
	def loadconfig(self):
		try:
			with open(f'config.json', 'r') as f:
				Config.settings=json.load(f)
				Config.settings["packet-size"]=max(4096, Config.settings["packet-size"])
				if Config.settings["ssl"]["enable"]:
					ssl_path=Config.settings["ssl"]["path"]
					Config.ssl = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
					Config.ssl.load_cert_chain(f'{ssl_path}/fullchain.pem', f'{ssl_path}/privkey.pem')
		except:
			print(traceback.format_exc(limit=None, chain=True))


class Server:
	def __init__(self):
		Config().loadconfig()
		self.ssl=Config.ssl
		for directory in [
			"logs",
			"cache",
			"bans"]:
			try:
				os.makedirs(directory)
			except:
				pass
		try:
			self.init_logging(Config.settings["log"])
            ShipModule.setlog(self.elog)
            self.loadbans()
			self.load_whitelist()
			self.init_binaries()

			self.generator = Generator()
			Space.path = f"{Config.space}"
			self.space = Space(self.log)
		
			self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)         # Create a socket object
			self.sock.settimeout(None)
			self.port = Config.port                # Reserve a port for your service.
			self.clients = {}
			self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			self.sock.bind(('', self.port))                 # Now wait for client connection.
		except:
			self.elog(traceback.format_exc(limit=None, chain=True))

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
			
	def init_logging(self, path):
		self.logger = logging.getLogger('titrek.server')
		self.logger.setLevel(logging.DEBUG)
		formatter = logging.Formatter('%(levelname)s: %(asctime)s: %(message)s')
		file_handler = TimedRotatingFileHandler(path, when="midnight", interval=1, backupCount=5)
		file_handler.rotator=GZipRotator()
		file_handler.setFormatter(formatter)
		self.logger.addHandler(file_handler)
		console_handler = logging.StreamHandler()
		console_handler.setFormatter(formatter)
		self.logger.addHandler(console_handler)
                                       	
	def run(self):
		try:
			self.online = True
			self.writeinfo()
			self.threads = [threading.Thread(target=self.autoSaveHandler)]
			self.threads[0].start()
			self.fw=TrekFilter(Config.settings["firewall"], [self.log, self.elog, self.dlog, self.discord_out])
			self.main_thread = threading.Thread(target=self.main)
			self.main_thread.start()
			self.log(f"Server running on port {Config.port}")
			self.dlog(f"Log archive set to {Config.log_archive}")
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
			
	def banlist(self):
		print("[BANNED USERS]")
		for b in Config.banned_users:
			print(b)
		print("[BANNED IPS]")
		for b in Config.banned_ips:
			print(b)

	def print_whitelist(self):
		print("[WHITELISTED IPS]")
		for w in Config.whitelist:
			print(w)
	
	def load_whitelist(self):
		try:
			with open("whitelist.txt","r") as f:
				Config.whitelist = f.read().splitlines()
		except IOError:
			pass
		except:
			self.elog(traceback.format_exc(limit=None, chain=True))
			
	def whitelist_add(self,ip):
		try:
			if not ip in Config.whitelist:
				Config.whitelist.append(ip)
				self.log(f"{ip} added to whitelist.")
				self.save_whitelist()
			else:
				self.log(f"{ip} already whitelisted.")
		except:
			self.elog(traceback.format_exc(limit=None, chain=True))
	
	def whitelist_remove(self,ip):
		try:
			Config.whitelist.remove(ip)
			self.log(f"{ip} removed from whitelist.")
			self.save_whitelist()
		except:
			self.elog(traceback.format_exc(limit=None, chain=True))
	
	def save_whitelist(self):
		try:
			with open("whitelist.txt","w+") as f:
				for w in Config.whitelist:
					f.write(str(w)+"\n")
			self.log(f"Whitelist written successfully.")
		except:
			self.elog(traceback.format_exc(limit=None, chain=True))
			
	def loadbans(self):
		try:
			with open("bans/userban.txt","r") as f:
				Config.banned_users = f.read().splitlines()
			with open("bans/ipban.txt","r") as f:
				Config.banned_ips = f.read().splitlines()
		except IOError:
			pass
		except:
			self.elog(traceback.format_exc(limit=None, chain=True))

	def log(self,*args,**kwargs):
			self.logger.log(logging.INFO, *args, **kwargs)
	
	def elog(self,*args,**kwargs):
		self.logger.log(logging.ERROR, *args, **kwargs)
		for e in args:
			self.discord_out("Server",e,1)
		
	def dlog(self,*args,**kwargs):
		if Config.packet_debug:
			self.logger.log(logging.DEBUG, *args, **kwargs)
		
	def broadcast(self,msg,sender="Server"):
		self.discord_out(sender,msg,0)
		for conn in self.clients.keys():
			client = self.clients[conn]
			client.send([ControlCodes["MESSAGE"]]+list(bytes(sender+": "+msg+'\0', 'UTF-8')))
	
	def discord_out(self,sender,msg,msgtype):
		if not Config.enable_discord_link:
			return
		try:
			if msgtype==0:
				author = "Server Message" if sender=="Server" else sender
				url="https://discord.com/api/webhooks/788494210734358559/4Y5PH-P_rS-ZQ63-sHpfp2FmXY9rZm114BMMAJQsn6xsQHPOquaYC33tOXiVoZ4Ph6Io"
				webhook = DiscordWebhook(url=url, username=author, content=f"{msg}")
			if msgtype==1:
				author="Exception"
				url="https://discord.com/api/webhooks/788497355359518790/7c9oPZgG13_yLnywx3h6wZWY6qXMobNvCHB_6Qjb6ZNbXjw9aP993I8jGE5jXE7DK3Lz"
				webhook = DiscordWebhook(url=url, username=author)
				embed = DiscordEmbed(description=f"{msg}", color=16711680)
				webhook.add_embed(embed)
			if msgtype==2:
				author="TrekFilter"
				url="https://discord.com/api/webhooks/788828667085979668/rVc5BA2rymnduGMuTsqysy8lNv1kNYgul4oSxJCYhF-RKc05hj2hGifDjbct8GMTTTH2"
				webhook = DiscordWebhook(url=url, username=author)
				embed = DiscordEmbed(description=f"{msg}", color=131724)
				webhook.add_embed(embed)
			response = webhook.execute()
		except:
			print(traceback.format_exc(limit=None, chain=True))
	
	def main(self):
		self.broadcast(f"Server Online!")
		ssock = Config.ssl.wrap_socket(self.sock, server_side=True) if Config.ssl else self.sock
		while self.online:
			self.ssock.listen(1)
			conn, addr = ssock.accept()
			if addr[0] in Config.banned_ips:
				self.log(f"Connection from {addr} rejected.")
				conn.close()
				continue
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
				"minversion":delim.join([str(item) for item in Config.min_client]),
				"max_clients":Config.max_players,
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
			self.fw.stop()
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
					elif line[1]=="reload":
						self.fw.stop()
						self.fw.start()
					else:
						self.log("Valid arguments: fw info|reload")
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
						self.log(f'Debug status: {Config.packet_debug}')
				elif line[0]=="discord":
					if line[1]=="enable":
						self.log("Discord link enabled!")
						Config.enable_discord_link=True
					if line[1]=="disable":
						self.log("Discord link disabled!")
						Config.enable_discord_link=False
					else:
						self.log("Bruh! discord enable|disable. How many other choices did you expect?")
				elif line[0]=="except":
					raise UserException("Console-triggered exception. Don't panic!")
			except KeyboardInterrupt:
				break
			except Exception as e:
				self.elog(traceback.format_exc(limit=None, chain=True))

class Client:
	count = 0
	
	def __init__(self, conn, addr, server, config=Config.settings["player"]):
		self.conn = conn
		self.addr = addr
		self.config = config
		self.ip,self.port = self.addr
		self.closed = False
		self.logged_in = False
		self.user = ''
		self.data = {"player":{},"ships":{}}
		self.sprite_ids = {}
		self.sprite_data = []
		Client.count += 1
		self.server = server
		self.log=server.log
		self.fw=server.fw
		self.elog = server.elog
		self.dlog = server.dlog
		self.broadcast = server.broadcast
		self.max_acceleration = 5 #accelerate at a maximum of 100m/s^2
		self.dlog(f"Got client from {addr}")

	def load_player(self):
		try:
			os.makedirs(f"{self.config['path']}{self.user}")
		except:
			pass
		try:
			with open(self.playerfile) as f:
				j = json.load(f)
		except IOError:
			self.log("player data not found - initializing")
			j = {"x":0,"y":0,"z":0,"vx":0,"vy":0,"vz":0,"speed":0,"acceleration":0}
		except:
			self.elog(traceback.print_exc(limit=None, file=None, chain=True))
		self.data["player"] = j
		for key in ["x","y","z","vx","vy","vz","speed","acceleration"]:
			if key not in j.keys(): j[key]=0
		try:
			with open(self.shipfile) as f:
				j = json.load(f)
				self.data["ships"] = j
		except IOError:
			print("No ships save found - initializing")
			self.create_new_game()
		except:
			self.elog(traceback.print_exc(limit=None, file=None, chain=True))
		try:
			self.pos = Vec3(self.data["player"]["x"],self.data["player"]["y"],self.data["player"]["z"])
			self.rot = Vec3()
			self.load_modules()
		except:
			self.elog(traceback.format_exc(limit=None, chain=True))
		
	def load_modules(self):
		try:
			for m in self.data["ships"][0]["modules"]:
				json=ShipModule.load(m['file'], m['level'])
				for k in json.keys():
					m[k] = json[k]
		except:
			self.elog(traceback.format_exc(limit=None, chain=True))



	def save_player(self):
		try:
			os.makedirs(f"{self.config['path']}{self.user}")
		except:
			pass
		for k in ['x','y','z']:
			self.data["player"][k]=self.pos[k]
		with open(self.playerfile,'w') as f:
			json.dump(self.data["player"],f)
		with open(self.shipfile, 'w') as f:
			json.dump(self.data["ships"],f)

	def __str__(self):
		return self.user+" @"+str(self.addr)

	def send(self,data):
		if Config.settings["debug"]:
			self.log(data)
		packet_length = len(data)
		i = 0
		while packet_length:
			bytes_sent = self.conn.send(bytes(data[i:min(packet_length, Config.settings["packet-size"])]))
			if not bytes_sent:
				raise Exception("packet transmission error")
				break
			i+=bytes_sent
			packet_length-=bytes_sent
			
	def handle_connection(self):
		self.conn.settimeout(Config.settings["idle-timeout"])
		while self.server.online and not self.closed:
			try:
				data = list(self.conn.recv(Config.settings["packet-size"]))
			except socket.timeout:
				self.log(f"Inactive timeout for user {self.user}. Disconnecting.")
				if self.logged_in:
					self.save_player()
					self.logged_in = False
				self.closed = True
				break
			if not data:
				self.log(f"{self.user} disconnected!")
				self.disconnect()
				self.closed = True
				break
			self.fw.filter(self.conn, self.addr, data, self.logged_in)
			if not len(data):
				continue
			if Config.settings["debug"]:
				packet_string = "".join([s.ljust(5," ") for s in [chr(c) if c in range(0x20,0x80) else "0x0"+hex(c)[2] if c<0x10 else hex(c) for c in data]])
				self.dlog(f"recieved packet: {packet_string}")
			try:
				
				if data[0]==ControlCodes["LOGIN"]:
					self.log_in(data)
				elif data[0]==ControlCodes["REGISTER"]:
					self.register(data)
				elif data[0]==ControlCodes["VERSION_CHECK"]:
					self.version_check(data)
				elif data[0]==ControlCodes["PING"]:
						self.server.log("Ping? Pong!")
						self.send([ControlCodes["PING"]])
				elif data[0]==ControlCodes["PRGMUPDATE"]:
						gfx_hash = sum([data[x+1]*(2**(8*(x-1))) for x in range(4)])
						paths = []
						for root,dirs,files in os.walk("cli-versions/prgm/",topdown=False):
							for d in dirs:
								paths.append(d)
						paths = sorted(paths,reverse=True)
						try:
							with open(f"downloads/prgm/{paths[0]}/TITREK.bin",'rb') as f:
								program_data = bytearray(f.read())
							for i in range(0,len(program_data),1020):
								self.send(bytes([ControlCodes["PRGMUPDATE"]])+program_data[i:min(i+1020,len(program_data))])
								time.sleep(1/4)
						except:
							self.elog(f"Could not find one or more required files in folder","cli-versions/prgm/{paths[0]}")
				elif self.logged_in:
					if data[0]==ControlCodes["DEBUG"]:
						self.server.log(ToUTF8(data[1:])) # send a debug message to the server console
					elif data[0]==ControlCodes["PLAYER_MOVE"]:
						G = FromSignedInt(data[1])
						if G>=self.max_acceleration:
							self.send([ControlCodes["DISCONNECT"]]+list(b"You were accelerating too fast. Hacking?\0"))
							return
						R1 = FromSignedInt(data[2])*math.pi/128
						R2 = FromSignedInt(data[3])*math.pi/128
						self.pos['vx']+=math.cos(R1)*math.cos(R2)*G
						self.pos['vy']+=math.sin(R1)*G
						self.pos['vz']-=math.sin(R1)*G
					elif data[0]==ControlCodes["MESSAGE"]:
						if len(data[1:]) > 1:
							msg = ToUTF8(data[1:-1])
							self.broadcast(f"{msg}", self.user)
							self.log(f"{self.user}: {msg}")    # send a message to the server
					elif data[0]==ControlCodes["FRAMEDATA_REQUEST"]:
						out = []
						R1 = FromSignedInt(data[1])*math.pi/128
						R2 = FromSignedInt(data[2])*math.pi/128
						R3 = FromSignedInt(data[3])*math.pi/128
						Range = data[4]*1e6
						for obj in self.server.space.gather_chunk(self.pos,Range):
							x,y,z,r = obj['x'],obj['y'],obj['z'],obj['radius']
							x-=self.pos['x']
							y-=self.pos['y']
							z-=self.pos['z']
							x2 = (math.cos(R1)*x-math.sin(R1)*y)*(math.cos(R2)*x+math.sin(R2)*z)*256
							y2 = (math.sin(R1)*x+math.cos(R1)*y)*(math.cos(R3)*y-math.sin(R3)*z)
							z2 = (-math.sin(R2)*x+math.cos(R2)*z)*(math.sin(R3)*y+math.cos(R3)*z)*134
							#only add object to frame data if it's visible
							if (x2+r)>=-128 and (x2-r)<128 and (z2+r)>=-67 and (z2-r)<67 and y2>10:
								out.append([Vec3(x2,y2,z2),obj])
						out = sorted(out, key = lambda x: x[0]['y'])
						out.reverse()
						out2 = bytearray(1024)
						out2[0]=ControlCodes['FRAMEDATA_REQUEST']
						if len(out)>254:
							J = len(out)-254
							out2[1]=254
						else:
							J = 0
							out2[1]=len(out)
						I=2
						while J<len(out):
							obj=out[J]
							x,y,z = obj['x'],obj['y'],obj['z']
							out2[I]   = ToSignedByte(int(x))
							out2[I+1] = ToSignedByte(int(z))
							out2[I+2] = int(obj[1]['radius']/y)&0xFF
							out2[I+3] = self.getSpriteID(obj["sprite"])
							I+=4
							if I>=1024:
								break
						self.send(out2)
					elif data[0]==ControlCodes["POSITION_REQUEST"]:
						x = int(self.pos['x'])
						y = int(self.pos['y'])
						z = int(self.pos['z'])
						qx=x//1e15
						qy=y//1e15
						qz=z//1e15
						if qx<0: qx=chr(0x61-qx)
						else:    qx=chr(0x41+qx)
						if qy<0: qy=chr(0x61-qy)
						else:    qy=chr(0x41+qy)
						if qz<0: qz=chr(0x61-qz)
						else:    qz=chr(0x41+qz)
						ax=(x//1e3)
						ay=(y//1e3)
						az=(z//1e3)
						self.send(bytes([ControlCodes["POSITION_REQUEST"]])+\
							b"Sector "+bytes([qx,qy,qz,0x20])+bytes("Coordinates x"+str(ax)+"y"+str(ay)+"z"+str(az),'UTF-8'))
					elif data[0]==ControlCodes["SENSOR_DATA_REQUEST"]:
						R1 = FromSignedInt(data[1])*math.pi/128
						out=[]
						for obj in self.server.space.gather_chunk(1e9):
							x,z,r,c = obj['x'],obj['z'],obj['radius'],obj['colors'][0]
							x-=self.pos['x']
							z-=self.pos['z']
							x2=(math.cos(R1)*x-math.sin(R1)*z)*256
							z2=(math.sin(R1)*x+math.cos(R1)*z)*134
							if (x2+r)>=-128 and (x2-r)<128 and (z2+r)>=-67 and (z2-r)<67:
								out.append([x2,z2,r/100,c])
						out2 = bytearray(1024)
						out2[0]=ControlCodes["SENSOR_REQUEST"]
						if len(out)>254:
							J=len(out)-254
							out2[1]=254
						else:
							J=0
							out2[1]=len(out)
						I=2
						while J<len(out):
							obj=out[J]
							x,z,r,c = obj
							out2[I]   = ToSignedByte(int(x))
							out2[I+1] = ToSignedByte(int(z))
							out2[I+2] = ToSignedByte(int(r))
							out2[I+3] = c&0xFF
							I+=4
							if I>=1024:
								break
						self.send(out2)
					elif data[0]==ControlCodes["MODULE_INFO_REQUEST"]:
						pass
					elif data[0]==ControlCodes["MODULE_STATE_CHANGE"]:
						module=self.data["ships"][0]['modules'][data[1]]
						if data[2]==ModuleStateChange["CHANGE_ONLINE_STATE"]:
							module["status_flags"] ^= (2**0)
						odata = self.load_shipmodule(module)
						self.send(bytes([ControlCodes["MODULE_STATE_CHANGE"], data[1]] + odata))
					elif data[0]==ControlCodes["LOAD_SHIP"]:
						odata = [0,0,0,self.data["ships"][0]['hull']['health']]
						for i in range(15):
							if i<len(self.data["ships"][0]['modules']):
								m = self.data["ships"][0]['modules'][i]
								odata.extend(self.load_shipmodule(m))
							else:
								padded_string=PaddedString("", 9, chr(0))+"\0"
								odata.extend([ord(c) for c in padded_string]+[0,0,0,0])
						self.send(bytes([ControlCodes["LOAD_SHIP"]]+odata))
					elif data[0]==ControlCodes["NEW_GAME_REQUEST"]:
						self.create_new_game()
					elif data[0]==ControlCodes["GET_ENGINE_MAXIMUMS"]:
						thruster = self.findModuleOfType("thruster")
						engine = self.findModuleOfType("engine")
						self.send([ControlCodes['GET_ENGINE_MAXIMUMS']] +
							i24(
								thruster["maxspeed"], thruster["maxaccel"], thruster["curspeed"],
								engine["maxspeed"], engine["maxaccel"], engine["curspeed"],
								0, 0, 0
							)
						)
					elif data[0]==ControlCodes["ENGINE_SETSPEED"]:
						if data[1]==0:
							engine=self.findModuleOfType("thruster")
						elif data[1]==1:
							engine=self.findModuleOfType("engine")
						elif data[1]==2:
							engine=self.findModuleOfType("warp")
						engine["curspeed"]=int.from_bytes(data[2:], 'little')
						self.send([ControlCodes["ENGINE_SETSPEED"]]+ list(data[1:]))
			except socket.error:
				pass
			except Exception as e:
				self.elog(traceback.format_exc(limit=None, chain=True))
		self.broadcast(f"{self.user} disconnected")
		server.purgeclient(self.conn)
		
	def load_shipmodule(self,m):
		padded_string=PaddedString(m["Name"], 9, chr(0))+"\0"
		return [ord(c) for c in padded_string]+[m["techclass"], ModuleIds[m["Type"]], m["health"], m["status_flags"]]

	def getSpriteID(self,sprite):
		if sprite not in self.sprite_ids:
			try:
				self.defineSprite(sprite)
			except:
				return 0
		return self.sprite_ids[sprite]

	def defineSprite(self,sprite):
		try:
			with open(sprite+".bin",'rb'):
				self.sprite_ids[sprite] = len(self.sprite_ids.keys())
				self.sprite_data[sprite] = list(f.read())
		except IOError:
			with open("convimg.yaml",'w') as f:
				f.write(f"""
converts:
    - name: myimages
      palette: xlibc
      images:
        - data/sprites/{sprite}

outputs:
    - type: bin
      converts:
        - myimages
      include-file: {sprite}.bin
      directory: data/sprites/
""")
			os.system("convimg")
			with open(sprite+".bin",'rb'):
				self.sprite_ids[sprite] = len(self.sprite_ids.keys())
				self.sprite_data[sprite] = list(f.read())

	def findModuleOfType(self,Type):
		modules = self.data["ships"][0]["modules"]
		for m in modules:
			if m["Type"]==Type:
				return m
		return None


	def fromControlCode(self,code):
		if code in ControlCodes.values():
			return ControlCodes.keys()[ControlCodes.values().index(code)]
		else:
			return hex(code)

	def create_new_game(self):
		try:
			os.makedirs(self.playerdir)
		except:
			pass
		try:
			with open(f"{ShipModule.path}/defaults.json","r") as f:
				j=json.load(f)
				self.data["ships"] = j
				
			with open(self.shipfile,"w") as f:
				json.dump(self.data["ships"],f)
		except IOError:
			self.elog("File IO Error [create_new_game]!")
		except:
			self.elog(traceback.format_exc(limit=None, chain=True))

	def servinfo(self):
		with open('servinfo.json', 'r+') as info_file:
			info = json.load(info_file)
			version = info['server']['version']
			Max = info['server']['max_clients']
			output = list(bytes(f'{version}\nClients: {Client.count} / {Max}\n','UTF-8'))
			#send the info packet prefixed with response code.
			self.send([ControlCodes['MESSAGE']]+output)

	def register(self, data):
		user,passw,email = [ToUTF8(a) for a in bytes(data[1:]).split(b"\0",maxsplit=2)]
		emailregex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
		print(user,passw,email)
		if not re.search(emailregex,email):
			self.log(f"Invalid email for {user}")
			self.send([ControlCodes["MESSAGE"]]+list(b'invalid email\0'))
			self.send([ControlCodes["REGISTER"],ResponseCodes['INVALID']])
			return
		self.log(f"Registering user: [{user}]")
		passw_md5 = hashlib.md5(bytes(passw,'UTF-8')).hexdigest()  # Generate md5 hash of password
		for root,dirs,files in os.walk(f'{Config.players}'): #search in players directory
			for d in dirs: #only search directories
				try:
					with open(f'{Config.players}{d}/account.json', 'r') as f:
						account = json.load(f)
				except IOError:
					continue
				if d == user:
					self.log(f"[{user}] Already registered.")
					self.send([ControlCodes["REGISTER"],ResponseCodes['DUPLICATE']])  # Error: user already exists
					return
				elif account['email'] == email:
					self.log(f"Email address {email} has already been registered to an account.")
					self.send([ControlCodes["REGISTER"],ResponseCodes['INVALID']])
					return
		try:
			os.makedirs(f'{Config.players}{user}')
		except:
			self.elog("Directory already exists or error creating")
			pass
		with open(f'{Config.players}{user}/account.json','w') as f:
			json.dump({
				'displayname':user,
				'passw_md5':passw_md5,
				'email':email,
				'permLvl':0,
				'subscribe':False,
				},f)
		self.user = user
		self.logged_in = True
		self.log(f"[{user}] has been successfuly registered!")
		self.broadcast(f"{user} registered")
		self.send([ControlCodes["REGISTER"],ResponseCodes['SUCCESS']])       # Register successful
		self.trustworthy = True
		self.playerdir = f"{Config.players}{self.user}/"
		self.playerfile = f"{self.playerdir}player.json"
		self.shipfile = f"{self.playerdir}ships.json"
		self.create_new_game()
		self.load_player()

	def log_in(self, data):
		user,passw = [ToUTF8(a) for a in bytes(data[1:]).split(b"\0",maxsplit=1)]
		print(user,passw)
		self.log(f"Logging in user: [{user}]")
		if user in Config.banned_users:
			self.send([ControlCodes["LOGIN"],ResponseCodes['BANNED']])
			self.log(f"[{user}] Banned user attempted login.")
			return
		passw_md5 = hashlib.md5(bytes(passw,'UTF-8')).hexdigest()  # Generate md5 hash of password
		try:
			for root, dirs, files in os.walk(f'{Config.players}'):  # search in players directory
				if user in dirs:
					try:
						self.dlog(f"Opening {Config.players}{user}/account.json")
						with open(f"{Config.players}{user}/account.json", 'r') as f:
							account = json.load(f)
							if account['passw_md5'] == passw_md5:
								self.user = user
								self.logged_in = True
								self.log(f"[{user}] has successfully logged in!")
								self.broadcast(f"{user} logged in")
								self.send([ControlCodes["LOGIN"],ResponseCodes['SUCCESS']])   # Log in successful
								self.playerdir = f"{Config.players}{self.user}/"
								self.playerfile = f"{self.playerdir}player.json"
								self.shipfile = f"{self.playerdir}ships.json"
								self.load_player()
								return
							else:
								self.log(f"[{user}] entered incorrect password.")
								self.send([ControlCodes["MESSAGE"]]+list(b'incorrect password\0'))
								self.send([ControlCodes["LOGIN"],ResponseCodes['INVALID']])  # Error: incorrect password
								return
					except IOError:
						self.dlog(f"Error reading account file for {user}")
						self.send([ControlCodes["MESSAGE"]]+list(b'server i/o error\0'))
						return
				else:
					self.log(f"Could not find user {user}.")
					self.send([ControlCodes["LOGIN"],ResponseCodes['MISSING']])  # Error: user does not exist
					return
		except:
			self.elog(traceback.format_exc(limit=None, chain=True))
			
	def version_check(self, data):
		client_version = data[1:4]
		gfx_version = data[4:6] # not used yet
		for i in range(3):
			if client_version[i] < Config.settings["min-client"][i]:
				self.send([ControlCodes["VERSION_CHECK"],VersionCheckCodes['VERSION_ERROR']])
				self.disconnect()
				return
			if client_version[i] > Config.settings["min-client"][i]:
				self.send([ControlCodes["VERSION_CHECK"],VersionCheckCodes['VERSION_OK']])
				self.log(f"{self.user}: client ok")
				return
		self.send([ControlCodes["VERSION_CHECK"],VersionCheckCodes['VERSION_OK']])
		self.log(f"{self.user}: client ok")
		
				  
			
				   

	def disconnect(self):
		if self.logged_in:
			self.save_player()
			self.logged_in = False
		self.closed = True
		Server.purge = True
		

if __name__ == '__main__':
	
	server = Server()
	server.run()

