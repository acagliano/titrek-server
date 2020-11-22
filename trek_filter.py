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
            ]:
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
        if not TrekFilter.status:
            return
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
        return
       
        
        
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
        return
        
    def drop_packet(self, conn, addr):
        ip, port = addr
        self.log(f'[FILTER] Dropping packet')
        data=[]
        return
        
    
      
    
    
  
