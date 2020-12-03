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
                {"check":"blacklist","method":"blacklisted","failaction":["drop_packet","refuse_connection"]},
                {"check":"order","method":"packet_order","failaction":["set_offender","drop_packet"]},
                {"check":"sanity","method":"sanity","failaction":["set_offender","inform_user","drop_packet"]},
                {"check":"threshold","method":"threshhold","failaction":["drop_packet","blacklist_ip"]}
            ]
            with open(f'{self.path}filter_rules.json', 'w+') as f:
                json.dump(self.rules,f)
        try:
            self.log(f'[Filter] {self.mode} mode')
            if self.mode == "normal":
                with open(f'{self.path}packet_whitelist.json', 'r') as f:
                    self.packetlist=json.load(f)
            elif self.mode == "exclude":
                with open(f'{self.path}packet_excludelist.json', 'r') as f:
                    self.packetlist=json.load(f)
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
        self.log(f"TrekFilter v{TrekFilter.version}")
        self.log("active ruleset")
        index=1
        rule_string="\n"
        for r in self.rules:
            rule_string+=f'-{index} RUN CHECK {r["method"]} RESPOND WITH {r["failaction"]}\n'
            index+=1
        if self.mode=="normal"
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
    
    
  
