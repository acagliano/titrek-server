import traceback,logging,os,yaml

class TrekModules:
	def __init__(self,path):
		self.path=path
		self.internal_gfx_path = f"{os.path.dirname(path)}/assets/modules"
		with open(path, 'r') as f:
			self.modules=yaml.safe_load(f)
			self.defaults = self.modules["defaults"]
	
	def load_module(self, name):
		try:
			return self.modules[name]
		except:
			print(traceback.format_exc(limit=None, chain=True))
    
  
