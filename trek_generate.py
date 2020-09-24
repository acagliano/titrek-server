
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
					if abs(math.hypot(x-planet["x"],y-planet["y"],z-planet["z"]))<1e13:
						gen_this = False; break
				if gen_this:
					for planet in self.generate(Vec3(x,y,z)):
						planet["name"] = "system "+chr(0x41+ri)+str(i)+"; "+planet["name"]
						space.append(planet)
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

