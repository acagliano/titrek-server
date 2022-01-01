# MAP STRUCTURE
#
# data/space/..
# 	galaxy##/	foreach galaxy in map, where ## is a number from 00 to 99 (or ff if we need more)
# 		galaxy.dat	metadata for galactic center
#		sys00.dat	metadata for sys00
#		sys01.dat	metadata for sys01
#		...
#		sys99.dat	metadata for sys99
#
#	In galaxy.dat:
#	json = {"name":<name>, "radius":<size>, "coords":{"x":<x>,"y":<y>,"z":<z>},"motion":{"dx":<x>,"dy":<y>,"dz":<z>}}
#	* if the map contains multiple galaxies, each galaxy will need coordinates of its own relative to universe origin.
#
#	In sys00.dat:
#	json = {"name":<name>, "coords":{"x":<x>,"y":<y>,"z":<z>}, "motion":{"dx":<x>,"dy":<y>,"dz":<z>}, "bodies":[<arr of objects>]}
#	foreach(<arr of objects>):
#		json={"name":<name>, "type":<type>, "radius":<radius>, "mass":mass",
#			coords:"coords":{"x":<x>,"y":<y>,"z":<z>}, "motion":{"dx":<x>,"dy":<y>,"dz":<z>}
#			...}
#
#	## Relative positioning system ##
#	If top-level is universe, then
#		(1) set universe origin to (0,0,0)
#		(2) generate galaxies with origins at offsets from universe origin (use relative coordinates in json)
#			Ex: galaxy00's (0,0,0) point may occur at (-23000000, 320000, 120000000) from universe origin.
#		(3) generate systems with origins at offsets from galaxy origin (use relative coordinates in json)
#			Ex: sys00's (0,0,0) point may occur at (141000, -10000, 320000) from galaxy00's origin.
#			This also places it at the absolute coord (-22859000, 310000, 120320000) relative to universe origin.
#			Use relative coords to make the math less intensive.
#		(4) generate system objects (planets, stars, black holes, etc) at offsets from system origin
#		(5) An object's absolute position is universe_origin + galaxy_origin + system_origin + object_coords
#		(6) Universe Generation (per galaxy) (if multi-galaxy support) should continue with somewhat of a random
#			distribution of galaxies being placed at coordinates progressively further from the universe origin
#			until the target map radius is hit.
#		(7) Galaxy Generation (per galaxy) should continue with somewhat of a center-weighted distribution of systems 
#			being placed at coordinates progressively further from the galaxy origin until the galaxy target radius is hit.
#		(8) System Generation (per system) should continue with a distribution of planets, stars, asteroids, and black holes
#			being placed at coordinates progressively further from the system origin until the system target radius is hit.
#	If top-level is galaxy, then skip universe origin step and set galaxy origin to (0,0,0). Continue normally.
#	Even if not planning to support multi-galaxy in present release, still create the galaxy00 directory, for forward compat.
#	** The system generator should select what to place where from a table of weighted options (based on distance from origin??).
#	** The universe/galaxy generator should use some sort of noise generation algorithm to place galaxies/systems.

import os,json,math,random,time,traceback
from trek.math.npcs import *
from trek.math.vec3 import *
from trek.codes import *
from trek.math.constants import *

class Generator:
	def __init__(self):
		try:
			with open("space/SEED.txt") as f:
				self._seed=float(f.read())
		except:
			self._seed=None
	def seed(self,seed):
		self._seed=seed
		with open("space/SEED.txt",'w') as f:
			f.write(str(seed))
	def generate_all(self,space):
		try:
			if self._seed is None:
				self._seed = random.random()
			random.seed(self._seed)
			for ri in range(11):
				rn = ri/(math.pi*2)
				x=y=z=rev=0
				dist=random.randint(9e9, 1e11)*1e3
				for i in range(500):
					rev+=math.atan2(1.8e13,dist)
					dist+=random.random()*1e13
					x=math.cos(rev)*dist
					z=math.sin(rev)*dist
					y=random.randint(-1e9,1e9)*1e3
					gen_this = True
					for planet in space:
						if abs(math.hypot(planet["position"]["x"],planet["position"]["y"],planet["position"]["z"]))<1e13:
							gen_this = False; break
					if gen_this:
						for planet in self.generate(Vec3(x,y,z)):
							planet["name"] = "system "+chr(0x41+ri)+str(i)+"; "+planet["name"]
							space.append(planet)
							
		except:
			print(traceback.print_exc(limit=None, file=None, chain=True))

	def generate(self,vec3):
		for planet in PlanetoidSystem(self._seed,vec3):
			yield planet

#Earth's radius: 6371 km. mass: 5.9e24 kg.

def LoadJsonFile(fname=None):
	if fname is None:
		return dict()
	try:
		with open(fname) as f:
			return json.load(f)
	except Exception as e:
		print("Something went wrong loading",fname)
		raise e


def PlanetoidSystem(seed,pos):
	x=float(pos['x']); y=float(pos['y']); z=float(pos['z'])
	mass = random.randint(1e29,9e32)
	r=random.choice(StandardStarList)
	r["position"]=Vec3(x,y,z)
	r["velocity"]=Vec3()
	r["name"]="Sol"
	rv=random.random()*.2+.9
	r["mass"]*=rv
	r["radius"]/=rv
	yield r
	grav = GRAVITATIONAL_CONSTANT*mass
	for i in range(random.randint(2,10)):
		x+=random.randint(-6e6,6e6)
		z+=random.randint(-6e6,6e6)
		y=random.randint(-1e6,1e6)
		r=random.choice(StandardPlanetList)
		r["position"]=Vec3(x,y,z)
		r["velocity"]=Vec3()
		r["name"]="Planet "+chr(i+0x41)
		rv=random.random()*.2+.9
		r["mass"]*=rv
		r["radius"]/=rv
		yield r



StandardPlanetList = LoadJsonFile("data/planetoids/planets.json")["data"]
StandardStarList = LoadJsonFile("data/planetoids/stars.json")["data"]
Materials = LoadJsonFile("data/materials/materials.json")["data"]

#if __name__=='__main__':
	#do some tests
#	def getRBGBinStr(c):
#		return str((c//(2**5))&7)+"r "+str((c//(2**3))&3)+"b "+str(c&7)+"g"
#	for i in range(16):
#		color=random.randint(0,256)
#		print(getRBGBinStr(color),"->",getRBGBinStr(RandomDeviatingColor(color)),"=",hex(color))

