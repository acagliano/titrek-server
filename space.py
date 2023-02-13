import os,random,requests
import configparser

from timeit import default_timer as timer



class Space:

	def __init__(self):
		self.path = "data/space"
		self.config_file = f"{self.path}/space.conf"
		os.makedirs(self.path, exist_ok=True)
		try:
			with open(self.config_file) as f:
				self.config = configparser.ConfigParser()
				self.config.read_file(f)
			self.generate()
		
		except IOError:
			get_url = "https://raw.githubusercontent.com/acagliano/titrek-server/rewrite/space.conf"
			r = requests.get(get_url, allow_redirects=True)
			
			with open(self.config_file, 'wb') as f:
				f.write(r.content)
			
			with open(self.config_file) as f:
				self.config = configparser.ConfigParser()
				self.config.read_file(f)
			self.generate()
		
		
	def generate(self):
	
		self.target_size = self.config["mapconfig"].getint("starting-size")
		self.current_size = 0	
		self.galaxies = []		
		self.galaxy_gen_preset = self.config["generationrates"]["galaxy"]
		self.system_gen_preset = self.config["generationrates"]["system"]
		galaxy_idx = 0
		
		if self.galaxy_gen_preset == "fast":
			self.galaxy_rates = (1, 3)
		else:
			self.galaxy_rates = (5, 9)
		
		if self.target_size == 0:
			self.galaxies[galaxy_idx] = galaxy = Galaxy(self.path)
			galaxy.generate(self.current_size)
		else:
			while self.current_size < self.target_size:
				galaxies_to_generate = random.choice(range(self.galaxy_rates[0], self.galaxy_rates[1]))
				for g in range(galaxies_to_generate):
					self.galaxies[galaxy_idx] = galaxy = Galaxy(self.path)
					galaxy.generate(self.current_size)
					galaxy_idx += 1
		
		self.map_time = {}		
		self.map_time["start"] = self.map_time["last"] = timer()
		self.map_time["current"] = None
		
		
	def save(self):
		return
					
			
	def tick(self):
		self.map_time["current"] = timer()
		return
				
				







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
		self.path = f"{path}/system{self.id}.dat"
		System.identifier += 1


##class CelestialObject:
##	def __init__(self):
##		return
##		
##	def generate(self, dist_from_origin):