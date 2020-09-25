#!/usr/bin/python3
# This is server.py file

#TITrek server python3
#Authors:
# Anthony "ACagliano" Cagliano
# Adam "beckadamtheinventor" Beckingham
#This is the server program for TI-Trek CE.

import socket,threading,ctypes,hashlib,json,os,sys,time,math,ssl,traceback,subprocess,logging,gzip
from datetime import datetime

from trek_codes import *
from trek_generate import *
from trek_space import *
from trek_vec3 import *
from trek_modules import loadModule

class Config:
	port = None
	banned_ips = []
	banned_users = []
	whitelist = []
	packet_debug = False
	use_ssl = False
	ssl_path = ""
	inactive_timeout = 600
	dir_gamedata = "data/"
	dir_player = "players/"
	dir_map = "space/"
	dir_modules = "modules/"
	dir_missions = "missions/"
	dir_downloads = "downloads/"
	log_file = "logs/server.log"
	log_archive = f"logs/{datetime.now().year}-{datetime.now().month}_server.log.gz"
	invalid_characters = [bytes(a,'UTF-8') for a in ["/","\\","#","$","%","^","&","*","!","~","`","\"","|"]] + \
					[bytes([a]) for a in range(1,0x20)] + [bytes([a]) for a in range(0x7F,0xFF)]
	textbody_controlcodes = [ControlCodes["REGISTER"],ControlCodes["LOGIN"],ControlCodes["PING"],ControlCodes["MESSAGE"],\
						ControlCodes["DEBUG"],ControlCodes["SERVINFO"],ControlCodes["DISCONNECT"]]
	player_path = ""
	map_path = ""
	module_path = ""
	mission_path = ""
	downloads_path = ""
	
	def setpaths(self):
		Config.player_path = f"{Config.dir_gamedata}{Config.dir_player}"
		Config.map_path = f"{Config.dir_gamedata}{Config.dir_map}"
		Config.module_path = f"{Config.dir_gamedata}{Config.dir_modules}"
		Config.mission_path = f"{Config.dir_gamedata}{Config.dir_missions}"
		Config.downloads_path = f"{Config.dir_gamedata}{Config.dir_downloads}"
	
	def loadconfig(self):
		try:
			with open(f'config.json', 'r') as f:
				config = json.load(f)
				Config.port = int(config["port"])
				Config.packet_debug = config["debug"]
				Config.use_ssl = config["ssl"]
				if Config.use_ssl:
					Config.ssl_path = config["ssl-path"]
					context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
					context.load_cert_chain(f'{SSL_PATH}/fullchain.pem', f'{SSL_PATH}/privkey.pem')
				if config["dir_gamedata"]:
					Config.dir_gamedata = config["dir_gamedata"]
				self.setpaths()
		except:
			print(traceback.print_exc(limit=None, file=None, chain=True))

def ToUTF8(dt):
	if b"\0" in dt:
		return str(bytes(dt[:dt.find(b"\0")]),'UTF-8')
	return str(bytes(dt),'UTF-8')

def FromSignedInt(n):
	if n&0x80:
		return 0x80-n
	else:
		return n

def ToSignedByte(n):
	if n<0:
		while abs(n)<-0x80: n+=0x80
		return 0x100+n%0x80
	else:
		while abs(n)>0x80: n-=0x80
		return n%0x80

class Server:
	purge = False
	def __init__(self):
		Config().loadconfig()
		for directory in [
			"logs",
			f"{Config.dir_gamedata}",
			f"{Config.player_path}",
			f"{Config.map_path}",
			f"{Config.module_path}",
			f"{Config.mission_path}",
			f"{Config.downloads_path}",
			"cache",
			"bans"]:
			try:
				os.makedirs(directory)
			except:
				pass
		try:
			self.logger = logging.getLogger('titrek.server')
			self.loadbans()
			self.load_whitelist()

			self.generator = Generator()
			self.space = Space(self.log)
		
			self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)         # Create a socket object
			self.sock.settimeout(None)
			self.port = Config.port                # Reserve a port for your service.
			self.clients = {}
			self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
			self.sock.bind(('', self.port))                 # Now wait for client connection.
		except:
			self.elog(traceback.print_exc(limit=None, file=None, chain=True))

	def run(self):
		try:
			self.online = True
			self.writeinfo()
			self.threads = [threading.Thread(target=self.autoSaveHandler)]
			self.threads[0].start()
			if Config.use_ssl:
				self.main_thread = threading.Thread(target=self.main_ssl)
			else:
				self.main_thread = threading.Thread(target=self.main_normal)
			self.main_thread.start()
			self.log(f"Server running on port {Config.port}")
			self.dlog(f"Log archive set to {Config.log_archive}")
			self.console()
			self.stop()
			self.sock.close()
			self.flush_log_to_archive()
		except:
			self.elog(traceback.print_exc(limit=None, file=None, chain=True))

	def flush_log_to_archive(self):
		try:
			with gzip.open(Config.log_archive, 'ab') as gf:
				with open(Config.log_file, 'rb') as lf:
					gf.write(lf.read())
				os.remove(Config.log_file)
				self.log("Instance logfile flushed to archive.")
		except:
			self.elog(traceback.print_exc(limit=None, file=None, chain=True))
			
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
			self.elog(traceback.print_exc(limit=None, file=None, chain=True))
			
	def whitelist_add(self,ip):
		try:
			if not ip in Config.whitelist:
				Config.whitelist.append(ip)
				self.log(f"{ip} added to whitelist.")
				self.save_whitelist()
			else:
				self.log(f"{ip} already whitelisted.")
		except:
			self.elog(traceback.print_exc(limit=None, file=None, chain=True))
	
	def whitelist_remove(self,ip):
		try:
			Config.whitelist.remove(ip)
			self.log(f"{ip} removed from whitelist.")
			self.save_whitelist()
		except:
			self.elog(traceback.print_exc(limit=None, file=None, chain=True))
	
	def save_whitelist(self):
		try:
			with open("whitelist.txt","w+") as f:
				for w in Config.whitelist:
					f.write(str(w)+"\n")
			self.log(f"Whitelist written successfully.")
		except:
			self.elog(traceback.print_exc(limit=None, file=None, chain=True))
			
	def loadbans(self):
		try:
			with open("bans/userban.txt","r") as f:
				Config.banned_users = f.read().splitlines()
			with open("bans/ipban.txt","r") as f:
				Config.banned_ips = f.read().splitlines()
		except IOError:
			pass
		except:
			self.elog(traceback.print_exc(limit=None, file=None, chain=True))

	def log(self,*args,**kwargs):
			self.logger.log(logging.INFO, *args, **kwargs)
	
	def elog(self,*args,**kwargs):
		self.logger.log(logging.ERROR, *args, **kwargs)
		
	def dlog(self,*args,**kwargs):
		if Config.packet_debug:
			self.logger.log(logging.DEBUG, *args, **kwargs)
	
	def main_ssl(self):
		while self.online:
			self.sock.listen(1)
			with context.wrap_socket(self.sock, server_side=True) as ssock:
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
				except:
					self.elog(traceback.print_exc(limit=None, file=None, chain=True))
				if Server.purge:
					self.purgeinactive(self)
				time.sleep(0.002)
				self.writeinfo()
				
	def main_normal(self):
		while self.online:
			self.sock.listen(1)
			conn, addr = self.sock.accept()
			if addr[0] in Config.banned_ips:
				self.log(f"Connection from {addr} rejected.")
				conn.close()
				continue
			self.clients[conn] = client = Client(conn,addr,self)
			try:
				thread = threading.Thread(target=client.handle_connection)
				self.threads.append(thread)
				thread.start()
			except:
				self.elog(traceback.print_exc(limit=None, file=None, chain=True))
			if Server.purge:
				self.purgeinactive(self)
			time.sleep(0.002)
			self.writeinfo()

	def writeinfo(self):
		if self.online:
			status="true"
		else:
			status="false"
		versionbuild = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'])
		version = f"2.01.{versionbuild}"
		with open("servinfo.json","w") as f:
				f.write('\
{"server":{\
	"version":"'+version+'",\
	"numclients":'+str(Client.count)+',\
	"minversion":"0.0.92",\
	"max_clients":250,\
	"online":'+status+'\
}}')
	def autoSaveHandler(self):
		last_save_time = start_time = time.time()
		while self.online:
			cur_time = time.time()
			if (cur_time-last_save_time)>=600:
				last_save_time = time.time()
				self.log("Autosaving...")
				threading.Thread(target=self.space.save,args=(f"{Config.map_path}", )).start()
			time.sleep(60)


	def stop(self):
		try:
			self.log("Shutting down.")
			self.space.save(f"{Config.map_path}")
			for client in self.clients.keys():
				self.clients[client].disconnect()
			self.clients.clear()
			self.online = False
			self.writeinfo()
		except:
			self.elog(traceback.print_exc(limit=None, file=None, chain=True))

	def kick(self,username):
		for conn in self.clients.keys():
			client = self.clients[conn]
			if client.user==username:
				client.disconnect()

	def kickip(self,ip):
		for conn in self.clients.keys():
			client = self.clients[conn]
			if client.ip==ip:
				client.disconnect()

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
			self.elog(traceback.print_exc(limit=None, file=None, chain=True))
			
	def purgeinactive(self):
		o = []
		for conn in self.clients.keys():
			client = self.clients[conn]
			if client.closed:
				o.append(conn)
		for i in o:
			del self.clients[i]
		Server.purge = False
		

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
				self.log("[Console] "+line+"\n")
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
				elif line[0]=="broadcast":
					self.log("[Server] "+line[1])
					# broadcast to all clients
				elif line[0]=="stop":
					self.log("Received stop command.")
					break
				elif line[0]=="save":
					self.log("Saving...")
					threading.Thread(target=self.space.save,args=("space/data", )).start()
					self.log("Saved.")
				elif line[0]=="seed":
					self.generator.seed(hash(line[1]))
				elif line[0]=="generate":
					self.log("Generating space...")
					threading.Thread(target=self.generator.generate_all,args=(self.space, )).start()
					self.log("Finished generating.")
				elif line[0]=="kick":
					self.kick(line[1])
				elif line[0]=="ban":
					self.ban(line[1])
				elif line[0]=="ipban":
					self.ipban(line[1])
				elif line[0]=="banlist":
					self.banlist()
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
				elif line[0]=="debug-on":
					PACKET_DEBUG = True
				elif line[0]=="debug-off":
					PACKET_DEBUG = False
			except KeyboardInterrupt:
				break
			except Exception as e:
				self.elog(traceback.print_exc(limit=None, file=None, chain=True))

class Client:
	count = 0
	
	def __init__(self, conn, addr, server):
		self.conn = conn
		self.addr = addr
		self.ip,self.port = self.addr
		self.trustworthy = False
		self.closed = False
		self.logged_in = False
		self.user = ''
		self.data = {"player":{},"ships":{}}
		self.sprite_ids = {}
		self.sprite_data = []
		Client.count += 1
		self.server = server
		self.log=server.log
		self.elog = server.elog
		self.dlog = server.dlog
		self.max_acceleration = 5 #accelerate at a maximum of 100m/s^2
		self.dlog(f"Got client from {addr}")
		self.send([ControlCodes["MESSAGE"]]+list(b'Logging you in...'))

	def load_player(self):
		try:
			os.makedirs(f"{Config.player_path}{self.user}")
		except:
			pass
		try:
			with open(self.playerfile) as f:
				j = json.load(f)
		except IOError:
			self.log("player data not found - initializing")
			j = {"x":0,"y":0,"z":0,"vx":0,"vy":0,"vz":0}
		except:
			self.elog(traceback.print_exc(limit=None, file=None, chain=True))
		self.data["player"] = j
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
			self.elog(traceback.print_exc(limit=None, file=None, chain=True))
		
	def load_modules(self):
		for m in self.data["ships"][0]["modules"]:
			self._load_module(m)
		self._load_module(self.data["ships"][0]['hull'])

	def _load_module(self,m):
		m['health'] = 100
		fname=m['file']+f".json"
		level=m['level']-1
		try:
			with open(f"{Config.module_path}{fname}") as f:
				j = json.load(f)
			for k in j['module'][level].keys():				
				m[k] = j['module'][level][k]
		except:
			self.elog(traceback.print_exc(limit=None, file=None, chain=True))



	def save_player(self):
		try:
			os.makedirs(f"{Config.player_path}{self.user}")
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
		if self.conn.send(bytes(data)):
			self.log("Sent packet")
		else:
			self.elog("Failed to send packet")
			
	def sanitize(self,i):
		if any([a in bytes(i, 'UTF-8') for a in Config.invalid_characters]):
			self.maliciousDisconnect()
			return
			
	def handle_connection(self):
		last_packet_time = time.time()
		while self.server.online and not self.closed:
			data = self.conn.recv(1024)
			if not data or len(data)==0:
				cur_time = time.time()
				if (cur_time-last_packet_time)>=Config.inactive_timeout:
					self.disconnect()
				time.sleep(1)
				continue
			last_packet_time = time.time()
			if Config.packet_debug:
				packet_string = "".join([s.ljust(5," ") for s in [chr(c) if c in range(0x20,0x80) else "0x0"+hex(c)[2] if c<0x10 else hex(c) for c in data]])
				self.dlog(f"recieved packet: {packet_string}")
			try:
				if data[0]==ControlCodes["LOGIN"]:
					self.log_in(data)
				elif self.ip in Config.whitelist:
					if data[0]==ControlCodes["REGISTER"]:
						self.register(data)
					elif data[0]==ControlCodes["SERVINFO"]:
						self.servinfo()
					elif data[0]==ControlCodes["PING"]:
						self.server.log("Ping? Pong!")
						self.send([ControlCodes["MESSAGE"]]+list(b"pong!"))
					elif data[0]==ControlCodes["PRGMUPDATE"]:
						gfx_hash = sum([data[x+1]*(2**(8*(x-1))) for x in range(4)])
						paths = []
						for root,dirs,files in os.walk("cli-versions/prgm/",topdown=False):
							for d in dirs:
								paths.append(d)
						paths = sorted(paths,reverse=True)
						try:
							with open(f"cli-versions/prgm/{paths[0]}/TITREK.bin",'rb') as f:
								program_data = bytearray(f.read())
							for i in range(0,len(program_data),1020):
								self.send(bytes([ControlCodes["PRGMUPDATE"]])+program_data[i:min(i+1020,len(program_data))])
								time.sleep(1/4)
						except:
							self.elog(f"Could not find one or more required files in folder","cli-versions/prgm/{paths[0]}")
					elif self.logged_in:
						if data[0]==ControlCodes["DEBUG"]:
							self.server.log(ToUTF8(data[1:])) # send a debug message to the server console
						elif data[0]==ControlCodes["DISCONNECT"]:
							self.disconnect()
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
							self.log("["+ToUTF8(self.user)+"]",ToUTF8(data[1:]))    # send a message to the server
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
							pass
						elif data[0]==ControlCodes["LOAD_SHIP"]:
							odata = [0,0,0,self.data["ships"][0]['hull']['health']]
							for i in range(15):
								if i<len(self.data["ships"][0]['modules']):
									m = self.data["ships"][0]['modules'][i]
									odata.extend([m['techclass'],m['techtype'],m['health'],m['status_flags']])
								else:
									odata.extend([0,0,0,0])
							self.send(bytes([ControlCodes["LOAD_SHIP"]]+odata))
						elif data[0]==ControlCodes["NEW_GAME_REQUEST"]:
							self.create_new_game()
					else:
						self.maliciousDisconnect()
				else:
					self.maliciousDisconnect()
			except socket.error:
				pass
			except Exception as e:
				self.elog(traceback.print_exc(limit=None, file=None, chain=True))
		Server.purge = True


	def maliciousDisconnect(self):
		try:
			if not self.trustworthy:
				if self.ip in Config.whitelist:
					server.whitelist_remove(self.ip)
					self.elog(f"Packet from {self.ip} rejected. Bad contents, or invalid. De-whitelisting.")
				else:
					server.ipban(self.ip)
					self.elog(f"Packet from {self.ip} rejected. IP banned due to suspect behavior.")
			if self.trustworthy:
				self.elog(f"Packet from {self.ip} rejected. Bad contents, or invalid.")
				self.send([ControlCodes["DISCONNECT"],ResponseCodes['BAD_MESSAGE_CONTENT']]) # Disconnect user, inform of error
			self.close()
			self.elog(f"{self.ip} disconnected.")
			self.trustworthy = False
		except:
			self.elog(traceback.print_exc(limit=None, file=None, chain=True))

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
			j = [{"hull": {'level':1, 'file':'hull','modifiers':[]},"modules":[
				{'level': 1, 'file': 'core', 'modifiers': []},
				{'level': 1, 'file': 'phaser', 'modifiers': []},
				]}
			]
			self.data["ships"] = j
			with open(self.shipfile,"w") as f:
				json.dump(self.data["ships"],f)
		except IOError:
			self.elog("Failed to write file!")
		except:
			self.elog(traceback.print_exc(limit=None, file=None, chain=True))

	def servinfo(self):
		with open('servinfo.json', 'r+') as info_file:
			info = json.load(info_file)
			version = info['server']['version']
			Max = info['server']['max_clients']
			output = list(bytes(f'{version}\nClients: {Client.count} / {Max}\n','UTF-8'))
			#send the info packet prefixed with response code.
			self.send([ControlCodes['MESSAGE']]+output)

	def register(self, data):
		if self.ip not in Config.whitelist:
			self.maliciousDisconnect(True)
		user,passw,email = [ToUTF8(a) for a in data[1:].split(b"\0",maxsplit=2)]
		self.sanitize(user)
		self.sanitize(passw)
		print(user,passw,email)
		self.log(f"Registering user: [{user}]")
		passw_md5 = hashlib.md5(bytes(passw,'UTF-8')).hexdigest()  # Generate md5 hash of password
		for root,dirs,files in os.walk(f'{Config.player_path}'): #search in players directory
			for d in dirs: #only search directories
				try:
					with open(f'{Config.player_path}{d}/account.json', 'r') as f:
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
			os.makedirs(f'{Config.player_path}{user}')
		except:
			self.elog("Directory already exists or error creating")
			pass
		with open(f'{Config.player_path}{user}/account.json','w') as f:
			json.dump({'displayname':user,'passw_md5':passw_md5,'email':email,'permLvl':0},f)
		self.user = user
		self.logged_in = True
		self.log(f"[{user}] has been successfuly registered!")
		self.send([ControlCodes["REGISTER"],ResponseCodes['SUCCESS']])       # Register successful
		self.trustworthy = True
		self.playerdir = f"{Config.player_path}{self.user}/"
		self.playerfile = f"{self.playerdir}player.json"
		self.shipfile = f"{self.playerdir}ships.json"
		self.create_new_game()
		self.load_player()

	def log_in(self, data):
		user,passw,vers = [ToUTF8(a) for a in data[1:].split(b"\0",maxsplit=2)]
		self.sanitize(user)
		self.sanitize(passw)
		print(user,passw)
		self.log(f"Logging in user: [{user}]")
		server.whitelist_add(self.ip)
		if user in Config.banned_users:
			self.send([ControlCodes["LOGIN"],ResponseCodes['BANNED']])
			self.log(f"[{user}] Banned user attempted login.")
			return
		passw_md5 = hashlib.md5(bytes(passw,'UTF-8')).hexdigest()  # Generate md5 hash of password
		try:
			for root, dirs, files in os.walk(f'{Config.player_path}'):  # search in players directory
				for d in dirs:  # only search directories
					try:
						with open(f'{Config.player_path}{d}/account.json', 'r') as f:
							account = json.load(f)
					except IOError:
						continue
					if d == user:
						if account['passw_md5'] == passw_md5:
							self.user = user
							self.logged_in = True
							self.log(f"[{user}] has successfuly logged in!")
							self.send([ControlCodes["LOGIN"],ResponseCodes['SUCCESS']])   # Log in successful
							self.playerdir = f"{Config.player_path}{self.user}/"
							self.playerfile = f"{self.playerdir}player.json"
							self.shipfile = f"{self.playerdir}ships.json"
							self.load_player()
							self.trustworthy = True
						else:
							self.log(f"[{user}] entered incorrect password.")
							self.send([ControlCodes["LOGIN"],ResponseCodes['INVALID']])  # Error: incorrect password
			if self.user == '':
				self.log("[",user,"] could not find user.")
				self.send([ControlCodes["LOGIN"],ResponseCodes['MISSING']])  # Error: user does not exist
		except Exception as e:
			self.elog(traceback.print_exc(limit=None, file=None, chain=True))

	def disconnect(self):
		self.save_player()
		self.send([ControlCodes['DISCONNECT']]) #Let the user know if disconnected. Might be useful eventually.
		self.logged_in = False
		self.closed = True
		

if __name__ == '__main__':
	server = Server()
	logging.basicConfig(format='%(levelname)s: %(asctime)s: %(message)s',level=logging.DEBUG,handlers=[
		logging.StreamHandler(), # writes to stderr
		logging.FileHandler(Config.log_file),
	])
	server.run()

