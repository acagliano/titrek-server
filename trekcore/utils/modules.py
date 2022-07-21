import traceback,logging,os,yaml,json

class TrekModules:
	def __init__(self,path):
		self.path=path
		self.internal_gfx_path = f"{os.path.dirname(path)}/assets/modules"
		with open(path, 'r') as f:
			self.module_data=yaml.safe_load(f)
			#print(json.dumps(self.module_data, indent=2))
			self.defaults = self.module_data["defaults"]
	
	def load_module(self, name):
		try:
			return self.module_data[name]
		except:
			print(traceback.format_exc(limit=None, chain=True))
    
  
