
import os,json,traceback

class TrekFilter:
  
    def __init__(self,path,log,hitcount):
        self.path=path
        self.log=log
        self.hitcount=hitcount
        os.makedirs(f"{self.path}")
        self.offenders=[]
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
                {"check":"blacklist","method":self.isBlacklisted,"failaction":self.log_and_disconnect},
                {"check":"sanity","method":self.isSane,"failaction":self.drop_packet},
                {"check":"overthreshold","method":self.overThresh,"failaction":self.blacklist}
            ]
        checks=[self.isBlacklisted,self.isSane,self.overThresh]
        actions=[self.log_and_disconnect,self.drop_packet,self.blacklist]
    
    def savestate(self):
        try:
            with open(f'{self.path}filter_rules.json', 'w+') as f:
                json.dump(self.blacklist,f)
            with open(f'{self.path}blacklist.txt', 'w+') as f:
                for b in self.blacklist:
					f.write(str(b)+"\n")
        except:
            self.log(traceback.print_exc(limit=None, file=None, chain=True))
    
    def filter(self,conn,addr,data):
        try:
            for r in rules:
                if not r["method"] in self.checks:
                    raise Exception(f'Method {r["method"]} not implemented')
                return = r["method"](addr, data)
                if not return:
                    if not r["failaction"] in self.actions:
                        raise Exception(f'Method {r["failaction"]} not implemented')
                    data = r["failaction"](conn, addr, data)
                    if not data:
                        break
            return data
        except:
            self.log(traceback.print_exc(limit=None, file=None, chain=True))
        
        
    def isBlacklisted(self, addr, data):
        ip, port = addr
        if ip in self.blacklist:
            self.log(f'[FILTER] {ip} is blacklisted')
            return False
        else
            return True
            
    def isSane(self, addr, data):
        return
    
    def log_and_disconnect(self, conn, addr):
        ip, port = addr
        self.log(f'[FILTER] Connection logged to fail2ban')
        # append properly formatted fail2ban log
        self.log(f'[FILTER] Connection closed')
        conn.close()
        data=[]
        
    def drop_packet(self, conn, addr):
        ip, port = addr
        self.log(f'[FILTER] Dropping packet')
        data=[]
        
    
      
    
    
  
