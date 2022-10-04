import os,yaml,logging,sys,gzip,datetime,traceback,socket,ctypes,hashlib
from Cryptodome.Cipher import AES
from Cryptodome.Cipher import PKCS1_OAEP
from Cryptodome.Hash import SHA256
import hmac

class ClientDisconnect(Exception):
	pass

class PacketFilter(Exception):
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
	
	def __init__(self, conn, addr):
		Client.count += 1
		self.conn = conn
		self.addr = addr
		self.ip = addr[0]
		self.port = addr[1]
		Client.packets = Client.meta["packets"]
		Client.config = Client.server.config
		
		
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
			self.log(logging.DEBUG, f"Packet id: {data[0]}, len + prefix: {written}, Sent successfully.
					
			return bytes_sent
		except (BrokenPipeError, OSError): self.elog("send() called on a closed connection. This is probably intended behavior, but worth double checking.")
			
	def handle_connection(self):
		except:
			self.log(logging.ERROR, traceback.format_exc(limit=None, chain=True))
	
	
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
					func()
					return
			raise PacketFilter(f"Unknown packet from {self.ip}")
		except PacketFilter as e:
			self.log(logging.IDS_WARN, e)
			return
		except Exception as e
			self.log(logging.ERROR, e)
			return
		
	### BEGIN PACKET HANDLERS
	def rsa_send(self):
		rsa_key = Client.server.rsa_pubkey
		
	
	
	def disconnect(self):
		Client.count -= 1
