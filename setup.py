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


#Some useful error dictionaries
#These are mostly used for mnemonics
#Something the server returns upon returning from user input
InputError={
    "success":b'\000',
    "invalid":b'\001',
    "duplicate":b'\002',
    "missing":b'\003'
}
#returned from the registration routine
RegisterError={
    "success":b'\000\001\000',
    "invalid":b'\000\001\001',
    "duplicate":b'\000\001\002',
    "missing":b'\000\001\003'
}
#returned from the login routine
LoginError={
    "success":b'\000\002\000',
    "invalid":b'\000\002\001',
    "duplicate":b'\000\002\002',
    "missing":b'\000\002\003'
}
#returned from the disconect routine
DisconnectError={
    "success":b'\000\003\000'
}
#server control codes
ControlCode={
    "servresponse":b'\000',
    "register":b'\001',
    "login":b'\002',
    "disconnect":b'\003',
    "message":b'\00e',
    "debug":b'\00f',
    "servinfo":b'\0ff'
}
#server response codes. The same as server control codes for simplicity.
ResponseCodes={
    "register":b'\000\001',
    "login":b'\000\002',
    "disconnect":b'\000\003',
    "message":b'\000\00e',
    "debug":b'\000\00f',
    "servinfo":b'\000\0ff'
}


class Client:
    count = 0
    
    def __init__(self, conn, addr):
        self.conn = conn
        self.addr = addr
        self.closed = False
        self.logged_in = False
        self.user = ''
        Client.count += 1
        print('Got connection from', self.addr)
        conn.send(b'Thank you for connecting')
    
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
            conn.send(bytes(list(ResponseCodes['servinfo'])+output))

    def register(self, data):
        conn = self.conn
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
        conn.send(RegisterError['success'])       # Register successful
    
    def log_in(self, data):
        conn = self.conn
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
        conn.send(LoginError['missing'])  # Error: user does not exist
            
    def disconnect(self):
        conn = self.conn
        conn.send(DisconnectError['success']) #Let the user know if disconnected. Might be useful eventually.
        conn.close()
        Client.count -= 1
        self.closed = False

def writePidFile():
    pid = str(os.getpid())
    f = open('/var/run/trekserv.pid', 'w')
    f.write(pid)
    f.close()

def servloop():
    online = True
    while online:
        for client in clients:  # Remove clients with terminated connections
            if client.closed:
                clients.remove(client)
            data, addr = sock.recvfrom(1024)     # Establish connection with client.
            if data:
                clients[addr] = Client(data)
                _thread.start_new_thread(clients[Client.count-1].handle_connection, data)




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







# Elements to be done
# 1. Accept connections
# 2. Handle login/register (possibly SQL)
# 3. Handle logout, connection destruction

#test 3
