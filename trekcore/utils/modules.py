import traceback,logging,os,json

class TrekModules:
	def __init__(self,path):
		self.path=path
		with open(path, 'r') as f:
			self.modules=yaml.safe_load(f)
			self.defaults = self.data["defaults"]
	
	def load_module(self, name):
		try:
			return self.modules["name"]
		except:
			print(traceback.format_exc(limit=None, chain=True))
    
  
