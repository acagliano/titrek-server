#!/usr/bin/python3
# This is server.py file

#TITrek server python3
#Authors:
# Anthony "ACagliano" Cagliano
# Adam "beckadamtheinventor" Beckingham
#This is the server program for Star Trek CE.

import socket               # Import socket module
import _thread
import hashlib
import json
import os,sys,time


from trekCodes import *
from generate import *
from trekSpace import *
from trek_vec3 import *

BANNED_USERS = []
BANNED_IPS = []

PACKET_DEBUG = False

class Server:
    def __init__(self):
        for directory in ["logs","space/data","players","terrain","cache","missions","notes","bans"]:
            try:
                os.makedirs(directory)
            except:
                pass
        self.loadbans()
        self.mlogf = open("logs/messages.txt","a+")
        self.elogf = open("logs/errors.txt","a+")
        self.ilogf = open("logs/log.txt","a+")
        self.banlist = open("bans/userban.txt","a+")
        self.ipbanlist = open("bans/ipban.txt","a+")

        self.generator = Generator()
        self.space = Space(self.log)

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)         # Create a socket object
        self.port = 51701                # Reserve a port for your service.
        self.clients = {}
        self.sock.bind(('', self.port))                 # Now wait for client connection.
        self.sock.listen(5)
    
    def run(self):
        try:
            self.main()
        except KeyboardInterrupt:
            self.sock.close()

    
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

    def log(self,*args,**kwargs):
        print(*args,**kwargs)
        for arg in args:
            self.ilogf.write(str(arg)+" ")
        self.ilogf.write("\n")
    
    def elog(self,*args,**kwargs):
        self.log(*args,**kwargs)
        for arg in args:
            self.elogf.write(str(arg)+" ")
        self.elogf.write("\n")


    
    def main(self):
        _thread.start_new_thread(self.console, ())
        _thread.start_new_thread(self.autoSaveHandler, ())
        self.online = True
        while self.online:
            conn, addr = self.sock.accept()
            self.clients[conn] = Client(addr,conn,self)
            _thread.start_new_thread(self.clients[conn].handle_connection)
    
    def autoSaveHandler(self):
        last_save_time = start_time = time.time()
        while self.online:
            cur_time = time.time()
            if (cur_time-last_save_time)>=600:
                last_save_time = time.time()
                self.log("Autosaving...")
                _thread.start_new_thread(self.space.save, ("space/data", ))
            time.sleep(60)


    def stop(self):
        self.log("Shutting down.")
        self.space.save("space/data")
        self.online = False
        for client in self.clients.keys():
            self.clients[client].disconnect()
            del self.clients[client]
        self.banlist.close()
        self.ipbanlist.close()
        self.mlogf.close()
        self.elogf.close()
        self.ilogf.close()

    def kick(self,username):
        for conn in self.clients.keys():
            client = self.clients[conn]
            if client.username==username:
                client.disconnect()
                del self.clients[conn]

    def kickip(self,ip):
        for conn in self.clients.keys():
            client = self.clients[conn]
            if client.addr==ip:
                client.disconnect()
                del self.clients[conn]

    def ban(self,username):
        self.kick(username)
        self.banlist.write(username+"\n")
        self.loadbans()

    def ipban(self,ip):
        self.kickip(ip)
        self.ipbanlist.write(ip+"\n")
        self.loadbans()
    def backupAll(self,sname):
        try:
            os.makedirs("backups/"+sname)
        except:
            pass
        try:
            os.system("cp -r space backups/"+sname)
        except:
            self.log("WARNING: failed to backup")

    def restoreAll(self,sname):
        try:
            os.makedirs("space")
        except:
            pass
        try:
            os.system("cp -r backups/"+sname+" space")
        except:
            self.log("WARNING: failed to restore")


    def console(self):
        while True:
            try:
                line = input(">")
                self.ilogf.write(">"+line+"\n")
                line = line.split()
                if line[0]=="help":
                    try:
                        with open("helpfile.txt") as f:
                            print(f.read())
                    except:
                        print("No help document availible.")
                elif line[0]=="stop":
                    self.stop(); break
                elif line[0]=="save":
                    _thread.start_new_thread(self.space.save, ("space/data", ))
                elif line[0]=="seed":
                    self.generator.seed(hash(line[1]))
                elif line[0]=="generate":
                    _thread.start_new_thread(self.generate, ())
                elif line[0]=="kick":
                    self.kick(line[1])
                elif line[0]=="ban":
                    self.ban(line[1])
                elif line[0]=="ipban":
                    self.ipban(line[1])
                elif line[0]=="backup":
                    self.backupAll(line[1])
                elif line[0]=="restore":
                    self.restoreAll(line[1])
                elif line[0]=="list":
                    for client in self.clients.values():
                        print(str(client))
                elif line[0]=="debug-on":
                    PACKET_DEBUG = True
                elif line[0]=="debug-off":
                    PACKET_DEBUG = False
            except KeyboardInterrupt:
                self.stop()
                break
            except Exception as e:
                self.elog("Internal Error:",e)

    def generate(self):
        self.log("Generating space...")
        for gen in self.generator.generate_all():
            self.space.append(gen)
        self.log("Finished generating")

class Client:
    count = 0
    
    def __init__(self, conn, addr, server):
        self.conn = conn
        self.closed = False
        self.logged_in = False
        self.user = ''
        Client.count += 1
        self.server = server
        self.log=server.log
        if PACKET_DEBUG:
            self.log("Got client from ", addr)
        self.send(list(ControlCodes["message"])+list('Thank you for connecting'))

    def __str__(self):
        return user+" ("+str(self.addr)+")"

    def send(self,data):
        self.conn.send(bytes(data))

    def handle_connection(self):
        while True:
            data = self.conn.recv(1024)
            if PACKET_DEBUG:
                o=[]
                for c in data:
                    if c>=0x20 and c<0x80: o.append(chr(c)+"   ")
                    elif c<0x10: o.append("\\x0"+hex(c)[2:])
                    else: o.append("\\x"+hex(c)[2:])
                self.log("recieved packet: ","".join(o))
            if data[0]==ControlCodes["REGISTER"]:
                self.register(data[1:])
            elif data[0]==ControlCodes["LOGIN"]:
                self.log_in(data[1:])
            elif data[0]==ControlCodes["DISCONNECT"]:
                self.disconnect()
            elif data[0]==ControlCodes["SERVINFO"]:
                self.servinfo()
            elif data[0]==ControlCodes["MESSAGE"]:
                self.log("[",self.user,"]",data[1:])    # send a message to the server
            elif data[0]==ControlCodes["DEBUG"]:
                self.server.log(str(data[1:])) # send a debug message to the server console
            elif data[0]==ControlCode["PING"]:
                self.server.log("Ping? Pong!")
                self.send([ControlCodes["MESSAGE"]]+list("pong!"))
            elif data[0]==ControlCodes["PLAYER_MOVE"]:
                pass
            elif data[0]==ControlCodes["CHUNK_REQUEST"]:
                x = data[1]+data[2]*256+data[3]*65536
                y = data[4]+data[5]*256+data[6]*65536
                z = data[7]+data[8]*256+data[9]*65536
                chunk = self.space.gather_chunk(Vec3(x,y,z))
                out = []

    def servinfo(self):
        with open('servinfo.json', 'r+') as info_file:
            info = json.load(info_file)
            version = info['server']['version']
            client = info['server']['client_req']
            Max = info['server']['max_clients']
            output = list('{},{},{},{}'.format(version, client, Client.count, Max))
            #send the info packet prefixed with response code.
            self.send(list(ControlCodes['MESSAGE'])+output)

    def register(self, data):
        user, passw, passw2 = data.split(bytes([0]),maxsplit=3)
        self.log("Registering user:",user)
        if passw != passw2:
            self.log("[",user,"] Registration failed. Passwords do not match.")
            self.send([ControlCodes['INVALID']])  # Error: passwords not same
            return
        passw_md5 = hashlib.md5(passw).hexdigest()  # Generate md5 hash of password
        with open('accounts.json', 'r+') as accounts_file:
            accounts = json.load(accounts_file)
            for account in accounts:
                if account['user'] == user:
                    self.log("[",user,"] Already registered.")
                    self.send([ControlCodes['DUPLICATE']])  # Error: user already exists
                    return
            accounts.append({'user':user, 'passw_md5': passw_md5})
            json.dump(accounts, accounts_file)
        self.user = user
        self.logged_in = True
        self.log("[",user,"] has been successfuly registered!")
        self.send([ControlCodes['SUCCESS']])       # Register successful
    
    def log_in(self, data):
        user, passw = data.split(bytes([0]),maxsplit=2)
        self.log("Logging in user:",user)
        if user in BANNED_USERS:
            self.send([ControlCodes['BANNED']])
            self.log("[",user,"]Banned user attempted login.")
            return
        passw_md5 = hashlib.md5(passw).hexdigest()  # Generate md5 hash of password
        with open('accounts.json', 'r') as accounts_file:
            accounts = json.load(accounts_file)
            for account in accounts:
                if account['user'] == user:
                    if account['passw_md5'] == passw_md5:
                        self.user = user
                        self.logged_in = True
                        self.log("[",user,"] has successfuly logged in!")
                        self.send([ControlCodes['SUCCESS']])   # Log in successful
                        return
                    else:
                        self.log("[",user,"] entered incorrect password.")
                        self.send([ControlCodes['INVALID']])  # Error: incorrect password
                        return
        self.log("[",user,"] could not find user.")
        self.send([ControlCodes['MISSING']])  # Error: user does not exist

    def disconnect(self):
        self.send([ControlCodes['DISCONNECT']]) #Let the user know if disconnected. Might be useful eventually.
        Client.count -= 1
        self.closed = False

server = Server()
server.run()






# Elements to be done
# 1. Accept connections
# 2. Handle login/register (possibly SQL)
# 3. Handle logout, connection destruction

#test 3
