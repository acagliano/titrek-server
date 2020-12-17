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

LOG_NORMAL=0
LOG_ERROR=1
LOG_DEBUG=2
LOG_DISCORD=3

class TrekFilter:
    version="1.0b"
    enable=False
    status=False
    offenders={}
    enable_sanity=True
    special_characters = [bytes(a,'UTF-8') for a in ["/","\\","#","$","%","^","&","*","!","~","`","\"","|"]] + \
					[bytes([a]) for a in range(1,0x20)] + [bytes([a]) for a in range(0x7F,0xFF)]
    
    def __init__(self,config,log):
	# "enable":true, "path":"filter/", "security-level":"default"
	
        # Configure filter
        if not config["enable"]:
            return
	self.log(LOG_NORMAL, "Starting TrekFilter")
        TrekFilter.enable=True
        self.path=config["path"]
        self.loggers=log
        self.security_level=config["security-level"]
        if self.security_level=="default":
            self.security_level="medium"
        self.skip_trusted = False if self.security_level=="high" else True
        self.mode = "normal" if self.security_level=="low" else "exclude"
        self.log(LOG_NORMAL, f'Security Level: {self.security_level}')
        self.modules=f"{self.path}modules/"
        self.actions=f"{self.path}actions/"
	
	# Create directories
        for directory in [
            f"{self.path}",
            f"{self.modules}",
            f"{self.actions}"
            ]:
            try:
                os.makedirs(directory)
            except:
                pass
	
	# Load packetlist for proper mode
        packet_list_file = f'{self.path}/packet_whitelist.json' if self.mode=="normal" else f'{self.path}/packet_excludelist.json'
        try:
            with open(packet_list_file, 'r') as f:
                self.packetlist = json.load(f)
        except:
            self.packetlist=[]
            self.log(LOG_NORMAL, "No packetlist file found. Initializing empty list.")
		
	# Load blacklist
        try:
            with open(f'{self.path}blacklist.txt', 'r') as f:
                self.blacklist = f.read().splitlines()
        except IOError:
            self.blacklist=[]
	
	# Load Filter rules
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
	# Make sure rules file is created after init
            with open(f'{self.path}filter_rules.json', 'w+') as f:
                json.dump(self.rules,f)
	
	# Load packet specs
        try:
            with open(f'{self.path}packet_specs.json', 'r') as f:
                self.packet_specs = json.load(f)
        except IOError:
            self.log(LOG_NORMAL, "Packet specs file missing or invalid. Sanity checks disabled.")
            self.enable_sanity=False
	
        TrekFilter.status=True
        self.log(LOG_NORMAL, "Enabled!")
        
    def log(self, loglvl, msg):
        self.loggers[loglvl](f"[Filter] {msg}")
        if loglvl==LOG_ERROR:
            self.loggers[LOG_DISCORD]("",msg,1)

    def printinfo(self):
        infostring=f"\n___TrekFilter Service Firewall v{TrekFilter.version}___"
        active="enabled" if TrekFilter.status else "disabled"
        infostring+=f"\nStatus {active}\nMode: {self.mode}"
        index=1
        infostring+=f"\n\n_Active Ruleset_"
        delim=","
        for r in self.rules:
            infostring+=f'\n-{index} RUN CHECK {r["method"]} RESPOND WITH {delim.join(r["failaction"])}'
            index+=1
        infostring+="\n\n_Active Packet Specs_"
        for s in self.packet_specs.keys():
            infostring+=f"\nPacket: {s}, Specs: {str(self.packet_specs[s]['segments'])}"
        if self.mode=="normal":
            infostring+="\nChecking Packets: "
        else:
            infostring+="\nExcluding Packets: "
        infostring+=f'{self.packetlist}'
        infostring+="\n\n_Offenders_"
        for o in self.offenders.keys():
            infostring+=f"\nIP: {o}, Hits: {self.offenders[o]}"
        infostring+="\n\n_Blacklist_"
        for b in self.blacklist:
            infostring+=f"\nIP: {b}"
        self.log(f"{infostring}")


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
            if trusted and self.skip_trusted:
                return
            if self.mode=="normal":
                if not data[0] in self.packetlist:
                    self.log(LOG_DEBUG, f"Packet {data[0]} from {addr[0]} not in packet list. Skipping.")
                    return
            elif self.mode=="exclude":
                if data[0] in self.packetlist:
                    self.log(LOG_DEBUG, f"Packet {data[0]} from {addr[0]} in exclude list. Skipping.")
                    return
            self.log(LOG_DEBUG, f"Checking packet {data[0]} from {addr[0]}")
            for r in self.rules:
                try:
                    response = getattr(self,r["method"])(addr, data, trusted)
                except AttributeError:
                    try:
                        response = getattr(self,self.loadModule(f'{self.modules}{r["method"]}.py'))(conn, addr, data, trusted)
                        pass
                    except AttributeError:
                        raise Exception(f'Method {r["method"]} not implemented')
                resp_string = "Fail" if response else "Pass"
                self.log(LOG_DEBUG, f"Check: {r['check']}, Status: {resp_string}")
                if response:
                    delim=","
                    msg=f"IP {addr[0]} failed TrekFilter.{r['check']} for packet {data[0]}\nPerforming Actions: {delim.join(r['failaction'])}"
                    self.log(LOG_DISCORD, msg)
                    self.log(LOG_DEBUG, f"Check: {r['check']}")
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
            self.log(LOG_ERROR, traceback.print_exc(limit=None, file=None, chain=True))
        return
      
    def packet_order(self, addr, data, trusted):
        if not trusted:        
            if not data[0]<9:
                self.log(LOG_NORMAL, f'[order] Failed for {addr[0]}')
                return True
        return False
        
    def blacklisted(self, addr, data, trusted):
        ip, port = addr
        if ip in self.blacklist:
            self.log(LOG_NORMAL, f'[blacklist] Failed for {ip}')
            return True
        else:
            return False
            
    def sanity(self, addr, data, trusted):
        if not self.enable_sanity:
        	self.log(LOG_DEBUG, "Sanity checks are disabled, skipping!")                          
       		return False
        packet_id=str(data[0])
        if not packet_id in self.packet_specs:
       		self.log(LOG_DEBUG, f"Packet {packet_id} not in speclist. Skipping!")
       		return False                      
        packet_segments=bytes(data[1:len(data)-1]).split(b"\0")
        if not len(packet_segments)==len(self.packet_specs[packet_id]["segments"]):
            self.log(LOG_NORMAL, "[sanity] Packet segment count invalid!")
            self.log(LOG_NORMAL, f"[sanity] Failed for {addr[0]}")
            return True
        loop_iter=0
        for seg in self.packet_specs[packet_id]["segments"]:
            if seg==False:
                continue
            response = getattr(self,seg)(packet_segments[loop_iter])
            if response:
                self.log(LOG_NORMAL, "[sanity] Segment analysis failed!")
                self.log(LOG_NORMAL, f"[sanity] Failed for {addr[0]}")
                return True
            loop_iter+=1
       	return False
                                        
    def special_chars(self, segment):
        if any([a in segment for a in TrekFilter.special_characters]):
            return True
        else:
           	return False                                                         
        
    def threshhold(self, addr, data, trusted):
        ip, port = addr
        if ip in self.offenders.keys():
            if self.offenders[ip]>=self.hitcount:
                self.log(LOG_NORMAL, f'[threshold] Failed for {ip}')
                return True
        return False
    
    def refuse_connection(self, conn, addr, data):
        ip, port = addr
        # append properly formatted fail2ban log
        self.log(LOG_NORMAL, 'Connection refused. Logging connection.')                       
        conn.close()
        return
        
    def drop_packet(self, conn, addr, data):
        self.log(LOG_NORMAL, 'Dropping packet')
        data.clear()
        return
        
    def inform_user(self, conn, addr, data):
        self.log(LOG_NORMAL, 'Sending "Invalid" to user')
        msg = b"Packet dropped by server: Invalid\0"
        conn.send(bytes([ControlCodes["MESSAGE"]]+list(msg)))
        return
        
    def blacklist_ip(self, conn, addr, data):
        ip, port = addr
        self.blacklist.append(ip)
        self.log(LOG_NORMAL, f'{ip} blacklisted')
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
    
  
