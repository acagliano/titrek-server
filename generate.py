
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
	def generate(self,vec3):
		if self._seed is None:
			self.seed(random.random())
		return PlanetoidSystem(self._seed,vec3)


def PlanetoidSystem(seed,pos):
	random.seed(seed)
	x=float(pos['x']); y=float(pos['y']); z=float(pos['z'])
	mass = random.randint(1e29,9e32)
	planets = [{"position":Vec3(x,y,z),"velocity":Vec3(),
			"mass":mass,"name":"Sol"}]
	rad = random.randint(80,300)*1e19
	grav = GRAVITATIONAL_CONSTANT*mass
	for i in range(random.randint(2,10)):
		x+=random.randint(-6e9,61e8)
		z+=random.randint(-6e9,61e8)
		y=random.randint(-1e9,1e9)
		mass=random.randint(1e24,1e26)
		planets.append({"position":Vec3(x,y,z),"velocity":Vec3(),
			"mass":mass,"name":"Planet "+chr(i+0x41)})
	return planets

