import os,traceback,json,logging,socket,hashlib,re

from trek.codes import *
from trek.server import *
from trek.utils.logging import *
from trek.utils.filter import *
from trek.utils.modules import *
from trek.math.vec3 import *
from trek.utils.util import *

class ClientDisconnectErr(Exception):
	pass

class Client:
	def __init__(self, conn, addr, server):
		self.conn = conn
		self.addr = addr
		self.config = server.config
		self.ip,self.port = self.addr
		self.connected = True
		self.logged_in = False
		self.server = server
		self.player_root=f"{self.server.server_root}{self.config.settings['player']['path']}"
		try:
			os.makedirs(self.player_root)
		except:
			pass
		self.user = ''
		self.data = {"player":{},"ships":{}}
		self.sprite_ids = {}
		self.sprite_data = []
		self.modules=server.modules
		self.fw=server.fw
		self.log=server.log
		self.elog = server.elog
		self.dlog = server.dlog
		self.broadcast = server.broadcast
		self.max_acceleration = 5 #accelerate at a maximum of 100m/s^2
		self.dlog(f"Got client from {addr}")

	def load_player(self):
		try:
			os.makedirs(f"{self.player_root}{self.user}")
		except:
			pass
		try:
			with open(self.playerfile) as f:
				self.data["player"] = json.load(f)
		except IOError:
			self.dlog("player data not found - initializing")
			self.data["player"] = {"x":0,"y":0,"z":0,"vx":0,"vy":0,"vz":0,"speed":0,"acceleration":0}
		except:
			self.elog(traceback.print_exc(limit=None, file=None, chain=True))
		
		for key in ["x","y","z","vx","vy","vz","speed","acceleration"]:
			if key not in self.data["player"].keys(): self.data["player"][key]=0
		try:
			with open(self.shipfile) as f:
				self.data["ships"] = json.load(f)
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
			hull=self.data["ships"][0]["hull"]
			j=self.modules.load_module(hull['file'], hull['level'])
			for k in j.keys():
				hull[k]=j[k]
			for m in self.data["ships"][0]["modules"]:
				j=self.modules.load_module(m['file'], m['level'])
				for k in j.keys():
					m[k]=j[k]
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
		if self.config.settings["debug"]:
			self.log(data)
		packet_length = len(data)
		i = 0
		try:
			while packet_length:
				bytes_sent = self.conn.send(bytes(data[i:min(packet_length, self.config.settings["packet-size"])]))
				if not bytes_sent:
					raise Exception("packet transmission error")
					break
				i+=bytes_sent
				packet_length-=bytes_sent
		except (BrokenPipeError, OSError): self.elog("send() called on a closed connection. This is probably intended behavior, but worth double checking.")
			
	def handle_connection(self):
		self.conn.settimeout(self.config.settings["idle-timeout"])
		while self.server.online:
			try:
				data = list(self.conn.recv(self.config.settings["packet-size"]))
				if not data or not self.connected:
					raise ClientDisconnectErr(f"{self.user} disconnected!")
				self.fw.filter(self.conn, self.addr, data, self.logged_in)
				if not len(data):
					continue
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
				if self.config.settings["debug"]:
					packet_string = "".join([s.ljust(5," ") for s in [chr(c) if c in range(0x20,0x80) else "0x0"+hex(c)[2] if c<0x10 else hex(c) for c in data]])
					self.dlog(f"recieved packet: {packet_string}")
				
			except socket.timeout:
				raise ClientDisconnectErr(f"Inactive timeout for user {self.user}. Disconnecting.")
				break	
			except socket.error:
				pass
			except ClientDisconnectErr as e:
				self.log(str(e))
				self.disconnect()
				self.server.purgeclient(self.conn)
				self.broadcast(f"{self.user} disconnected")
			except Exception as e:
				self.elog(traceback.format_exc(limit=None, chain=True))
				    
		
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
			with open(f"{self.modules.path}defaults.json","r") as f:
				self.data["ships"]=json.load(f)
				
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
		for root,dirs,files in os.walk(self.player_root): #search in players directory
			for d in dirs: #only search directories
				try:
					with open(f'{self.player_root}{d}/account.json', 'r') as f:
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
			os.makedirs(f'{self.player_root}{user}')
		except:
			self.elog("Directory already exists or error creating")
			pass
		with open(f'{self.player_root}{user}/account.json','w') as f:
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
		self.playerdir = f"{self.player_root}{self.user}/"
		self.playerfile = f"{self.playerdir}player.json"
		self.shipfile = f"{self.playerdir}ships.json"
		self.create_new_game()
		self.load_player()

	def log_in(self, data):
		user,passw = [ToUTF8(a) for a in bytes(data[1:]).split(b"\0",maxsplit=1)]
		print(user,passw)
		self.log(f"Logging in user: [{user}]")
		#if user in self.config.banned_users:
		#	self.send([ControlCodes["LOGIN"],ResponseCodes['BANNED']])
		#	self.log(f"[{user}] Banned user attempted login.")
		#	return
		passw_md5 = hashlib.md5(bytes(passw,'UTF-8')).hexdigest()  # Generate md5 hash of password
		try:
			for root, dirs, files in os.walk(self.player_root):  # search in players directory
				if user in dirs:
					try:
						self.dlog(f"Opening {self.player_root}{user}/account.json")
						with open(f"{self.player_root}{user}/account.json", 'r') as f:
							account = json.load(f)
							if account['passw_md5'] == passw_md5:
								self.user = user
								self.logged_in = True
								self.log(f"[{user}] has successfully logged in!")
								self.broadcast(f"{user} logged in")
								self.send([ControlCodes["LOGIN"],ResponseCodes['SUCCESS']])   # Log in successful
								self.playerdir = f"{self.player_root}{self.user}/"
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
		
	def kick(self):
		# send kick to client
		self.connected=False
		self.conn.shutdown(socket.SHUT_WR)
				    
	def version_check(self, data):
		client_version = data[1:4]
		gfx_version = data[4:6] # not used yet
		for i in range(3):
			if client_version[i] < self.config.settings["min-client"][i]:
				self.send([ControlCodes["VERSION_CHECK"],VersionCheckCodes['VERSION_ERROR']])
				self.disconnect()
				return
			if client_version[i] > self.config.settings["min-client"][i]:
				self.send([ControlCodes["VERSION_CHECK"],VersionCheckCodes['VERSION_OK']])
				self.log(f"{self.user}: client ok")
				return
		self.send([ControlCodes["VERSION_CHECK"],VersionCheckCodes['VERSION_OK']])
		self.log(f"{self.user}: client ok")
		
				  
			
				   

	def disconnect(self):
		if self.logged_in:
			self.save_player()
			self.logged_in = False
		self.connected = False
		self.server.purge = True
