import logging, os
import importlib
# may want to set up logging in here

class RunServer:
  def __init__(self):
    for file in os.walk("includes")[2]:
      m = os.path.splitext(file)[0]
      importlib.import_module(f"includes.{m}")
    self.instance=Server()
    
  def run(self):
    self.instance.run()
    
  def reload(self):
    for file in os.walk("includes")[2]:
      m = os.path.splitext(file)[0]
      importlib.reload(f"includes.{m}")
    self.old=self.instance
    self.instance=Server()
    self.instance.clients=self.old.clients
    del self.old
    self.run()
       
    
if __name__ == '__main__':
	
	server = RunServer()
	server.run()
