import json,os,sys,logging

class Space:
	def __init__(self, dir, log, config)
		self.config=config
		self.logger=log
		self.path=dir
		
		
	def load(self):
	# this will determine if a map has already been created and load it
	# or it will create a new map
		try:
			self.logger.log(logging.INFO, f"Loading map.")
			with open(f"{self.path}/universe.meta", "r") as f:
				universe_meta = json.load(f)
			galaxies = [ item for item in os.listdir(self.path) if os.path.isdir(os.path.join(root, item)) ]
			for galaxy in galaxies:
				self.map.append(CelestialObject(f"{self.path}/{galaxy}"))
				
		except IOError:
			self.logger.log(logging.INFO, f"Universe meta file not found. Generating new map.")
			self.generate_map()
		except:
			self.logger.log(logging.ERROR, f"Universe meta file not found. Loading new map.")
	
	
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
	def __init__(self):
		
		
class Galaxy(CelestialObject):
	
	
class System(CelestialObject):
	

class Planetoid(CelestialObject):
	
	
class Stellar(CellestialObject):
