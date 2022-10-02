
# class to handle incoming client connections
class Client:
	count = 0
	
	def __init__(self, conn, addr, server):
		Client.count += 1
		return
