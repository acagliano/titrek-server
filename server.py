#!/usr/bin/python3
# This is server.py file

#TITrek server python3
#Authors:
# Anthony "ACagliano" Cagliano
# Adam "beckadamtheinventor" Beckingham
#This is the server program for TI-Trek CE.

import socket,multiprocessing,ctypes,hashlib,json,os,sys,time,math,ssl

from pip._vendor.colorama.win32 import CONSOLE_SCREEN_BUFFER_INFO

from trek_codes import *
from trek_generate import *
from trek_space import *
from trek_vec3 import *
from trek_modules import loadModule

PACKET_DEBUG = False
USE_SSL = False

BANNED_USERS = []
BANNED_IPS = []
InvalidCharacters = [bytes(a,'UTF-8') for a in ["/","\\","#","$","%","^","&","*","!","~","`","\"","|"]] + \
					[bytes([a]) for a in range(1,0x20)] + [bytes([a]) for a in range(0x7F,0xFF)]
TextBodyControlCodes = [ControlCodes["REGISTER"],ControlCodes["LOGIN"],ControlCodes["PING"],ControlCodes["MESSAGE"],\
						ControlCodes["DEBUG"],ControlCodes["SERVINFO"],ControlCodes["DISCONNECT"]]
with open(f'config.json', 'r') as f:
	config = json.load(f)
	PORT = int(config["port"])
	if config["debug"] == "yes":
		PACKET_DEBUG = True
	if config["ssl"] == "yes":
		USE_SSL = True
		SSL_PATH = config["ssl-path"]
		context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
		context.load_cert_chain(f'{SSL_PATH}/fullchain.pem', f'{SSL_PATH}/privkey.pem')

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
	def __init__(self):
		for directory in ["logs","space/data","players","terrain","cache","missions","notes","bans"]:
			try:
				os.makedirs(directory)
			except:
				pass
		self.loadbans()
		self.mlogf = open("logs/messages.txt","a+")
		self.elogf = open("logs/errors.txt","a+")
		self.ilogf = open("logs/log.txt","a+")
		self.banlist = open("bans/userban.txt","a+")
		self.ipbanlist = open("bans/ipban.txt","a+")

		self.generator = Generator()
		self.space = Space(self.log)
		
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)         # Create a socket object
		self.sock.settimeout(None)
		self.port = PORT                # Reserve a port for your service.
		self.clients = {}
		self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.sock.bind(('', self.port))                 # Now wait for client connection.

	def run(self):
		self.online = True
		self.writeinfo()
		self.threads = [multiprocessing.Process(target=self.autoSaveHandler)]
		self.threads[0].start()
		if USE_SSL:
			self.main_thread = multiprocessing.Process(target=self.main_ssl)
		else:
			self.main_thread = multiprocessing.Process(target=self.main_normal)
		self.main_thread.start()
		self.console()
		self.stop()
		self.sock.close()


	def loadbans(self):
		try:
			with open("bans/userban.txt") as f:
				BANNED_USERS = f.read().splitlines()
		except:
			pass
		try:
			with open("bans/ipban.txt") as f:
				BANNED_IPS = f.read().splitlines()
		except:
			pass

	def log(self,*args,**kwargs):
		print(*args,**kwargs)
		for arg in args:
			self.ilogf.write(str(arg)+" ")
		self.ilogf.write("\n")
	
	def elog(self,*args,**kwargs):
		self.log(*args,**kwargs)
		for arg in args:
			self.elogf.write(str(arg)+" ")
		self.elogf.write("\n")


	
	def main_ssl(self):
		while self.online:
			self.sock.listen(1)
			with context.wrap_socket(self.sock, server_side=True) as ssock:
				conn, addr = ssock.accept()
				self.clients[conn] = client = Client(conn,addr,self)
				thread = multiprocessing.Process(target=client.handle_connection)
				self.threads.append(thread)
				thread.start()
				time.sleep(0.002)
				self.writeinfo()
				
	def main_normal(self):
		while self.online:
			self.sock.listen(1)
			conn, addr = self.sock.accept()
			self.clients[conn] = client = Client(conn,addr,self)
			thread = multiprocessing.Process(target=client.handle_connection)
			self.threads.append(thread)
			thread.start()
			time.sleep(0.002)
			self.writeinfo()

	def writeinfo(self):
		if self.online:
			status="true"
		else:
			status="false"
		with open("servinfo.json","w") as f:
				f.write('\
{"server":{\
	"version":"2.01.0000",\
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
				multiprocessing.Process(target=self.space.save,args=("space/data", )).start()
			time.sleep(60)


	def stop(self):
		self.log("Shutting down.")
		self.space.save("space/data")
		for client in self.clients.keys():
			self.clients[client].disconnect()
			del self.clients[client]
		for thread in self.threads:
			thread.terminate()
		self.main_thread.terminate()
		self.online = False
		self.writeinfo()
		self.closeFiles()

	def closeFiles(self):
		self.banlist.close()
		self.ipbanlist.close()
		self.mlogf.close()
		self.elogf.close()
		self.ilogf.close()

	def kick(self,username):
		for conn in self.clients.keys():
			client = self.clients[conn]
			if client.username==username:
				client.disconnect()
				del self.clients[conn]

	def kickip(self,ip):
		for conn in self.clients.keys():
			client = self.clients[conn]
			if client.addr==ip:
				client.disconnect()
				del self.clients[conn]

	def ban(self,username):
		self.kick(username)
		self.banlist.write(username+"\n")
		self.loadbans()

	def ipban(self,ip):
		self.kickip(ip)
		self.ipbanlist.write(ip+"\n")
		self.loadbans()

	def backupAll(self,sname):
		try:
			os.makedirs("backups/"+sname)
		except:
			pass
		try:
			os.system("cp -r space backups/"+sname)
		except:
			self.log("WARNING: failed to backup")

	def restoreAll(self,sname):
		try:
			os.makedirs("space")
		except:
			pass
		try:
			os.system("cp -r backups/"+sname+" space")
		except:
			self.log("WARNING: failed to restore")

	def console(self):
		while True:
			try:
				line = input(">")
				self.ilogf.write(">"+line+"\n")
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
				elif line[0]=="stop":
					self.log("Received stop command.")
					break
				elif line[0]=="save":
					self.log("Saving...")
					multiprocessing.Process(target=self.space.save,args=("space/data", )).start()
					self.log("Saved.")
				elif line[0]=="seed":
					self.generator.seed(hash(line[1]))
				elif line[0]=="generate":
					self.log("Generating space...")
					multiprocessing.Process(target=self.generator.generate_all,args=(self.space, )).start()
					self.log("Finished generating.")
				elif line[0]=="kick":
					self.kick(line[1])
				elif line[0]=="ban":
					self.ban(line[1])
				elif line[0]=="ipban":
					self.ipban(line[1])
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
					for client in self.clients.values():
						self.log("\t",str(client))
				elif line[0]=="debug-on":
					PACKET_DEBUG = True
				elif line[0]=="debug-off":
					PACKET_DEBUG = False
			except KeyboardInterrupt:
				break
			except Exception as e:
				self.elog("Internal Error:",e)

class Client:
	count = 0
	
	def __init__(self, conn, addr, server):
		self.conn = conn
		self.addr = addr
		self.closed = False
		self.logged_in = False
		self.user = ''
		Client.count += 1
		self.server = server
		self.log=server.log
		self.max_acceleration = 5 #accelerate at a maximum of 100m/s^2
		if PACKET_DEBUG:
			self.log(f"Got client from {addr}")
		self.send([ControlCodes["MESSAGE"]]+list(b'Logging you in...'))

	def load_player(self):
		try:
			os.makedirs(f"players/data/{self.user}")
		except:
			pass
		try:
			with open(self.playerfile) as f:
				self.data = json.load(f)
		except:
			self.data = {'x':0,'y':0,'z':0,'vx':0,'vy':0,'vz':0}
		self.pos = Vec3(self.data['x'],self.data['y'],self.data['z'])
		self.rot = Vec3()
		if "modules" not in self.data.keys():
			self.data["modules"] = [
				{'level': 1, 'file': 'modules/core', 'modifiers': []},
			]
			self.data['hull'] = {'level':1, 'file':'modules/hull','modifiers':[]}
			self.load_modules()

	def load_modules(self):
		for m in self.data['modules']:
			self._load_module(m)
		self._load_module(self.data['hull'])

	def _load_module(self,m):
		m['health'] = 100
		fname=m['file']+f"-L{str(m['level'])}.json"
		try:
			with open(fname):
				j = json.load(f)
			for k in j.keys():
				m[k] = j[k]
		except:
			self.log(f"Error: Failed to load module json \"{fname}\".")


	def save_player(self):
		try:
			os.makedirs(f"players/data/{self.user}")
		except:
			pass
		for k in ['x','y','z']:
			self.data[k]=self.pos[k]
		with open(self.playerfile,'w') as f:
			json.dump(self.data,f)

	def __str__(self):
		return user+" @"+str(self.addr)

	def send(self,data):
		if self.conn.send(bytes(data)):
			self.log("Sent packet")
		else:
			self.log("Failed to send packet")

	def handle_connection(self):
		while self.server.online:
			data = self.conn.recv(1024)
			if not data:
				time.sleep(1)
				continue
			if len(data)==0:
				time.sleep(1)
				continue
			if PACKET_DEBUG:
				o=[]
				for c in data:
					if c>=0x20 and c<0x80: o.append(chr(c)+"   ")
					elif c<0x10: o.append("\\x0"+hex(c)[2:])
					else: o.append("\\x"+hex(c)[2:])
				self.log("recieved packet: ","".join(o))
			if data[0] in TextBodyControlCodes:
				msg = data[1:]
				if any([a in msg for a in InvalidCharacters]):
					self.maliciousDisconnect(data[0])
					return
			try:
				if data[0]==ControlCodes["REGISTER"]:
					self.register(data)
				elif data[0]==ControlCodes["LOGIN"]:
					self.log_in(data)
				elif data[0]==ControlCodes["DISCONNECT"]:
					self.disconnect()
				elif data[0]==ControlCodes["SERVINFO"]:
					self.servinfo()
				elif data[0]==ControlCodes["DEBUG"]:
					self.server.log(ToUTF8(data[1:])) # send a debug message to the server console
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
					if data[0]==ControlCodes["PLAYER_MOVE"]:
						G = FromSignedInt(data[1])
						if G>=self.max_acceleration:
							self.send([ControlCodes["DISCONNECT"]]+list(b"You were accelerating too fast. Hacking?\0"))
							return
						R1 = FromSignedInt(data[2])*math.pi/128
						R2 = FromSignedInt(data[3])*math.pi/128
						self.pos['vx']+=math.cos(R1)*math.cos(R2)*G
						self.pos['vy']+=math.sin(R1)*G
						self.pos['vz']+=-math.sin(R1)*G
					elif data[0]==ControlCodes["MESSAGE"]:
						self.log("["+ToUTF8(self.user)+"]",ToUTF8(data[1:]))    # send a message to the server
					elif data[0]==ControlCodes["CHUNK_REQUEST"]:
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
						out2[0]=ControlCodes['CHUNK_REQUEST']
						if len(out)>127:
							J = len(out)-127
							out2[1]=127
						else:
							J = 0
							out2[1]=len(out)
						I=2
						while J<len(out):
							obj=out[J]
							x,y,z = obj[0]['x'],obj[0]['y'],obj[0]['z']
							out2[I]   = ToSignedByte(int(x))
							out2[I+1] = ToSignedByte(int(z))
							out2[I+2] = int(obj[1]['radius']/y)
							for X in range(3):
								out2[I+3+X] = obj[1]['colors'][X]
							out2[I+6] = int(time.time()*100)&FF
							I+=8
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
					elif data[0]==ControlCodes["SENSOR_REQUEST"]:
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
					elif data[0]==ControlCodes["MODULE_REQUEST"]:
						pass
					elif data[0]==ControlCodes["MODULE_UPDATE"]:
						pass
					elif data[0]==ControlCodes["LOAD_SHIP"]:
						odata = [0,0,0,0,0,0,self.data['hull']['health']]+self.data['hull']['composition']
						for i in range(15):
							if i<len(self.data['modules']):
								odata.extend([m['techclass'],m['techtype'],m['health'],m['status_flags']])
							else:
								odata.extend([0,0,0,0])
						self.send(bytes([ControlCodes["LOAD_SHIP"]]+odata))
					elif data[0]==ControlCodes["NEW_GAME_REQUEST"]:
						self.create_new_game()
				else:
					self.maliciousDisconnect(data[0])
			except socket.error:
				pass
			except Exception as e:
				self.log("Internal Error:",e)
		else:
			self.disconnect()

	def maliciousDisconnect(self,A):
		ts = time.asctime()
		j = {"time": ts, "match": True, "host": str(self.addr)}
		with open("malicious.txt", 'a+') as f:
			f.write(f"# failJSON: {json.dumps(j)}\n{str(self.addr)} @ {ts}:\
		Attempted request without login. Control code: {hex(self.fromControlCode(A))}")
		self.send([ControlCodes["DISCONNECTED"], ResponseCodes["BAD_MESSAGE_CONTENT"]])
		self.close()


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
		ship = {"core":[loadModule("core",1)],"weapons":[],"hull":[loadModule("hull",1)],"shield":[]}
		try:
			with open(self.playerdir+"/ship.json","w") as f:
				json.dump(ship,f)
		except:
			self.elog(f"[{self.user}] Failed to create new game!")

	def servinfo(self):
		with open('servinfo.json', 'r+') as info_file:
			info = json.load(info_file)
			version = info['server']['version']
			Max = info['server']['max_clients']
			output = list(bytes(f'{version}\nClients: {Client.count} / {Max}\n','UTF-8'))
			#send the info packet prefixed with response code.
			self.send([ControlCodes['MESSAGE']]+output)

	def register(self, data):
		user,passw,email = [ToUTF8(a) for a in data[1:].split(b"\0",maxsplit=2)]
		print(user,passw,email)
		self.log("Registering user:",user)
		passw_md5 = hashlib.md5(bytes(passw,'UTF-8')).hexdigest()  # Generate md5 hash of password
		for root,dirs,files in os.walk('players/data/'): #search in players directory
			for d in dirs: #only search directories
				with open(f'players/data/{d}/accounts.json', 'r') as f:
					account = json.load(f)
					if account['user'] == user:
						self.log(f"[{user}] Already registered.")
						self.send([ControlCodes["REGISTER"],ResponseCodes['DUPLICATE']])  # Error: user already exists
						return
					elif account['email'] == email:
						self.log(f"Email address {email} has already been registered to an account.")
						self.send([ControlCodes["REGISTER"],ResponseCodes['INVALID']])
						return
		try:
			os.makedirs(f'players/data/{user}')
		except:
			pass
		with open(f'players/data/{user}/account.json','w') as f:
			json.dump({'user':user,'passw_md5':passw_md5,'email':email},f)
		self.user = user
		self.logged_in = True
		self.log(f"[{user}] has been successfuly registered!")
		self.send([ControlCodes["REGISTER"],ResponseCodes['SUCCESS']])       # Register successful
		self.playerdir = f"players/data/{self.user}/"
		self.playerfile = f"players/data/{self.user}/player.json"
		self.load_player()
		self.create_new_game()

	def log_in(self, data):
		user,passw = [ToUTF8(a) for a in data[1:].split(b"\0",maxsplit=1)]
		print(user,passw)
		self.log("Logging in user:",user)
		if user in BANNED_USERS:
			self.send([ControlCodes["LOGIN"],ResponseCodes['BANNED']])
			self.log(f"[{user}] Banned user attempted login.")
			return
		passw_md5 = hashlib.md5(bytes(passw,'UTF-8')).hexdigest()  # Generate md5 hash of password
		try:
			for root, dirs, files in os.walk('players/data/'):  # search in players directory
				for d in dirs:  # only search directories
					with open(f'players/data/{d}/account.json', 'r') as f:
						account = json.load(f)
					if account['user'] == user:
						if account['passw_md5'] == passw_md5:
							self.user = user
							self.logged_in = True
							self.log(f"[{user}] has successfuly logged in!")
							self.send([ControlCodes["LOGIN"],ResponseCodes['SUCCESS']])   # Log in successful
							self.playerfile = f"players/data/{self.user}/player.json"
							self.load_player()
						else:
							self.log(f"[{user}] entered incorrect password.")
							self.send([ControlCodes["LOGIN"],ResponseCodes['INVALID']])  # Error: incorrect password
		except:
			self.log("[",user,"] could not find user.")
			self.send([ControlCodes["LOGIN"],ResponseCodes['MISSING']])  # Error: user does not exist

	def disconnect(self):
		self.save_player()
		self.send([ControlCodes['DISCONNECT']]) #Let the user know if disconnected. Might be useful eventually.
		self.close()

	def close(self):
		Client.count -= 1
		self.logged_in = False

server = Server()
server.run()

