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
				map-size: 'single-galaxy'
				map-scale: 1
				realistic-physics: false
				rogue-objects: false
			"""
			self.config = yaml.safe_load(yaml_string)
			with open(self.config_file, 'w') as f:
				yaml.dump(self.config, f)
			return
		
		
	def generate(self):
		# generate galaxies
		self.galaxies = []
		if self.config["map-size"] == "single-galaxy":
			self.galaxies[0] = self.generate_galaxy()
		else:
			generate_next = True
			galaxy_idx = 0
			while generate_next:
				self.galaxies[galaxy_idx] = self.generate_galaxy()
				if galaxy_origin_distance_map_origin > map-size:
					generate_next = False
