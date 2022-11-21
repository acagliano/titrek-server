import os,random,requests
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
			self.config = configparser.ConfigParser()
			self.config.read(self.config_file)
			self.generate()
			
		except IOError:
			get_url = "https://raw.githubusercontent.com/acagliano/titrek-server/rewrite/space.conf"
			r = requests.get(url, allow_redirects=True)
			
			with open(self.config_file, 'wb') as f:
				f.write(r.content)
			
			self.config = configparser.ConfigParser()
			self.config.read(self.config_file)
			self.generate()
		
		
	def generate(self):
		# generate galaxies
		self.realsize = 0
		self.galaxies = []
		galaxies_per = self.config["galaxies-per-Mpc"]
		if self.config["map-size"] == 0:
			self.galaxies[0] = galaxy = Galaxy(self.path)
			galaxy.generate(0)
		else:
			while self.realsize < self.config["map-size"]:
				galaxies_to_generate = random.choice(range(galaxies_per["min"], galaxies_per["max"]))
				for g in galaxies_to_generate:
					self.galaxies[galaxy_idx] = galaxy = Galaxy(self.path)
					galaxy.generate(self.realsize)
					
			
	def tick(self):
		return
				
				
###########################################
# Class Definitions for Celestial Objects #
###########################################
# - Galaxy()
# - System()
# - Planetoid()
# - Stellar()
# - ext class CelestialObject()			  
###########################################

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
		
		
