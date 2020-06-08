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

class Server:
    def __init__(self):
        for directory in ["logs","space","players","terrain","cache","missions","notes","bans"]:
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

        socket.settimeout(0)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)         # Create a socket object
        self.host = socket.gethostname() # Get local machine name
        self.port = 1701                # Reserve a port for your service.
        self.clients = {}
        self.sock.bind((self.host, self.port))                 # Now wait for client connection.
    
    def run(self):
        try:
            self.main()
        except KeyboardInterrupt:
            self.s.close()

    
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
            self.ilogf.write(str(arg)+" ")
        self.ilogf.write("\n")
    
    def elog(self,*args):
        self.log(*args)
        for arg in args:
            self.elogf.write(str(arg)+" ")
        self.elogf.write("\n")


    
    def main(self):
        _thread.start_new_thread(self.console, ())
        self.online = True
        while self.online:
            for conn in self.clients.keys():
                if client.closed:
                    del self.clients[conn]
                self.sock.listen(1)
                try:
                    conn, addr = self.sock.accept()
                    self.clients[conn] = Client(addr,conn,self)
                except:
                    pass
                data = conn.recv(1024)
                if len(data):
                    client=self.clients[conn]
                    if addr in BANNED_IPS:
                        conn.send(OutboundCodes['BANNED'])
                    _thread.start_new_thread(self.clients[conn].handle_connection, conn)


    def stop(self):
        self.log("Shutting down.")
        self.space.save("space")
        self.online = False
        for client in self.clients:
            client.disconnect()
            self.clients.remove(client)
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
    
    def backup(self,sname,x,y,z):
        fname = "x"+str(x)+"y"+str(y)+"z"+str(z)+".dat"
        try:
            with open("space/"+fname,"rb") as f:
                pass
            try:
                os.makedirs("backups/"+sname+"/space")
            except:
                pass
            os.system("cp space/"+fname+" backups/"+sname+"/space/"+fname)
        except:
            self.log("WARNING: failed to back up")

    def restore(self,sname,x,y,z):
        fname = "x"+str(x)+"y"+str(y)+"z"+str(z)+".dat"
        try:
            with open("backups/space/"+fname,"rb") as f:
                pass
            try:
                os.makedirs("space")
            except:
                pass
            os.system("cp backups/"+sname+"/"+fname+" space/"+fname)
        except:
            self.log("WARNING: failed to restore")

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
                    self.space.save("space/data")
                elif line[0]=="seed":
                    self.generator.seed(hash(line[1]))
                elif line[0]=="gen":
                    x,y,z=float(line[1])*1e6,float(line[2])*1e6,float(line[3])*1e6
                    self.space.append(self.generator.generate(Vec3(x,y,z)))
                elif line[0]=="kick":
                    self.kick(line[1])
                elif line[0]=="ban":
                    self.ban(line[1])
                elif line[0]=="ipban":
                    self.ipban(line[1])
                elif line[0]=="backup":
                    self.backup(line[1],int(line[2]),int(line[3]),int(line[4]))
                elif line[0]=="restore":
                    self.restore(line[1],int(line[2]),int(line[3]),int(line[4]))
                elif line[0]=="backup-all":
                    self.backupAll(line[1])
                elif line[0]=="restore-all":
                    self.restoreAll(line[1])
            except KeyboardInterrupt:
                self.stop()
                break
            except Exception as e:
                self.elog("Internal Error:",e)


class Client:
    count = 0
    
    def __init__(self, conn, addr, server):
        self.conn = conn
        self.closed = False
        self.logged_in = False
        self.user = ''
        Client.count += 1
        self.server = server
        server.log('Got connection from', self.addr)
        conn.send(bytes(list(OutboundCodes["message"])+list('Thank you for connecting')))

    def handle_connection(self,data):
        while True:
            if not data:
                continue   #looks better imho :P
            if data[3]==InboundCodes["REGISTER"]:
                self.register(data[1:])
            elif data[3]==InboundCodes["LOGIN"]:
                self.log_in(data[1:])
            elif data[3]==InboundCodes["DISCONNECT"]:
                self.disconnect()
                break
            elif data[3]==InboundCodes["SERVINFO"]:
                self.servinfo()
            elif data[3]==InboundCodes["MESSAGE"]:
                pass    # send a message to the server
            elif data[3]==InboundCodes["DEBUG"]:
                self.server.log(str(data[1:])) # send a debug message to the server console
            elif data[3]==ControlCode["PING"]:
                self.server.log("Ping? Pong!")
                self.conn.send(bytes([OutboundCodes["MESSAGE"]]+list("pong!")))
            elif data[3]==InboundCodes["PLAYER_MOVE"]:
                pass
            elif data[3]==InboundCodes["CHUNK_REQUEST"]:
                x = data[4]+data[5]*256+data[6]*65536
                y = data[7]+data[8]*256+data[9]*65536
                z = data[10]+data[11]*256+data[12]*65536
                self.space.gather_chunk(Vec3(x,y,z))

    def servinfo(self):
        with open('servinfo.json', 'r+') as info_file:
            info = json.load(info_file)
            version = info['server']['version']
            client = info['server']['client_req']
            Max = info['server']['max_clients']
            output = list('{},{},{},{}'.format(version, client, Client.count, Max))
            #send the info packet prefixed with response code.
            self.conn.send(bytes(list(TypeCodes['MESSAGE'])+output))

    def register(self, data):
        user, passw, passw2 = data.split(b',')
        if passw != passw2:
            self.conn.send(RegisterError['INVALID'])  # Error: passwords not same
            return
        passw_md5 = hashlib.md5(passw).hexdigest()  # Generate md5 hash of password
        with open('accounts.json', 'r+') as accounts_file:
            accounts = json.load(accounts_file)
            for account in accounts:
                if account['user'] == user:
                    self.conn.send(ResponseCodes['DUPLICATE'])  # Error: user already exists
                    return
            accounts.append({'user':user, 'passw_md5': passw_md5})
            json.dump(accounts, accounts_file)
        self.user = user
        self.logged_in = True
        self.conn.send(ResponseCodes['SUCCESS'])       # Register successful
    
    def log_in(self, data):
        user, passw = data.split(b',')
        if user in BANNED_USERS:
            self.conn.send(ResponseCodes['BANNED'])
            return
        passw_md5 = hashlib.md5(passw).hexdigest()  # Generate md5 hash of password
        with open('accounts.json', 'r') as accounts_file:
            accounts = json.load(accounts_file)
            for account in accounts:
                if account['user'] == user:
                    if account['passw_md5'] == passw_md5:
                        self.user = user
                        self.logged_in = True
                        self.conn.send(ResponseCodes['SUCCESS'])   # Log in successful
                        return
                    else:
                        self.conn.send(ResponseCodes['INVALID'])  # Error: incorrect password
                        return
        self.conn.send(ResponseCodes['MISSING'])  # Error: user does not exist

    def disconnect(self):
        self.conn.send(OutboundCodes['SUCCESS']) #Let the user know if disconnected. Might be useful eventually.
        Client.count -= 1
        self.closed = False

server = Server()
server.run()






# Elements to be done
# 1. Accept connections
# 2. Handle login/register (possibly SQL)
# 3. Handle logout, connection destruction

#test 3
