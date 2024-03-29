import os,traceback,json,logging,socket,hashlib,re,math,yaml
from Crypto.Cipher import AES
from Crypto.Cipher import PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Hash import SHA256
import hmac

from trekcore.codes import *
from trekcore.server import *
from trekcore.utils.logging import *
from trekcore.utils.filter import *
from trekcore.utils.modules import *
from trekcore.math.vec3 import *
from trekcore.utils.util import *

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
		self.data_stream = b''
		self.data_size = 0
		Client.rsa_key_size = self.config.settings["rsa-key-size"]
		self.player_root=f"{self.server.server_root}{self.config.settings['gamedata']}/players/"
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
			for m in self.data["ships"]["ship0"]:
				j=self.modules.load_module(m)
				
		except KeyError:
			print("ship save corrupted - resetting")
			self.create_new_game()
			self.load_modules()
		except:
			self.elog(traceback.format_exc(limit=None, chain=True))



	def save_player(self):
		try:
			os.makedirs(f"{self.player_root}{self.user}")
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
		if (len(data)+3) > self.config.settings["packet-size"]:
			elf.elog("Error: Packet buffer overflow. Failed to send packet!")
			return
		try:
			to_send = bytes(u24(len(data)))
			bytes_out = bytes(data[0:min(len(data), self.config.settings["packet-size"])])
					
			bytes_sent = self.conn.send(to_send + bytes_out)
			if not bytes_sent:
				raise Exception("packet transmission error")
			print(f"Sent packet id {data[0]}; Packet length: {bytes_sent}")
			return bytes_sent
		except (BrokenPipeError, OSError): self.elog("send() called on a closed connection. This is probably intended behavior, but worth double checking.")
			
	def handle_connection(self):
		self.conn.settimeout(self.config.settings["idle-timeout"])
		while self.server.online:
			try:
				self.data_stream += bytes(list(self.conn.recv(self.config.settings["packet-size"])))
				
				# check if data_size is unset, if it is, read size
				if not self.data_size:
					if len(self.data_stream) < 3: return
					self.data_size = int.from_bytes(self.data_stream[0:3], "little")
					self.data_stream = self.data_stream[3:]
				
				#print(f"{self.data_size} bytes reqd, stream size {len(self.data_stream)} bytes")
				# if length of data is unsufficient, return
				if len(self.data_stream) < self.data_size:
					return
				
				# duplicate data for internal use
				data = list(self.data_stream)
				
				# reset data size and advance the internal data block
				self.data_stream = self.data_stream[self.data_size:]
				self.data_size = 0
				
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
					elif data[0]==ControlCodes["MESSAGE"]:
						if len(data[1:]) > 1:
							msg = ToUTF8(data[1:-1])
							self.broadcast(f"{msg}", self.user)
							self.log(f"{self.user}: {msg}")    # send a message to the server
					elif data[0]==ControlCodes["LOAD_SHIP"]:
						odata = []
						for m in self.data["ships"]["ship0"]:
							odata.extend(self.load_shipmodule(m))
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
		rdata = []
		m = self.data["ships"]["ship0"][m]
		module_name = m["name"].encode('ascii').ljust(11, b'\0')
		rdata.extend(u8(m["type"]))
		rdata.extend(u8(m["status"]))
		rdata.extend([x.decode("ascii") for x in module_name if len(module_name)])
		rdata.extend(u8(m["stats"]["health"]["current"]))
		rdata.extend(u8(m["stats"]["health"]["max"]))
		rdata.extend(u8(m["stats"]["power"]["draw"]))
		rdata.extend(u8(m["stats"]["power"]["required"]))
		rdata.extend(self.load_module_sprite(m["icon"])) # was missing a closing bracket here Cags :p
		return rdata
					  
	def load_module_sprite(self, iconfilename):
		iconfilename = os.path.splitext(iconfilename)[0]
		default_search_path = f"{self.modules.internal_gfx_path}/{iconfilename}"
		try:
			os.makedirs("/tmp/titrek/gfx/modules")
		except: pass
		try:
			tmpfile_search_path = f"/tmp/titrek/gfx/modules/{iconfilename}.bin"
			tosend=[]
			if(os.path.exists(tmpfile_search_path)):
				with open(tmpfile_search_path, "rb") as f:
					  tosend = f.read()
			else:
				with open("convimg.yaml",'w') as convf:
					convf.write(f"""
converts:
    - name: tmpimg
      palette: xlibc
      images:
        - {default_search_path}
outputs:
    - type: bin
      converts:
        - tmpimg
      include-file: /dev/null
      directory: /tmp/titrek/gfx/modules/
""")
				os.system("data/bin/convimg")
				with open(tmpfile_search_path,'rb') as f:
					tosend = f.read()
				os.remove("convimg.yaml")
			if len(tosend) < 66:
				return list(tosend) + [0]*(66-len(tosend))
			return list(tosend)
		except Exception as e:
			self.elog(traceback.format_exc(limit=None, chain=True))
				
					  

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
			user_gfx_dir = f"{self.playerdir}gfx"
			default_gfx_dir = f"trekcore/defaults/assets"
			selected_gfx_dir = default_gfx_dir
			self.client_side_sha256 = bytes(data[1:])
			if os.path.isdir(user_gfx_dir):
				if os.path.isfile(f"{user_gfx_dir}/uxassets.bin"):
					self.log("Loading custom graphics")
					selected_gfx_dir = user_gfx_dir
			with open(f"{selected_gfx_dir}/uxassets.bin", "rb") as f:
				self.gfx_bin = f.read()
				self.gfx_len = len(self.gfx_bin)
				self.gfx_hash = hashlib.sha256(bytes(self.gfx_bin)).digest()
				if hmac.compare_digest(self.client_side_sha256, self.gfx_hash):
					self.send([ControlCodes['GFX_SKIP']])
					self.log("Hash match for graphics. Skipping download.")
					del self.gfx_bin
					del self.gfx_len
					del self.gfx_hash
					del self.client_side_sha256
					return
				else:
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
			client_bin = f"data/client-binaries/TITREK.bin"
			self.client_side_sha256 = bytes(data[1:])
			with open(f"{client_bin}", "rb") as f:
				self.client_bin = f.read()
				self.client_len = len(self.client_bin)
				self.client_hash = hashlib.sha256(bytes(self.client_bin)).digest()
				if hmac.compare_digest(self.client_side_sha256, self.client_hash):
					self.send([ControlCodes['MAIN_SKIP']])
					self.log("Hash match for binary. Skipping download.")
					del self.client_bin
					del self.client_len
					del self.client_hash
					del self.client_side_sha256
					return
				else: 
					self.client_curr = 0
					self.send([ControlCodes['MAIN_FRAME_START']]+u24(self.client_len))
				
		except IOError:
			output = list(bytes(f'error loading client bin\0','UTF-8'))
			self.send([ControlCodes['MESSAGE']]+output)
			self.elog("File IO Error: [client_bin]")
			return
		except:
			self.elog(traceback.format_exc(limit=None, chain=True))
		
		
	def gfx_send_frame(self):
		if self.gfx_curr >= self.gfx_len:
			self.send([ControlCodes['GFX_FRAME_DONE']]+list(self.gfx_hash))
			self.log("gfx download complete")
			del self.gfx_bin
			del self.gfx_len
			del self.gfx_curr
			del self.gfx_hash
			del self.client_side_sha256
			return
		data_offset = min(self.config.settings["packet-size"]-4, self.gfx_len - self.gfx_curr)
		data_to_send = self.gfx_bin[self.gfx_curr:self.gfx_curr+data_offset]
		print(f"Length of data to send (outer): {len(data_to_send)}\n")
		data_sent = self.send([ControlCodes['GFX_FRAME_IN']]+list(data_to_send))
		self.gfx_curr += (data_sent - 4)
	
	def client_send_frame(self):
		if self.client_curr >= self.client_len:
			self.send([ControlCodes['MAIN_FRAME_DONE']]+list(self.client_hash))
			self.log("client download complete")
			del self.client_bin
			del self.client_len
			del self.client_curr
			del self.client_hash
			del self.client_side_sha256
			return
		data_offset = min(self.config.settings["packet-size"]-4, self.client_len - self.client_curr)
		data_to_send = self.client_bin[self.client_curr:self.client_curr+data_offset]
		data_sent = self.send([ControlCodes['MAIN_FRAME_IN']]+list(data_to_send))
		self.client_curr += (data_sent - 4)


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
			self.data["ships"] = {}
			self.data["ships"]["ship0"] = {}
			for m in self.modules.defaults["modules"]:
				self.data["ships"]["ship0"][m] = self.modules.module_data[m]
			
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
			key = cipher.decrypt(ct)
			padding = key[len(key)-1]
			key = key[0:-padding]
			self.log(f"searching for user with matching key.")
			for dir in os.listdir(self.player_root):
				try:
					with open(f"{self.player_root}{dir}/TrekId00.8xv", 'rb') as f:
						saved_key = f.read()[74:-2]
						if hmac.compare_digest(key, saved_key):
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
					self.log(f"Error opening file {self.player_root}{dir}/TrekId00.8xv.")
					continue
			self.log(f"Could not find a match for the given key. Sorry..")
			self.send([ControlCodes["LOGIN"],ResponseCodes['INVALID']])  # Error: user does not exist
			self.kick()
			return
		except:
			self.elog(traceback.format_exc(limit=None, chain=True))
		

	def kick(self):
		# send kick to client
		try:
			self.connected=False
			self.conn.shutdown(socket.SHUT_WR)
			self.log(f"{self.user} has been kicked.")
		except OSError: self.log("Error terminating the endpoint; It may have already disconnected")
		except: self.elog(traceback.format_exc(limit=None, chain=True))
				    
	def init_secure_session(self):
		try:
			self.rsa_key = RSA.generate(Client.rsa_key_size)
			rsa_key_size = int(math.ceil(Client.rsa_key_size/8))
			print(rsa_key_size)
			pubkey_bytes = bytes(self.rsa_key.publickey().exportKey('DER'))
			pubkey_bytes = pubkey_bytes[-5 - rsa_key_size:-5]
			self.send([ControlCodes["REQ_SECURE_SESSION"]] + u24(rsa_key_size) + list(pubkey_bytes))
			return
		except: self.elog(traceback.format_exc(limit=None, chain=True))
		
	def setup_aes_session(self, data):
		try:
			cipher = PKCS1_OAEP.new(self.rsa_key, hashAlgo=SHA256)
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
