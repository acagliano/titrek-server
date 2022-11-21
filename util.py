import os,random
import configparser

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
			config_string = """
				
				generation-rates:
					galaxy: "fast"
					system: "fast"
				_comments:
					map-size: "specifies initial size, amount to increase, interval to increase, and size to stop"
					scale-distances: "Specifies ratio of emulated distance to real distance. 1 means exact scaling"
					realistic-physics: "Determines whether to path celestial objects, tick star life cycles, compute gravity on dynamic entities, and spawn and path rogue objects like comets"
					generation-rates: "Sets preconfigured spawn rates of galaxies per Mpc of map space and systems per galaxy. Supported options are 'fast' and 'normal'. Normal attempts to emulate spawning patterns consistent with real life"
					
			"""
			self.config = yaml.safe_load(yaml_string)
			with open(self.config_file, 'w') as f:
				yaml.dump(self.config, f)
			self.generate()
		
		
	def generate(self):
		# generate galaxies
		self.realsize = 0
		self.galaxies = []
		galaxies_per = self.config["galaxies-per-Mpc"]
		if self.config["map-size"] == 0:
			self.galaxies[0] = galaxy = Galaxy(self.path)
			galaxy.generate()
		else:
			while self.realsize < self.config["map-size"]:
				galaxies_to_generate = random.choice(range(galaxies_per["min"], galaxies_per["max"]))
				for g in galaxies_to_generate:
					self.galaxies[galaxy_idx] = galaxy = Galaxy(self.path)
					galaxy.generate(self.realsize)
				


class Galaxy(CelestialObject):
	identifier = 0
	def __init__(self, path):
		self.id = Galaxy.identifier
		self.path = f"{path}/galaxy{self.id}"
		Galaxy.identifier += 1


class System(CelestialObject):
	identifier = 0
	def __init__(self, path):
		self.id = System.identifier
		self.path = f"{path}/system{id}.dat"
		System.identifier += 1


class CelestialObject:
	def __init__(self):
		return
		
	def generate(self, dist_from_origin):
		
		
