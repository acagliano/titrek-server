
# class to handle incoming client connections
class Client:
	count = 0
	server = None
	log_handle = None
	def __init__(self, conn, addr):
		Client.count += 1
		self.conn = conn
		self.addr = addr
		self.ip = addr[0]
		self.port = addr[1]
		return
		
		
	def log(self, lvl, msg):
		Client.log_handle.log(lvl, msg)
		
	
	def listener(self):
		return
		
		
	def disconnect(self):
		Client.count -= 1
