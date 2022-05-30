import json,os,sys,logging,traceback

INIT_MODE_LOAD = 0
INIT_MODE_GENERATE = 1

class Space:
	def __init__(self, dir, log, config)
		self.config=config
		self.logger=log
		self.path=dir
		self.map={}
		
		
	def load(self):
	# this will determine if a map has already been created and load it
	# or it will create a new map
		try:
			with open(f"{self.path}/universe.meta", "r") as f:
				universe_meta = json.load(f)
			galaxies = [ item for item in os.listdir(self.path) if os.path.isdir(os.path.join(self.path, item)) ]
			self.logger.log(logging.INFO, f"Loading map save.")
			for g in galaxies:
				self.map.append(Galaxy(f"{self.path}/{g}", INIT_MODE_LOAD))
				
		except IOError:
			self.logger.log(logging.INFO, f"Universe meta file not found. Generating new map.")
			self.generate_map()
		except:
			self.logger.log(logging.ERROR, traceback.print_exc(limit=None, file=None, chain=True))
	
	
	def generate_map(self):
	
	def tick(self):
	# this will iterate all tickable stuff, like star life cycles, pathing of objects, etc
	
	
	def save(self):
	# this will save all map objects to disk.
	# call this on server setdown and every 5 or 10 minutes
	
	
	def generate_path(self, objCenter, objSelf):
	# this will calculate a path for the given object
	# should only be used on bodies within a system (and maybe systems)
	
	
	def map_to_octree(self):
	# converts the multi-d json array to octree for optimized proximity checking
	# call this after loading the map
	
	
class CelestialObject:
	def __init__(self, filepath, mode):
		self.path = filepath
		self.identifier = os.path.basename(filepath).split('.')[0])
		self.contains = {}
		if mode==INIT_MODE_LOAD:
			self.load()
		elif mode==INIT_MODE_GENERATE:
			self.generate()
		
		
class Galaxy(CelestialObject):
	def load(self):
		systems = [ item for item in os.listdir(self.path) if os.path.isfile(os.path.join(self.path, item)) ]
		for s in systems:
			self.contains.append(System(f"{self.path}/{s}", INIT_MODE_LOAD))
			
		
	def generate(self):
		for x in <num of systems>:
			
	def save(self)
	
	
class System(CelestialObject):
	def load(self):
		
	def generate(self):
		
	def save(self):
	
	

class SystemBody(CelestialObject):
	def load(self):
		
	def generate(self):
		
	def save(self):
	

