
#!/usr/bin/python           # This is server.py file

import socket               # Import socket module

class Client:
    count = 0
    def __init__(self, conn, addr):
        self.conn = conn
        self.addr = addr
        Client.count += 1
        print('Got connection from', self.addr)
        conn.send('Thank you for connecting')
    def disconnect(self):
        conn = self.conn
        conn.close()


s = socket.socket()         # Create a socket object
host = socket.gethostname() # Get local machine name
port = 12345                # Reserve a port for your service.
s.bind((host, port))        # Bind to the port
online = True

s.listen(5)                 # Now wait for client connection.
while online:
    c, addr = s.accept()     # Establish connection with client.
    if c:
        client.append(Client(c, addr))
                    # Close the connection

# Elements to be done
# 1. Accept connections
# 2. Handle login/register (possibly SQL)
# 3. Handle logout, connection destruction
