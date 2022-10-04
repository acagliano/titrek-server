import os,yaml,logging,sys,gzip,datetime,traceback,socket,ctypes,hashlib
from Cryptodome.Cipher import AES
from Cryptodome.Cipher import PKCS1_OAEP
from Cryptodome.Hash import SHA256
import hmac


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
	
	def __init__(self, conn, addr):
		Client.count += 1
		self.conn = conn
		self.addr = addr
		self.ip = addr[0]
		self.port = addr[1]
		Client.packets = Client.meta["packets"]
		Client.config = Client.server.config
		return
		
		
	def log(self, lvl, msg):
		Client.log_handle.log(lvl, msg)
		
	
	def listener(self):
		self.data_size = 0
		try:
			self.conn.settimeout(Client.config["conn-timeo"])
			while Client.server.online:
			
				# read at most packet-max bytes from socket
				data = self.conn.recv(self.config["packet-max"])))
				
				if not data:
					raise Exception(f"{self.addr} appears to have disconnected.")
					# I remember reading that conn.recv returning null means conn closed
					break
				
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
			del Client.server.clients[self.conn]
			return
			
		except socket.timeout:
			raise Exception(f"{self.addr} timed out. Disconnecting.")
			del Client.server.clients[self.conn]
			
			
	def parse_packet(self, data):
		return
		
		
	def disconnect(self):
		Client.count -= 1
