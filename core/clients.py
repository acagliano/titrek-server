import os,yaml,logging,sys,gzip,datetime,traceback,socket,ctypes,hashlib
from Cryptodome.Cipher import AES
from Cryptodome.Cipher import PKCS1_OAEP
from Cryptodome.Hash import SHA256
import hmac,asn1

class ClientDisconnect(Exception):
	pass

class PacketFilter(Exception):
	pass

class LoginError(Exception):
	pass

# class to handle incoming client connections
class Client:
	count = 0
	
	# stuff we import from the server instance
	server = None
	config = None
	log_handle = None
	meta = None
	map = None
	packets=None
	path = None
	
	def __init__(self, conn, addr):
		Client.count += 1
		self.conn = conn
		self.addr = addr
		self.ip = addr[0]
		self.port = addr[1]
		Client.packets = Client.meta["packets"]
		Client.config = Client.server.config
		Client.path = "data/players"
		
	def log(self, lvl, msg):
		Client.log_handle.log(lvl, msg)
	
	def send_bytes(self, data):
		try:
		
			# catch buffer overflow
			if (len(data)+3) > Client.config["packet-max"]:
				raise Exception(f"Send error, Packet id: {data[0]}: Packet + size word exceeds packet max spec.")
				
			# data length to 3-byte size prefix
			out = len(data).to_bytes(3, 'little')
			out += data
			
			written = self.conn.send(out)
			
			# check if bytes written doesn't match length of input + prefix
			if not written == (len(data)+3):
				raise Exception(f"Send error, Packet id: {data[0]}: Bytes written did not match input")
			
			# if we make it this far, print successful send
			self.log(logging.DEBUG, f"Packet id: {data[0]}, len + prefix: {written}, Sent successfully.")
					
			return bytes_sent
		except (BrokenPipeError, OSError):
			self.log(logging.ERROR, "Send error, Packet id: {data[0]}. Connection invalid.")
		except Exception as e:
			self.log(logging.ERROR, e)
			
	
	
	def listener(self):
		self.data_size = 0
		self.connected = True
		self.logged_in = False
		try:
			self.conn.settimeout(Client.config["conn-timeo"])
			while Client.server.online and self.connected:
			
				# read at most packet-max bytes from socket
				data = self.conn.recv(self.config["packet-max"])))
				
				# I remember reading that conn.recv returning null means conn closed
				if not data: break
				
				self.in_buf += data
				
				# if there is no size set, read size from in buffer
				# remove size from in buffer
				if not self.data_size:
					if len(self.in_buf) < 3: continue
					self.data_size = int.from_bytes(self.in_buf[0:3], "little")
					self.in_buf = self.in_buf[3:]
					
				# if not enough bytes have been read from socket, go back to waiting
				if len(self.in_buf) < self.data_size:
					continue
				
				# process packet
				self.parse_packet(self.in_buf)
				
				# remove processed data from in buffer
				# zero data size
				self.in_buf = self.in_buf[self.data_size:]
				self.data_size = 0
			self.conn.close()
			Client.count -= 1
			raise ClientDisconnect()
			
		except socket.timeout, ClientDisconnect:
			self.log(logging.INFO, f"{self.ip} has disconnected.")
			del Client.server.clients[self.conn]
			return
		except:
			self.log(logging.ERROR, traceback.format_exc(limit=None, chain=True))
			
			
	def parse_packet(self, data):
		try:
			for packet in Client.packets:
				if data[0] == packet["id"]:
					if ("req-login" in packet) and (packet["req-login"] == True):
						if not self.logged_in:
							raise PacketFilter(f"Priviledged packet from unpriviledged connection: {self.ip}")
					func = getattr(self, packet["func"], None)
					if not callable(func):
						raise Exception("Packet parse error. Func spec for packet id {data[0]} invalid.")
					func(data[1])
					return
			raise PacketFilter(f"Unknown packet from {self.ip}")
		except PacketFilter as e:
			self.log(logging.IDS_WARN, e)
			return
		except Exception as e
			self.log(logging.ERROR, e)
			return
			
	#############################
	### BEGIN PACKET HANDLERS ###
	#############################
	
	# send RSA key to client
	def rsa_send(self, data):
		ctl = Client.packets["SEND_RSA_KEY"]["id"].to_bytes(1, 'little')
		self.send_bytes(ctl + Client.server.rsa_pubkey)
		
	# receive AES key and HMAC key, RSA decrypt, and save
	def aes_recv(self, data):
		cipher = PKCS1_OAEP.new(Client.server.rsa_privkey, hashAlgo=SHA256)
		data_decrypted = cipher.decrypt(bytes(data[1:]))
		self.aes_key = data_decrypted[0:32]		# should be 32 bytes
		self.hmac_key = data_decrypted[32:]			# should be 16 bytes
		ctl = Client.packets["RECV_AES_KEY"]["id"].to_bytes(1, 'little')
		self.send_bytes(ctl)
		
	# receive login token, AES decrypt, and verify
	def login(self, data):
	
		try:
			# extract IV, ciphertext, and auth tag from packet
			iv = data[0:16]
			ct = data[16:-32]
			hmac_digest = data[-32:]
		
			# set response CTL code
			ctl = Client.packets["RECV_LOGIN_TOKEN"]["id"].to_bytes(1, 'little')
		
			# authenticate message before decryption. Discard if fails.
			hmac_verify = hmac.new(self.hmac_key, iv + ct, hashlib.sha256).digest()
			if not hmac.compare_digest(hmac_digest, hmac_verify):
				raise LoginError("HMAC validation error")
			
			# decrypt message and strip padding
			cipher = AES.new(self.aes_key, AES.MODE_CBC, iv=iv)
			token = cipher.decrypt(ct)
			padding = token[len(token)-1]	# expect PKCS7 padding
			token = token[0:-padding]		# strip padding
		
			# retrieve user to verify
			hostname_len = int.from_bytes(token[7:10], "little")
			user_field_pos = 7 + 3 + hostname_len
			username_len = int.from_bytes(token[user_field_pos:user_field_pos+3], "little")
			username = token[user_field_pos+3:user_field_pos+3+username_len]
			with open(f"{Client.path}/{username}/TrekId00.8xv", 'rb') as f:
				saved_key = f.read()[74:-2]
				if not hmac.compare_digest(token, saved_key):
					raise LoginError("Invalid login token")
					
				self.user = username
				self.logged_in = True
				self.log(logging.DEBUG, f"Key match for user {self.user}!")
				self.broadcast(f"{self.user} logged in")
				self.send(ctl + b"\x00")   # Log in successful
				self.playerdir = f"{Client.path}/{self.user}"
				self.playerfile = f"{self.playerdir}/player.json"
				self.shipfile = f"{self.playerdir}/ships.json"
				self.load_player()
				return
				
		except LoginError as e:
			self.log(logging.INFO, e)
			self.send(ctl + b"\x01" + e)   	# ctl + login resp error + msg
			self.connected = False
			return
		except IOError:
			self.log(logging.ERROR, "Failed to open user keyfile")
			self.connected = False
			return
		except: self.log(logging.ERROR, traceback.format_exc(limit=None, chain=True))
			
		
		
	
	
	def disconnect(self):
		Client.count -= 1
		
		
	
	
