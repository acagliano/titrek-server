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
    
    def __init__(self,path,log,hitcount):
        # Filter settings
        self.path=path
        self.log=log
        self.hitcount=hitcount
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
                {"check":"blacklist","method":"blacklisted","failaction":["refuse_connection"]},
                {"check":"order","method":"packet_order","failaction":["set_offender","drop_packet_no_response"]},
                {"check":"sanity","method":"sanity","failaction":["set_offender","drop_packet_response"]},
                {"check":"threshold","method":"threshhold","failaction":["blacklist_ip"]}
            ]
            with open(f'{self.path}filter_rules.json', 'w+') as f:
                json.dump(self.rules,f)
        TrekFilter.status=True
        self.log("[Filter] Enabled!")
        
    def stop(self):
        self.log("[Filter] Stopping...")
        self.save_blacklist()
        TrekFilter.status=False
        self.log("[Filter] Disabled!")
        
    def printinfo(self):
        self.log(f"TrekFilter v{TrekFilter.version}")
        self.log("Offenders:")
        for o in offenders:
            self.log(o)
        self.log("Blacklist:")
        for b in blacklist:
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
            if trusted:
                return
            for r in self.rules:
                try:
                    response = getattr(self,r["method"])(addr, data)
                except AttributeError:
                    try:
                        response = getattr(self,self.loadModule(f'{self.modules}{r["method"]}.py'))(conn, addr, data)
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
      
    def packet_order(self, addr, data):
        if not data[0]<9:
            self.log(f'[Filter][order] Failed for {addr[0]}')
            return True
        return False
        
    def blacklisted(self, addr, data):
        ip, port = addr
        if ip in self.blacklist:
            self.log(f'[Filter][blacklist] Failed for {ip}')
            return True
        else:
            return False
            
    def sanity(self, addr, data):
        return False
        
    def threshhold(self, addr, data):
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
        data=[]
        return
        
    def drop_packet_no_response(self, conn, addr, data):
        ip, port = addr
        self.log(f'[Filter] Silently dropping packet')
        data=[]
        return
        
    def drop_packet_response(self, conn, addr, data):
        ip, port = addr
        self.log(f'[Filter] Dropping packet')
        msg="Packet dropped by server: Invalid"
        conn.send([ControlCodes["MESSAGE"]]+list(bytes(msg+'\0', 'UTF-8')))
        data=[]
        return
        
    def blacklist_ip(self, conn, addr, data):
        ip, port = addr
        self.blacklist.append(ip)
        self.log(f'[Filter] {ip} blacklisted')
        conn.close()
        data=[]
        return
        
    def set_offender(self, conn, addr, data):
        ip, port = addr
        if ip in self.offenders.keys():
            self.offenders[ip]+=1
        else:
            self.offenders.update({f'{ip}':1})
        return
    
    
  
