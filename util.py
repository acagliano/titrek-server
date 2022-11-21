import os,random

# Space class for map data
######################################
class Space:
######################################
	def __init__(self):
		self.path = "data/space"
		self.config_file = f"{self.path}/space.conf"
		os.makedirs(self.path, exist_ok=True)
		try:
			with open(self.config_file, "r") as f:
				self.config = yaml.safe_load(f)
			self.generate()
			
		except IOError:
			yaml_string = """
				map-size:
					start: 0
					end: ?
					step: 5
				scale-distances: 1
				realistic-physics: false
				rogue-objects: false
				galaxies-per-unit:
					min: 1
					max: 3
				systems-per-galaxy: 10
					min: 10
					max: 50
			"""
			self.config = yaml.safe_load(yaml_string)
			with open(self.config_file, 'w') as f:
				yaml.dump(self.config, f)
			return
		
		
	def generate(self):
		# generate galaxies
		self.realsize = 0
		self.galaxies = []
		if self.config["map-size"] == 0:
			self.galaxies[0] = galaxy = Galaxy(self.path)
			galaxy.generate()
		else:
			while self.realsize < self.config["map-size"]:
				galaxies_to_generate = random.choice(range(self.config["min-galaxies-per-unit"], self.config["max-galaxies-per-unit"]))
				for g in galaxies_to_generate:
					self.galaxies[galaxy_idx] = galaxy = Galaxy(self.path)
					galaxy.generate()
				
				
	def generate_galaxy(self, single_galaxy=False):
		# spawn galaxy center at random point on circle
		# defined by a radius of self.realsize,
		# centered on (0,0,0)
		# all galaxy origin coordinates are relative to map origin
		if single_galaxy==True:
			return CelestialObject("galaxy", 0, 0, 0)
			


CelestialObjectTypes = {
	"galaxy": 0,
	"system": 1
}

class Galaxy(CelestialObject):
	identifier = 0
	def __init__(self, path):
		self.id = Galaxy.identifier
		self.path = f"{path}/galaxy{self.id}"
		Galaxy.identifier += 1
	def generate(self, dist_from_origin, min_systems, max_systems, single_galaxy=False):
		# do stuff


class CelestialObject:
	identifier = 0
	def __init__(self, path):
		self.id = CelestialObject.identifier
		self.path = f"{path}/galaxy{self.id}"
		CelestialObject.identifier += 1
		
		
		
