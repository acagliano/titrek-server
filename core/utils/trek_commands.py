import logging,os,json,traceback

from core.trek_server import *

class TrekCommands:
  def __init__(self, server, log):
    self.logger=log
    self.server=server
    try:
      with open("commands.json") as f:
        j=json.load(f)
      self.commands=j["commands"]
    except IOError:
      self.logger.log(logging.ERROR, "Failed to load commands file")
    except:
      self.logger.log(logging.ERROR, traceback.format_exc(limit=None, chain=True)) 
      
  def run(self,commands, client=None):
    command=commands[0]
    if not command in self.commands.keys():
      self.logger.log(logging.INFO, "Invalid command. Type 'help' to view the command list")
      return
    spec=self.commands[command]
    args=len(commands)-1
    if not args=spec["args"]:
      self.logger.log(logging.INFO, f"Invalid command usage. {spec['helper']}")
    try:                  
      if args>0:
        getattr(self,spec["run"])(commands[1:])
      else:
        getattr(self,spec["run"])()
    except: self.logger.log(logging.ERROR, f"{command} registered, but unimplemented.")                    
      
    
    
  
      
