import traceback,logging,os,json

class TrekModules:
	def __init__(self,path):
		self.path=path
	
	def load_module(self, name, level):
		try:
			level-=1
			module_path=f"{self.path}{name}.json"
			with open(module_path) as f:
				modules_data=json.load(f)
			return modules_data["module"][level]
		except:
			print(traceback.format_exc(limit=None, chain=True))
    
  
