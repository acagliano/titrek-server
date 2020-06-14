#!/usr/bin/python3
# This is server.py file

#TITrek server python3
#Authors:
# Anthony "ACagliano" Cagliano
# Adam "beckadamtheinventor" Beckingham
#This is the server program for Star Trek CE.

import socket,multiprocessing,ctypes,hashlib,json,os,sys,time,math


from trekCodes import *
from generate import *
from trekSpace import *
from trek_vec3 import *

BANNED_USERS = []
BANNED_IPS = []

PACKET_DEBUG = False

def ToUTF8(dt):
    return str(bytes(dt),'UTF-8')

def FromSignedInt(n):
    if n&0x80:
        return 0x80-n
    else:
        return n

def ToSignedByte(n):
    if n<0:
        while abs(n)<-0x80: n+=0x80
        return 0x100+n%0x80
    else:
        while abs(n)>0x80: n-=0x80
        return n%0x80


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
        self.sock.settimeout(None)
        self.port = 51701                # Reserve a port for your service.
        self.clients = {}
        self.sock.bind(('', self.port))                 # Now wait for client connection.

    def run(self):
        self.online = True
        self.threads = [multiprocessing.Process(target=self.autoSaveHandler)]
        self.threads[0].start()
        self.main_thread = multiprocessing.Process(target=self.main)
        self.main_thread.start()
        self.console()
        self.stop()
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
        while self.online:
            self.sock.listen(1)
            conn, addr = self.sock.accept()
            self.clients[conn] = Client(conn,addr,self)
            self.threads.append(multiprocessing.Process(target=self.clients[conn].handle_connection))
            self.threads[-1].start()

    def autoSaveHandler(self):
        last_save_time = start_time = time.time()
        while self.online:
            cur_time = time.time()
            if (cur_time-last_save_time)>=600:
                last_save_time = time.time()
                self.log("Autosaving...")
                multiprocessing.Process(target=self.space.save,args=("space/data", )).start()
            time.sleep(60)


    def stop(self):
        self.log("Shutting down.")
        self.space.save("space/data")
        self.online = False
        for client in self.clients.keys():
            self.clients[client].disconnect()
            del self.clients[client]
        for thread in self.threads:
            thread.terminate()
        self.main_thread.terminate()
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
                line = input("")
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
                    multiprocessing.Process(target=self.space.save,args=("space/data", )).start()
                elif line[0]=="seed":
                    self.generator.seed(hash(line[1]))
                elif line[0]=="generate":
                    multiprocessing.Process(target=self.generate)
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
        self.max_acceleration = 5 #accelerate at a maximum of 100m/s^2
        if PACKET_DEBUG:
            self.log("Got client from ", addr)
        self.send([ControlCodes["MESSAGE"]]+list(b'Thank you for connecting'))

    def load_player(self):
        try:
            with open(self.playerfile) as f:
                self.data = json.load(f)
        except:
            self.data = {'x':0,'y':0,'z':0,'rot':0,'vx':0,'vy':0,'vz':0}
        self.pos = Vec3(self.data['x'],self.data['y'],self.data['z'])

    def __str__(self):
        return user+" ("+str(self.addr)+")"

    def send(self,data):
        if self.conn.send(bytes(data)):
            self.log("Sent packet:",data)
        else:
            self.log("Failed to send packet:",data)

    def handle_connection(self):
        while self.server.online:
            data = self.conn.recv(1024)
            if PACKET_DEBUG:
                o=[]
                for c in data:
                    if c>=0x20 and c<0x80: o.append(chr(c)+"   ")
                    elif c<0x10: o.append("\\x0"+hex(c)[2:])
                    else: o.append("\\x"+hex(c)[2:])
                self.log("recieved packet: ","".join(o))
            if not data:
                continue
            if len(data)==0:
                continue
            try:
                if data[0]==ControlCodes["REGISTER"]:
                    self.register(data)
                elif data[0]==ControlCodes["LOGIN"]:
                    self.log_in(data)
                elif data[0]==ControlCodes["DISCONNECT"]:
                    self.disconnect()
                elif data[0]==ControlCodes["SERVINFO"]:
                    self.servinfo()
                elif data[0]==ControlCodes["MESSAGE"]:
                    self.log("["+ToUTF8(self.user)+"]",ToUTF8(data[1:]))    # send a message to the server
                elif data[0]==ControlCodes["DEBUG"]:
                    self.server.log(ToUTF8(data[1:])) # send a debug message to the server console
                elif data[0]==ControlCode["PING"]:
                    self.server.log("Ping? Pong!")
                    self.send([ControlCodes["MESSAGE"]]+list(b"pong!"))
                elif data[0]==ControlCodes["PLAYER_MOVE"]:
                    G = FromSignedInt(data[1])
                    if G>=self.max_acceleration:
                        self.send([ControlCodes["DISCONNECT"]]+list(b"You were accelerating too fast. Hacking?\0"))
                        return
                    R1 = FromSignedInt(data[2])*math.pi/128
                    R2 = FromSignedInt(data[3])*math.pi/128
                    self.pos['vx']+=math.cos(R1)*math.cos(R2)*G
                    self.pos['vy']+=math.sin(R1)*G
                    self.pos['vz']+=-math.sin(R1)*G
                elif data[0]==ControlCodes["CHUNK_REQUEST"]:
                    out = []
                    R1 = FromSignedInt(data[1])*math.pi/128
                    R2 = FromSignedInt(data[2])*math.pi/128
                    R3 = FromSignedInt(data[3])*math.pi/128
                    Range = data[4]*1e6
                    for obj in self.space.gather_chunk(self.pos,Range):
                        x,y,z,r = obj['x'],obj['y'],obj['z'],obj['radius']
                        x-=self.pos['x']
                        y-=self.pos['y']
                        z-=self.pos['z']
                        x2 = (math.cos(R1)*x-math.sin(R1)*y)*(math.cos(R2)*x+math.sin(R2)*z)*256
                        y2 = (math.sin(R1)*x+math.cos(R1)*y)*(math.cos(R3)*y-math.sin(R3)*z)
                        z2 = (-math.sin(R2)*x+math.cos(R2)*z)*(math.sin(R3)*y+math.cos(R3)*z)*134
                        #only add object to frame data if it's visible
                        if (x2+r)>=-128 and (x2-r)<128 and (z2+r)>=-67 and (z2-r)<67 and y2>10:
                            out.append([Vec3(x2,y2,z2),obj])
                    out.sort(key = lambda x: x[0]['y'],reversed=True)
                    out2 = bytearray(1024)
                    out2[0]=ControlCodes['CHUNK_REQUEST']
                    if len(out)>127:
                        J = len(out)-127
                        out2[1]=127
                    else:
                        J = 0
                        out2[1]=len(out)
                    I=2
                    while J<len(out):
                        obj=out[J]
                        x,y,z = obj[0]['x'],obj[0]['y'],obj[0]['z']
                        out2[I]   = ToSignedByte(int(x))
                        out2[I+1] = ToSignedByte(int(z))
                        out2[I+2] = int(obj[1]['radius']/y)
                        for X in range(3):
                            out2[I+3+X] = obj[1]['colors'][X]
                        out2[I+6] = int(time.time()*100)&FF
                        I+=8
                        if I>=1024:
                            break
                    self.send(out2)
                elif data[0]==ControlCodes["POSITION_REQUEST"]:
                    x = int(self.pos['x'])
                    y = int(self.pos['y'])
                    z = int(self.pos['z'])
                    qx=x//1e15
                    qy=y//1e15
                    qz=z//1e15
                    if qx<0: qx=chr(0x61-qx)
                    else:    qx=chr(0x41+qx)
                    if qy<0: qy=chr(0x61-qy)
                    else:    qy=chr(0x41+qy)
                    if qz<0: qz=chr(0x61-qz)
                    else:    qz=chr(0x41+qz)
                    ax=(x//1e3)
                    ay=(y//1e3)
                    az=(z//1e3)
                    self.send(bytes([ControlCodes["POSITION_REQUEST"]])+\
                        b"Sector "+bytes([qx,qy,qz,0x20])+bytes("Coordinates x"+str(ax)+"y"+str(ay)+"z"+str(az),'UTF-8'))
                elif data[0]==ControlCodes["SENSOR_REQUEST"]:
                    R1 = FromSignedInt(data[1])*math.pi/128
                    out=[]
                    for obj in self.space.gather_chunk(1e9):
                        x,z,r,c = obj['x'],obj['z'],obj['radius'],obj['colors'][0]
                        x-=self.pos['x']
                        z-=self.pos['z']
                        x2=(math.cos(R1)*x-math.sin(R1)*z)*256
                        z2=(math.sin(R1)*x+math.cos(R1)*z)*134
                        if (x2+r)>=-128 and (x2-r)<128 and (z2+r)>=-67 and (z2-r)<67:
                            out.append([x2,z2,r/100,c])
                    out2 = bytearray(1024)
                    out2[0]=ControlCodes["SENSOR_REQUEST"]
                    if len(out)>254:
                        J=len(out)-254
                        out2[1]=254
                    else:
                        J=0
                        out2[1]=len(out)
                    I=2
                    while J<len(out):
                        obj=out[J]
                        x,z,r,c = obj
                        out2[I]   = ToSignedByte(int(x))
                        out2[I+1] = ToSignedByte(int(z))
                        out2[I+2] = ToSignedByte(int(r))
                        out2[I+3] = c&0xFF
                        I+=4
                        if I>=1024:
                            break
                    self.send(out2)
            except socket.error:
                pass
            except Exception as e:
                self.log("Internal Error:",e)
        self.send([ControlCodes["DISCONNECT"]])

    def servinfo(self):
        with open('servinfo.json', 'r+') as info_file:
            info = json.load(info_file)
            version = info['server']['version']
            client = info['server']['client_req']
            Max = info['server']['max_clients']
            output = list(b'{},{},{},{}'.format(version, client, Client.count, Max))
            #send the info packet prefixed with response code.
            self.send([ControlCodes['MESSAGE']]+output)

    def register(self, data):
        user,passw,email = [ToUTF8(a[:a.find(b"\0")]) for a in data[1:].split(b"\0",maxsplit=2)]
        self.log("Registering user:",user)
        passw_md5 = hashlib.md5(bytes(passw,'UTF-8')).hexdigest()  # Generate md5 hash of password
        with open('players/accounts.json', 'r') as accounts_file:
            accounts = json.load(accounts_file)
            for account in accounts:
                if account['user'] == user:
                    self.log("[",user,"] Already registered.")
                    self.send([ControlCodes["REGISTER"],ResponseCodes['DUPLICATE']])  # Error: user already exists
                    return
                elif account['email'] == email:
                    self.log("Email address",email,"has already been registered to an account.")
                    self.send([ControlCodes["REGISTER"],ResponseCodes['INVALID']])
            accounts.append({'user':user,'passw_md5':passw_md5,'email':email})
        with open('players/accounts.json','w') as accounts_file:
            json.dump(accounts, accounts_file)
        self.user = user
        self.logged_in = True
        self.log("[",user,"] has been successfuly registered!")
        self.send([ControlCodes["REGISTER"],ResponseCodes['SUCCESS']])       # Register successful
    
    def log_in(self, data):
        user,passw = [ToUTF8(a[:a.find(b"\0")]) for a in data[1:].split(b"\0",maxsplit=1)]
        self.log("Logging in user:",user)
        if user in BANNED_USERS:
            self.send([ControlCodes["LOGIN"],ResponseCodes['BANNED']])
            self.log("[",user,"] Banned user attempted login.")
            return
        passw_md5 = hashlib.md5(bytes(passw,'UTF-8')).hexdigest()  # Generate md5 hash of password
        try:
            with open('players/accounts.json', 'r') as accounts_file:
                accounts = json.load(accounts_file)
                for account in accounts:
                    if account['user'] == user:
                        if account['passw_md5'] == passw_md5:
                            self.user = user
                            self.logged_in = True
                            self.log("[",user,"] has successfuly logged in!")
                            self.send([ControlCodes["LOGIN"],ResponseCodes['SUCCESS']])   # Log in successful
                            self.playerfile = "players/data/"+self.user+".json"
                            return
                        else:
                            self.log("[",user,"] entered incorrect password.")
                            self.send([ControlCodes["LOGIN"],ResponseCodes['INVALID']])  # Error: incorrect password
                            return
        except:
            with open('players/accounts.json','w') as f:
                f.write("[]")
        self.log("[",user,"] could not find user.")
        self.send([ControlCodes["LOGIN"],ResponseCodes['MISSING']])  # Error: user does not exist

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
