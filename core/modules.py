
class Module:
	count = 0
	
	def log(self, lvl, msg):
		Module.log_handle.log(lvl, msg)
	
	def __init__(self, type):
		self.type = type
		self.tech = None
		if not hasattr(Module, 'moduleinfo'):
			self.load_moduleinfo()
		count+=1
		
	def load_moduleinfo(self):
		try:
			with open("data/tech/modules.yml") as f:
				mdata = yaml.safe_load(f)
		except: IOError:
			self.log(logging.ERROR, "unable to load module techdata.")
			return
		
		Module.moduleinfo = mdata["modules"]
		Module.config = mdata["base-config"]
		return
		
	def assign_tech(self):
