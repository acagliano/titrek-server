# This file is the beginning of a self-contained, custom firewall
# for the TI-Trek server. It uses a JSON rules file, containing
# check names, methods, and actions.

# "check" name of the test to be done
#  -----(also the name of the file in which the method can be found)
# "method" the self.method to call to perform the check
# "failaction" the action to take should the packet fail the check
# Might add the ability to pass a format specifier to the filter, such that our sanity checks...
# ... can know what type of data to expect in different packet segments

# Not yet implemented, but this module will be designed as a class
# that can be invoked optionally, should a user wish to provide it on their own server

import os,json,traceback,importlib
from trek_codes import *

class TrekFilter:
    version="1.0b"
    status=False
    offenders={}
    enable_sanity=True
    special_characters = [bytes(a,'UTF-8') for a in ["/","\\","#","$","%","^","&","*","!","~","`","\"","|"]] + \
					[bytes([a]) for a in range(1,0x20)] + [bytes([a]) for a in range(0x7F,0xFF)]
    
    def __init__(self,path,log,dlog,hitcount,mode):
        # Filter settings
        self.path=path
        self.log=log
        self.dlog=dlog
        self.hitcount=hitcount
        self.mode=mode
        self.modules=f"{self.path}modules/"
        self.actions=f"{self.path}actions/"
        
        # Create directory structure
        for directory in [
            f"{self.path}",
            f"{self.modules}",
            f"{self.actions}"
            ]:
            try:
                os.makedirs(directory)
            except:
                pass
        open(f'{self.path}/packet_whitelist.json', 'w+').close()
        open(f'{self.path}/packet_excludelist.json', 'w+').close()
        
    def start(self):
        self.log("[Filter] Starting...")
        try:
            with open(f'{self.path}blacklist.txt', 'r') as f:
                self.blacklist = f.read().splitlines()
        except IOError:
            self.blacklist=[]
        try:
            with open(f'{self.path}filter_rules.json', 'r') as f:
                self.rules = json.load(f)
        except IOError:
            self.rules=[
                {"check":"blacklist","method":"blacklisted","failaction":["drop_packet","refuse_connection","fail2ban"]},
                {"check":"order","method":"packet_order","failaction":["set_offender","drop_packet"]},
                {"check":"sanity","method":"sanity","failaction":["set_offender","inform_user","drop_packet"]},
                {"check":"threshold","method":"threshhold","failaction":["drop_packet","blacklist_ip"]}
            ]
            with open(f'{self.path}filter_rules.json', 'w+') as f:
                json.dump(self.rules,f)
        try:
            with open(f'{self.path}packet_specs.json', 'r') as f:
                self.packet_specs = json.load(f)
        except IOError:
            self.log("Packet specs file missing or invalid. Sanity checks disabled.")
            self.enable_sanity=False
        try:
            self.log(f'[Filter] {self.mode} mode')
            if self.mode == "normal":
                with open(f'{self.path}packet_whitelist.json', 'r') as f:
                    try:
                        self.packetlist=json.load(f)
                    except:
                        self.packetlist=[]
                        self.log("Packet whitelist empty or invalid. Initializing empty list.")
            elif self.mode == "exclude":
                with open(f'{self.path}packet_excludelist.json', 'r') as f:
                    try:
                        self.packetlist=json.load(f)
                    except:
                        self.packetlist=[]
                        self.log("Packet excludelist empty or invalid. Initializing empty list.")
            else:
                raise Exception("Invalid option for filter-mode in config.json. Valid options: normal|exclude.")
        except IOError:
            self.packetlist=[]
            pass
        except:
            self.log(traceback.print_exc(limit=None, file=None, chain=True))
        TrekFilter.status=True
        self.log("[Filter] Enabled!")
            
            
        
    def stop(self):
        self.log("[Filter] Stopping...")
        self.save_blacklist()
        TrekFilter.status=False
        self.log("[Filter] Disabled!")
        
    def printinfo(self):
        self.log(f"TrekFilter v{TrekFilter.version}")
        if TrekFilter.status:
            active="enabled"
        else:
            active="disabled"
        self.log(f"Status: {active}")
        self.log(f"Mode: {self.mode}")
    
    def printrules(self):
        index=1
        rule_string=f"TrekFilter active ruleset\n"
        delim=","
        for r in self.rules:
            rule_string+=f'-{index} RUN CHECK {r["method"]} RESPOND WITH {delim.join(r["failaction"])}\n'
            index+=1
        if self.mode=="normal":
            rule_string+="Checking Packets: "
        else:
            rule_string+="Excluding Packets: "
        rule_string+=f'{self.packetlist}'
        self.log(f"{rule_string}")
        
    def printoffenders(self):
        self.log("Offenders:")
        for o in self.offenders:
            self.log(o)
        self.log("Blacklist:")
        for b in self.blacklist:
            self.log(b)
                                                 
    def save_blacklist(self):
        try:
            with open(f'{self.path}blacklist.txt', 'w+') as f:
                for b in self.blacklist:
                    f.write(str(b)+"\n")
        except:
            self.log(traceback.print_exc(limit=None, file=None, chain=True))
            
    def loadModule(self, fname):
        spec = importlib.util.spec_from_file_location("*", fname)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module.main
    
    def filter(self,conn,addr,data,trusted=False):
        try:
            if not TrekFilter.status:
                return
            if self.mode=="normal":
                if not data[0] in self.packetlist:
                    self.dlog(f"[Filter] Packet {data[0]} from {addr[0]} not in packet list. Skipping.")
                    return
            elif self.mode=="exclude":
                if data[0] in self.packetlist:
                    self.dlog(f"[Filter] Packet {data[0]} from {addr[0]} in exclude list. Skipping.")
                    return
            self.dlog(f"[Filter] Checking packet {data[0]} from {addr[0]}")
            for r in self.rules:
                try:
                    response = getattr(self,r["method"])(addr, data, trusted)
                except AttributeError:
                    try:
                        response = getattr(self,self.loadModule(f'{self.modules}{r["method"]}.py'))(conn, addr, data, trusted)
                        pass
                    except AttributeError:
                        raise Exception(f'Method {r["method"]} not implemented')
                if response:
                    for action in r["failaction"]:
                        try:
                            getattr(self, action)(conn, addr, data)
                        except AttributeError:
                            try:
                                getattr(self,self.loadModule(f'{self.actions}{action}.py'))(conn, addr, data)
                                pass
                            except AttributeError:
                                raise Exception(f'Method {action} not implemented')
                                continue
                    if not data:
                        break
        except:
            self.log(traceback.print_exc(limit=None, file=None, chain=True))
        return
      
    def packet_order(self, addr, data, trusted):
        if not trusted:        
            if not data[0]<9:
                self.log(f'[Filter][order] Failed for {addr[0]}')
                return True
        return False
        
    def blacklisted(self, addr, data, trusted):
        ip, port = addr
        if ip in self.blacklist:
            self.log(f'[Filter][blacklist] Failed for {ip}')
            return True
        else:
            return False
            
    def sanity(self, addr, data, trusted):
        if not self.enable_sanity:
            self.dlog("[Filter] Sanity checks are disabled, skipping!")                          
            return False
        packet_id=str(ord(data[0]))
        if not packet_id in self.packet_specs:
            self.dlog(f"[Filter] Packet {packet_id} not in speclist. Skipping!")
            return False                      
        packet_segments=bytes(data[1:]).split(b"\0")
        if not len(packet_segments)==len(self.packet_specs[packet_id]["segments"]):
            self.log("[Filter] Packet segment count invalid!")
            return True
        loop_iter=0
        for seg in self.packet_specs[packet_id]["segments"]:
            if seg==False:
                continue
            response = getattr(self,seg)(packet_segments[loop_iter])
            if response:
                return True 
            loop_iter+=1                       
        return False
                                        
    def special_chars(self, segment):
        if any([a in bytes(segment, 'UTF-8') for a in TrekFilter.special_characters]):
			return True
        else
            return False                                                         
        
    def threshhold(self, addr, data, trusted):
        ip, port = addr
        if ip in self.offenders.keys():
            if self.offenders[ip]>=self.hitcount:
                self.log(f'[Filter][threshold] Failed for {ip}')
                return True
        return False
    
    def refuse_connection(self, conn, addr, data):
        ip, port = addr
        # append properly formatted fail2ban log
        self.log(f'[Filter] Connection refused. Logging connection.')                       
        conn.close()
        return
        
    def drop_packet(self, conn, addr, data):
        self.log(f'[Filter] Dropping packet')
        data.clear()
        return
        
    def inform_user(self, conn, addr, data):
        self.log(f'[Filter] Sending "Invalid" to user')
        msg="Packet dropped by server: Invalid"
        conn.send([ControlCodes["MESSAGE"]]+list(bytes(msg+'\0', 'UTF-8')))
        return
        
    def blacklist_ip(self, conn, addr, data):
        ip, port = addr
        self.blacklist.append(ip)
        self.log(f'[Filter] {ip} blacklisted')
        self.refuse_connection(conn, addr, data)                               
        return
        
    def set_offender(self, conn, addr, data):
        ip, port = addr
        if ip in self.offenders.keys():
            self.offenders[ip]+=1
        else:
            self.offenders.update({f'{ip}':1})
        return
    
    def fail2ban(self, conn, addr, data):
        ip, port = addr
        date_now=datetime.today().strftime('%Y-%m-%dT%H:%M:%S')
        with open("{self.path}trek-f2b.log", "a+") as f:
            json = f'# failJSON: { "time": "{date_now}", "match": true , "host": "{ip}" }\n'
            text = f'{date_now} Connect from blacklisted IP at {ip}\n'
            f.write(json)
            f.write(text)
    
  
