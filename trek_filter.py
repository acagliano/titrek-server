# This file is the beginning of a packet filter module for the service
# to provide more solid protection than a regex and a banlist
# it has a series of rules that will be written to a file on the server,
# much like your standard packet filter
# "check" name of the test to be done
# "method" the self.method to call to perform the check
# "failaction" the action to take should the packet fail the check
# Might add the ability to pass a format specifier to the filter, such that our sanity checks...
# ... can know what type of data to expect in different packet segments

# Not yet implemented, but this module will be designed as a class
# that can be invoked optionally, should a user wish to provide it on their own server

import os,json,traceback

class TrekFilter:
    status=False
    
    def __init__(self,path,log,hitcount):
        # Filter settings
        self.path=path
        self.log=log
        self.hitcount=hitcount
        
        # Create directory structure
        for directory in [
            f"{self.path}",
            f"{self.path}checks/",
            f"{self.path}actions/"
            ]
            try:
                os.makedirs(f"{directory}")
            except:
                pass

    def start(self):
        self.log("[FILTER] Starting...")
        try:
            with open(f'{self.path}blacklist.txt', 'r') as f:
                self.blacklist = f.read().splitlines()
        except IOError:
            self.blacklist=[]
        try:
            with open(f'{self.path}filter_rules.json', 'r') as f:
                self.rules = json.load(f)
        except:
            self.rules=[
                {"check":"blacklist","method":self.blacklisted,"failaction":self.refuse_connection},
                {"check":"sanity","method":self.sanity,"failaction":self.drop_packet},
                {"check":"threshold","method":self.threshold,"failaction":self.blacklist}
            ]
            with open(f'{self.path}filter_rules.json', 'w+') as f:
                json.dump(self.rules,f)
        TrekFilter.status=True
        self.log("[FILTER] Packet filter enabled!")
        
    def stop(self):
        self.log("[FILTER] Stopping...")
        self.save_blacklist()
        TrekFilter.status=False
        self.log("[FILTER] Packet filter disabled!")
    
    def save_blacklist(self):
        try:
            with open(f'{self.path}blacklist.txt', 'w+') as f:
                for b in self.blacklist:
                    f.write(str(b)+"\n")
        except:
            self.log(traceback.print_exc(limit=None, file=None, chain=True))
    
    def filter(self,conn,addr,data):
        for r in rules:
            try:
                if not method_exists('TrekFilter', f'{r["method"]}'):
                    raise Exception(f'Method {r["method"]} not implemented')
                if not method_exists('TrekFilter', f'{r["failaction"]}'):
                    raise Exception(f'Method {r["failaction"]} not implemented')
                response = r["method"](addr, data)
                if not response:
                    data = r["failaction"](conn, addr, data)
                    if not data:
                        break
            except:
                self.log(traceback.print_exc(limit=None, file=None, chain=True))
                continue
        return data
       
        
        
    def blacklisted(self, addr, data):
        ip, port = addr
        if ip in self.blacklist:
            self.log(f'[FILTER] {ip} is blacklisted')
            return False
        else
            return True
            
    def sanity(self, addr, data):
        return
    
    def refuse_connection(self, conn, addr):
        ip, port = addr
        self.log(f'[FILTER] Connection logged to fail2ban')
        # append properly formatted fail2ban log
        self.log(f'[FILTER] Connection refused')
        conn.close()
        data=[]
        return data
        
    def drop_packet(self, conn, addr):
        ip, port = addr
        self.log(f'[FILTER] Dropping packet')
        data=[]
        return data
        
    
      
    
    
  
