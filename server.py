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

SERVERPASSWORD = "titrek-eZ80TICE"
BANNED_USERS = []
BANNED_IPS = []

class Server:
    def __init__(self):
        for directory in ["logs","space","players","terrain","cache","missions","notes","bans"]:
            try:
                os.makedirs(directory)
            except:
                pass
        self.loadbans()
        self.mlog = open("logs/messages.txt","a+")
        self.elog = open("logs/errors.txt","a+")
        self.ilog = open("logs/log.txt","a+")
        self.banlist = open("bans/userban.txt","a+")
        self.ipbanlist = open("bans/ipban.txt","a+")

        self.s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)         # Create a socket object
        self.host = socket.gethostname() # Get local machine name
        self.port = 1701                # Reserve a port for your service.
        self.clients = {}
        self.s.bind((self.host, self.port))                 # Now wait for client connection.
    
    def run(self):
        #writePidFile()
        try:
            self.main()
        except KeyboardInterrupt:
            self.s.close()

        #destroyPidFile()
    
    def loadbans(self):
        try:
            with open("bans/userban.txt") as f:
                BANNED_USERS = f.read().splitlines()
        except:
            pass
        try:
            with open("bans/ipban.txt") as f:
                BANNED_IPS = f.read().splitlines()
        except:
            pass
    
    def log(self,*args):
        print(*args)
        for arg in args:
            self.ilog.write(arg+"\n")
    
    def main(self):
        _thread.start_new_thread(self.console, ())
        self.online = True
        while self.online:
            for client in self.clients:  # Remove clients with terminated connections
                if client.closed:
                    self.clients.remove(client)
                data, addr = sock.recvfrom(1024)     # Establish connection with client.
                if data:
                    if addr in BANNED_IPS:
                        sock.sendto(LoginError['banned'],addr)
                    self.clients[addr] = Client(addr)
                    _thread.start_new_thread(self.clients[addr].handle_connection, data, self.handle_event)


    def stop(self):
        self.log("Shutting down.")
        self.online = False
        for client in self.clients:
            client.disconnect()
            self.clients.remove(client)
        self.banlist.close()
        self.ipbanlist.close()
        self.mlog.close()
        self.elog.close()
        self.ilog.close()

    def handle_event(self,event):
        event = str(event)
        if event.startswith("stop-server "+SERVERPASSWORD):
            self.stop()
    
    def kick(self,username):
        for client in self.clients:
            if client.username==username:
                client.disconnect()
                self.clients.remove(client)

    def kickip(self,ip):
        for client in self.clients:
            if client.addr==ip:
                client.disconnect()
                self.clients.remove(client)

    def ban(self,username):
        self.kick(username)
        self.banlist.write(username+"\n")
        self.loadbans()

    def ipban(self,ip):
        self.kickip(ip)
        self.ipbanlist.write(ip+"\n")
        self.loadbans()
    
    def console(self):
        while True:
            try:
                line = input(">")
                self.ilog.write(">"+line+"\n")
                line = line.split()
                if line[0]=="help":
                    try:
                        with open("helpfile.txt") as f:
                            self.log(f.read())
                    except:
                        print("No help document availible.")
                elif line[0]=="stop":
                    self.stop(); break
                elif line[0]=="gen":
                    self.generator.gen(int(line[1]),Vec3(line[2],line[3],line[4]))
                elif line[0]=="kick":
                    self.kick(line[1])
                elif line[0]=="ban":
                    self.ban(line[1])
                elif line[0]=="ipban":
                    self.ipban(line[1])
            except KeyboardInterrupt:
                self.stop(); break
            except Exception as e:
                self.log("Internal Error:",e,"\nprobable malformed input.")


class Client:
    count = 0
    
    def __init__(self, addr, server):
        self.addr=(addr,port)
        self.closed = False
        self.logged_in = False
        self.user = ''
        Client.count += 1
        self.server = server
        server.log('Got connection from', self.addr)
        sock.sendto(bytes(list(ResponseCodes["message"])+list('Thank you for connecting')))
    
    def handle_connection(self,data):
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
                pass    # send a message to the server
            elif data.startswith(ControlCode["debug"]):
                self.server.log(str(data[1:])) # send a debug message to the server console
            elif data.startswith(ControlCode["ping"]):
                self.server.log("Ping? Pong!")
                sock.sendto(bytes(list(ResponseCodes["message"])+list("pong!")),self.addr)
            else:
                self.server.handle_event(data)            # Will be handed off to game handler

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
        if user in BANNED_USERS:
            conn.send(LoginError['banned'])
            return
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


server = Server()
server.run()






# Elements to be done
# 1. Accept connections
# 2. Handle login/register (possibly SQL)
# 3. Handle logout, connection destruction

#test 3
