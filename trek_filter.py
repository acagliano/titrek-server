
import os,json,traceback

class TrekFilter:
  path="filter/"
  
  def __init__(self,log):
    os.makedirs(f"{path}")
    self.log=log  
    offenders=[]
    checks=[self.isBlacklisted,self.isSane,self.overThresh]
    actions=[self.DISCONNECT,self.IGNORE,self.BLACKLIST]
    rules=[
    {"check":"blacklist","method":self.isBlacklisted,"failaction":self.DISCONNECT},
    {"check":"sanity","method":self.isSane,"failaction":self.IGNORE},
    {"check":"overthreshold","method":self.overThresh,"failaction":self.BLACKLIST}
    ]
    
  def packetfilter(self,conn,addr,data):
    try:
     for r in rules:
       if not r["method"] in self.checks:
        raise Exception(f"Method {r["method"]} not implemented")
       return = r["method"](self, conn, addr, data)
       if not return:
        if not r["failaction"] in self.actions:
          raise Exception(f"Method {r["failaction"]} not implemented")
        r["failaction"](self, conn, addr)
      except:
        self.log(traceback.print_exc(limit=None, file=None, chain=True))
      
    
    
  
