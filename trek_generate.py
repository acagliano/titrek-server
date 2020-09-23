
from trek_npcs import *
from trek_vec3 import *
from trek_codes import *
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
	def generate_all(self,space):
		x=y=z=0
		for i in range(2000):
			x+=random.randint(-6e6,6e6)*1e3
			z+=random.randint(-6e6,6e6)*1e3
			y=random.randint(-1e6,1e6)*1e2
			for planet in self.generate(Vec3(x,y,z)):
				planet["name"] = "system "+str(i)+"; "+planet["name"]
				space.append(planet)
	def generate(self,vec3):
		if self._seed is None:
			self.seed(random.random())
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

