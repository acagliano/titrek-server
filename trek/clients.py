import os,traceback,json,logging,socket,hashlib,re,bcrypt
from Cryptodome.Cipher import AES
from Cryptodome.Cipher import PKCS1_OAEP
from Cryptodome.PublicKey import RSA
import hmac

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
		except KeyError:
			print("ship save corrupted - resetting")
			self.create_new_game()
			self.load_modules()
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
		if data[0] in self.config.settings["debug"]:
			self.log(data)
		try:
			bytes_sent = self.conn.send(bytes(data[0:min(len(data), self.config.settings["packet-size"])]))
			if not bytes_sent:
				raise Exception("packet transmission error")
			print(f"Sent packet id {data[0]}; Packet length: {bytes_sent}")
			return bytes_sent
		except (BrokenPipeError, OSError): self.elog("send() called on a closed connection. This is probably intended behavior, but worth double checking.")
			
	def handle_connection(self):
		self.conn.settimeout(self.config.settings["idle-timeout"])
		while self.server.online:
			try:
				data = list(self.conn.recv(self.config.settings["packet-size"]))
				if not data or not self.connected:
					raise ClientDisconnectErr(f"{self.user} disconnected!")
				if not self.fw.filter_packet(self, data):
					raise ClientDisconnectErr(f"{self.user} disconnected, invalid packet.")
				if not len(data):
					continue
				if data[0]==ControlCodes["LOGIN"]:
					self.log_in(data)
				elif data[0]==ControlCodes["REGISTER"]:
					self.register(data)
				elif data[0]==ControlCodes["MAIN_REQ_UPDATE"]:
					self.init_client_transfer(data)
				elif data[0]==ControlCodes["MAIN_FRAME_NEXT"]:
					self.client_send_frame()
				elif data[0]==ControlCodes["REQ_SECURE_SESSION"]:
					self.init_secure_session()
				elif data[0]==ControlCodes["RSA_SEND_SESSION_KEY"]:
					self.setup_aes_session(data)
				elif data[0]==ControlCodes["PING"]:
						self.server.log("Ping? Pong!")
						self.send([ControlCodes["PING"]])
				elif self.logged_in:
					if data[0]==ControlCodes["GFX_REQ_UPDATE"]:
						self.init_gfx_transfer(data)
					elif data[0]==ControlCodes["GFX_FRAME_NEXT"]:
						self.gfx_send_frame()
					elif data[0]==ControlCodes["DEBUG"]:
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
				if data[0] in self.config.settings["debug"]:
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
				return
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
	
	def init_gfx_transfer(self, data):
		try:
			self.log("Loading graphics for client")
			user_gfx_dir = f"{self.playerdir}gfx/"
			default_gfx_dir = f"data/assets/ui/"
			selected_gfx_dir = default_gfx_dir
			self.client_side_sha256 = bytes(data[1:])
			if os.path.isdir(user_gfx_dir):
				if os.path.isfile(f"{user_gfx_dir}uiassets.bin"):
					self.log("Loading custom graphics")
					selected_gfx_dir = user_gfx_dir
			with open(f"{selected_gfx_dir}uiassets.bin", "rb") as f:
				self.gfx_bin = f.read()
				self.gfx_len = len(self.gfx_bin)
				self.gfx_hash = hashlib.sha256(bytes(self.gfx_bin)).digest()
				self.gfx_curr = 0
				self.send([ControlCodes['GFX_FRAME_START']]+u24(self.gfx_len))
		except IOError:
			output = list(bytes(f'error loading ui assets\0','UTF-8'))
			self.send([ControlCodes['MESSAGE']]+output)
			self.elog("File IO Error: [gfx_ui]")
			return
		except:
			self.elog(traceback.format_exc(limit=None, chain=True))
			
	def init_client_transfer(self, data):
		try:
			self.log("Loading client binary")
			client_bin = f"data/bins/TITREK.bin"
			self.client_side_sha256 = bytes(data[1:])
			with open(f"{client_bin}", "rb") as f:
				self.client_bin = f.read()
				self.client_len = len(self.client_bin)
				self.client_hash = hashlib.sha256(bytes(self.client_bin)).digest()
				self.client_curr = 0
				self.send([ControlCodes['MAIN_FRAME_START']]+u24(self.client_len))
				
		except IOError:
			output = list(bytes(f'error loading client bin\0','UTF-8'))
			self.send([ControlCodes['MESSAGE']]+output)
			self.elog("File IO Error: [client_bin]")
			return		
		
		
	def gfx_send_frame(self):
		if hmac.compare_digest(self.client_side_sha256, self.gfx_hash):
			self.send([ControlCodes['GFX_SKIP']])
			self.log("Hash match for graphics. Skipping download.")
			del self.gfx_bin
			del self.gfx_len
			del self.gfx_curr
			del self.gfx_hash
			del self.client_side_sha256
			return
		if self.gfx_curr >= self.gfx_len:
			self.send([ControlCodes['GFX_FRAME_DONE']]+list(self.gfx_hash))
			self.log("gfx download complete")
			del self.gfx_bin
			del self.gfx_len
			del self.gfx_curr
			del self.gfx_hash
			del self.client_side_sha256
			return
		data_offset = min(self.config.settings["packet-size"]-1, self.gfx_len - self.gfx_curr)
		data_to_send = self.gfx_bin[self.gfx_curr:self.gfx_curr+data_offset]
		print(f"Length of data to send (outer): {len(data_to_send)}\n")
		data_sent = self.send([ControlCodes['GFX_FRAME_IN']]+list(data_to_send))
		self.gfx_curr += (data_sent - 1)
	
	def client_send_frame(self):
		if hmac.compare_digest(self.client_side_sha256, self.client_hash):
			self.send([ControlCodes['MAIN_SKIP']])
			self.log("Hash match for binary. Skipping download.")
			del self.client_bin
			del self.client_len
			del self.client_curr
			del self.client_hash
			del self.client_side_sha256
			return
		if self.client_curr >= self.client_len:
			self.send([ControlCodes['MAIN_FRAME_DONE']]+list(self.client_hash))
			self.log("client download complete")
			del self.client_bin
			del self.client_len
			del self.client_curr
			del self.client_hash
			del self.client_side_sha256
			return
		data_offset = min(self.config.settings["packet-size"]-1, self.client_len - self.client_curr)
		data_to_send = self.client_bin[self.client_curr:self.client_curr+data_offset]
		data_sent = self.send([ControlCodes['MAIN_FRAME_IN']]+list(data_to_send))
		self.client_curr += (data_sent - 1)


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
   

	def log_in(self, data):
		try:
			iv = bytes(data[1:17])
			ct = bytes(data[17:])
			cipher = AES.new(self.aes_key, AES.MODE_CBC, iv=iv)
			padded_key = cipher.decrypt(ct)
			padding = padded_key[len(padded_key)-1]
			key = padded_key[0:-padding]
			for dir in os.listdir(self.player_root):
				try:
					
					self.dlog(f"Attempting to match key to user {dir}")
					with open(f"{self.player_root}{dir}/account.json", 'r') as f:
						account = json.load(f)
						hashed_pw=hashlib.sha512(bytes(key)).hexdigest()
						if hmac.compare_digest(hashed_pw, account['pubkey']):
							self.user = dir
							self.logged_in = True
							self.log(f"Key match for user {self.user}!")
							self.broadcast(f"{self.user} logged in")
							self.send([ControlCodes["LOGIN"],ResponseCodes['SUCCESS']])   # Log in successful
							self.playerdir = f"{self.player_root}{self.user}/"
							self.playerfile = f"{self.playerdir}player.json"
							self.shipfile = f"{self.playerdir}ships.json"
							self.load_player()
							return
				except IOError:
					self.dlog(f"Error reading account file for {user}")
					self.send([ControlCodes["MESSAGE"]]+list(b'server i/o error\0'))
					self.kick()
					return
			self.log(f"Could not match key. Sorry..")
			self.send([ControlCodes["LOGIN"],ResponseCodes['MISSING']])  # Error: user does not exist
			self.kick()
			return
		except:
			self.elog(traceback.format_exc(limit=None, chain=True))
		

	def kick(self):
		# send kick to client
		try:
			self.connected=False
			self.conn.shutdown(socket.SHUT_WR)
		except OSError: self.log("Error terminating the endpoint; It may have already disconnected")
		except: self.elog(traceback.format_exc(limit=None, chain=True))
				    
	def init_secure_session(self):
		try:
			self.rsa_key = RSA.generate(1024)
			self.rsa_key2 = RSA.generate(1024)
			pubkey_bytes = bytes(self.rsa_key.publickey().exportKey('DER'))[29:29+128]
			pubkey2_bytes = bytes(self.rsa_key2.publickey().exportKey('DER'))[29:29+128]
			print(f"{pubkey_bytes}\n{len(pubkey_bytes)}")
			print(f"{pubkey2_bytes}\n{len(pubkey2_bytes)}")
			self.send([ControlCodes["REQ_SECURE_SESSION"]] + list(pubkey_bytes))
			return
		except: self.elog(traceback.format_exc(limit=None, chain=True))
		
	def setup_aes_session(self, data):
		try:
			cipher = PKCS1_OAEP.new(self.rsa_key, hashAlgo=Crypto.Hash.SHA256)
			self.aes_key = cipher.decrypt(bytes(data[1:]))
			del self.rsa_key
			self.send([ControlCodes["RSA_SEND_SESSION_KEY"]])
			return
		except: self.elog(traceback.format_exc(limit=None, chain=True))
				  
			
				   

	def disconnect(self):
		if self.logged_in:
			self.save_player()
			self.logged_in = False
		self.connected = False
		self.server.purge = True
