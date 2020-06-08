
from npcs import *
from trek_vec3 import *
from trekCodes import *
from trek_constants import *
import os,json,math,random,time


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
	def generate_all(self):
		x=y=z=0
		for i in range(250):
			x+=random.randint(-6e8,6e8)*1e7
			z+=random.randint(-6e8,6e8)*1e7
			y=random.randint(-1e8,1e8)*1e5
			for planet in self.generate(Vec3(x,y,z)):
				yield planet
	def generate(self,vec3):
		if self._seed is None:
			self.seed(random.random())
		return PlanetoidSystem(self._seed,vec3)

#Earth's radius: 6371 km. mass: 5.9e24 kg.

StandardPlanetList = [
	{"type": "planet","living": True, "mass": 1e24, "radius": 1e6, "colors":[0x2E,0x18,0x7F]},
	{"type": "planet","living": False,"mass": 1e20, "radius": 5e5, "colors":[0x21,0x22,0x00]},
	{"type": "planet","living": False,"mass": 1e21, "radius": 6e5, "colors":[0x41,0x42,0x00]},
	{"type": "planet","living": False,"mass": 6e23, "radius": 3.4e6, "colors":[0x60,0x81,0x21]},
	{"type": "planet","living": False,"mass": 1e16, "radius": 1e4, "colors":[0xA0,0xA9,0x8D]}
]

StandardCompositionMaterials = [
	"rock","H2O","Deutrium","Tritium","N2O","C2H6","CH4","C3H8","C4H12","FeO","U"
]

StandardStarList = [
	{"type": "star","mass": 2e30,"radius":7e8,"colors":[0xE7,0xC3,0xEF]},
	{"type": "star","mass": 3e30,"radius":3e6,"colors":[0xFF,0xDF,0xBF]},
	{"type": "star","mass": 1e32,"radius":4e9,"colors":[0x11,0x08,0x14]}
]


def PlanetoidSystem(seed,pos):
	random.seed(seed)
	x=float(pos['x']); y=float(pos['y']); z=float(pos['z'])
	mass = random.randint(1e29,9e32)
	r=random.choice(StandardStarList)
	a={"position":Vec3(x,y,z),"velocity":Vec3(),"name":"Sol"}
	for name in r.keys(): a[name] = r[name]
	yield a
	rad = random.randint(80,300)*1e19
	grav = GRAVITATIONAL_CONSTANT*mass
	for i in range(random.randint(2,10)):
		x+=random.randint(-6e9,6e9)
		z+=random.randint(-6e9,6e9)
		y=random.randint(-1e9,1e9)
		r=random.choice(StandardPlanetList)
		a={"position":Vec3(x,y,z),"velocity":Vec3(),"name":"Planet "+chr(i+0x41)}
		for name in r.keys(): a[name] = r[name]
		yield a

