#!/usr/bin/python           # This is server.py file

#TITrek server python3
#Authors:
# Anthony "ACagliano" Cagliano
# Adam "beckadamtheinventor" Beckingham
#This is the server program for Star Trek CE.

import socket               # Import socket module
import _thread
import hashlib
import json
import os,sys


from trekCodes import *

class Client:
    count = 0
    
    def __init__(self, addr):
        self.addr=(addr,port)
        self.closed = False
        self.logged_in = False
        self.user = ''
        Client.count += 1
        print('Got connection from', self.addr)
        sock.sendto(bytes(list(ResponseCodes["message"])+list('Thank you for connecting')))
    
    def handle_connection(self, data):
        while True:
            if not data:
                continue   #looks better imho :P
            if data.startswith(ControlCode["register"]):
                self.register(data[1:])
            elif data.startswith(ControlCode["login"]):
                self.log_in(data[1:])
            elif data.startswith(ControlCode["disconnect"]):
                self.disconnect()
                break
            elif data.startswith(ControlCode["servinfo"]):
                self.servinfo()
                break
            elif data.startswith(ControlCode["message"]):
                pass            # send a message to the server
            elif data.startswith(ControlCode["debug"]):
                print(str(data[1:])) # send a debug message to the server console
            elif data.startswith(ControlCode["ping"]):
                print("Ping? Pong!")
                sock.sendto(bytes(list(ResponseCodes["message"])+list("pong!")),self.addr)
            else:
                pass            # Will be handed off to game handler

    def servinfo(self):
        with open('servinfo.json', 'r+') as info_file:
            info = json.load(info_file)
            version = info['server']['version']
            client = info['server']['client_req']
            Max = info['server']['max_clients']
            output = list('{},{},{},{}'.format(version, client, Client.count, Max))
            #send the info packet prefixed with response code.
            sock.sendto(bytes(list(ResponseCodes['servinfo'])+output),self.addr)

    def register(self, data):
        user, passw, passw2 = data.split(b',')
        if passw != passw2:
            conn.send(RegisterError['invalid'])  # Error: passwords not same
            return
        passw_md5 = hashlib.md5(passw).hexdigest()  # Generate md5 hash of password
        with open('accounts.json', 'r+') as accounts_file:
            accounts = json.load(accounts_file)
            for account in accounts:
                if account['user'] == user:
                    conn.send(RegisterError['duplicate'])  # Error: user already exists
                    return
            accounts.append({'user':user, 'passw_md5': passw_md5})
            json.dump(accounts, accounts_file)
        self.user = user
        self.logged_in = True
        sock.sendto(RegisterError['success'],self.addr)       # Register successful
    
    def log_in(self, data):
        user, passw = data.split(b',')
        passw_md5 = hashlib.md5(passw).hexdigest()  # Generate md5 hash of password
        with open('accounts.json', 'r') as accounts_file:
            accounts = json.load(accounts_file)
            for account in accounts:
                if account['user'] == user:
                    if account['passw_md5'] == passw_md5:
                        self.user = user
                        self.logged_in = True
                        conn.send(LoginError['success'])   # Log in successful
                        return
                    else:
                        conn.send(LoginError['invalid'])  # Error: incorrect password
                        return
        sock.sendto(LoginError['missing'],self.addr)  # Error: user does not exist
            
    def disconnect(self):
        sock.sendto(DisconnectError['success'],self.addr) #Let the user know if disconnected. Might be useful eventually.
        Client.count -= 1
        self.closed = False

def writePidFile():
    pid = str(os.getpid())
    f = open('/var/run/trekserv.pid', 'w')
    f.write(pid)
    f.close()

def destroyPidFile():
    os.system('rm /var/run/trekserv.pid')

def servloop():
    online = True
    while online:
        for client in clients:  # Remove clients with terminated connections
            if client.closed:
                clients.remove(client)
            data, addr = sock.recvfrom(1024)     # Establish connection with client.
            if data:
                clients[addr] = Client(addr)
                _thread.start_new_thread(clients[-1].handle_connection, data)




s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)         # Create a socket object
host = socket.gethostname() # Get local machine name
port = 1701                # Reserve a port for your service.
clients = {}
s.bind((host, port))                 # Now wait for client connection.
writePidFile()
try:
    servloop()
except KeyboardInterrupt:
    s.close()

destroyPidFile()






# Elements to be done
# 1. Accept connections
# 2. Handle login/register (possibly SQL)
# 3. Handle logout, connection destruction

#test 3
