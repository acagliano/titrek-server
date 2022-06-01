import json,os,sys,logging,traceback
from pathlib import Path
from abc import ABC, abstractmethod

INIT_MODE_LOAD = 0
INIT_MODE_GENERATE = 1

GalaxyTypes = {
	"Spiral":0,
	"Elliptical":1,
	"Irregular":2
}

StarTypes = {
	"MainSequence":0,
	"RedGiant":1,
	"WhiteDwarf":2,
	"BlackDwarf":3,
	"Neutron":4,
	"Supernova":5,
	"BlackHole":6
}

PlanetoidTypes = {
	"Terrestrial":0,
	"Jovian":1,
	"Asteroid":2
}

SaveAttributes = [
	# list of SystemBody attributes to serialize
	"id",
	"name",
	"type",
	"position",
	"radius",
	"mass",
	"composition",
	"logistics"
]

class Space:
	def __init__(self, dir, log, config)
		try:
			self.logger=log
			self.path=Path(dir)
			self.config_path=Path(config)
			with self.config_path.open() as cf:
				self.config = json.load(cf)
			self.map={}
			self.path.mkdir(exist_ok=True)
			if any(self.path.iterdir()):
				self.load_map()
			else: 
				self.generate_map()
			
		except IOError:
			self.logger.log(logging.ERROR, f"There was an error loading the map configuration file.")
		except: self.logger.log(logging.ERROR, traceback.print_exc(limit=None, file=None, chain=True))
			
	
	def load_map(self):
		try:
			self.logger.log(logging.ERROR, f"A map already exists. Loading it.")
			for galaxy in self.path.iterdir():
				if galaxy.is_dir():
					self.map.append(Galaxy(galaxy))
		except: self.logger.log(logging.ERROR, traceback.print_exc(limit=None, file=None, chain=True))
			
		
		
	
	
	
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
	
	
class MapObject(ABC):
	@abstractmethod
	def __init__(self, filepath, mode):
		self.path = Path(filepath)
		pass

		
class Galaxy(MapObject):
	def __init__(self, filepath):
		try:
			self.path = filepath
			self.identifier = self.path.name
			self.systems={}
			if self.path.exists() and any(self.path.iterdir()):
				self.load()
			else:
				self.generate()
				
		except: self.logger.log(logging.ERROR, traceback.print_exc(limit=None, file=None, chain=True))
		
		
	def load(self):
		try:
			for system in self.path.iterdir():
				if system.is_file():
					self.systems.append(System(system))
		
		except:
			self.logger.log(logging.ERROR, traceback.print_exc(limit=None, file=None, chain=True))
			
		
	def generate(self):
	#	for x in <num of systems>:
			
	def save(self)
	
	
class System(MapObject):
	def __init__(self, filepath, mode):
		try:
			self.path = filepath
			self.identifier = self.path.stem
			self.systembodies={}
			
				
		except: self.logger.log(logging.ERROR, traceback.print_exc(limit=None, file=None, chain=True))
	
	def load(self):
		try:
			with self.path.open() as f:
				systemjson = json.load(f)
				for sb in systemjson["system-bodies"]:
					self.systembodies.append(SystemBody(sb))
					
		except:
			self.logger.log(logging.ERROR, traceback.print_exc(limit=None, file=None, chain=True))
		
		
		
	def generate(self):
		
	def save(self):
		try:
			with self.path.open("r+") as f:
				js = json.load(f)
				sb_json = {}
				for s in self.systembodies:
					sb_json.append(s.save())
				js["system-bodies"] = sb_json
				json.dump(js, f)
			
	
	

class SystemBody(MapObject):
	def __init__(self, jsondata):
		
		
	def load(self, jsondata):
		for var in jsondata:
			setattr(self, var, jsondata[var])
		
		
	def generate(self):
		
		
	def save(self):
		
		
	def serialize(self):
		# create dict from class vars
		j={}
		for var in dir() if var in SaveAttributes:
			j[var] = getattr(self, var)
		return j
	

